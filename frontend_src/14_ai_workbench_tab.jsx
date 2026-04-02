function AIWorkbenchTab({ documents, manuals, nonConformances }) {
  const sources = [...documents, ...manuals]
    .map(item => ({
      id: item.id,
      name: item.name,
      department: item.department || "",
      version: item.version || "",
      path: item.docxPath || item.pdfPath || "",
    }))
    .filter(item => item.path)
    .sort((a, b) => a.id.localeCompare(b.id));
  const sourceMetadata = sources.reduce((acc, item) => {
    acc[item.path] = {
      title: item.name,
      document_code: item.id,
      owner_dept: item.department,
      version: item.version,
      source_system: "iso_local_library",
    };
    return acc;
  }, {});

  const [apiBase, setApiBase] = useState(() => loadStoredState("audit_v2_api_base", "http://127.0.0.1:8890/api/v2"));
  const [serviceInfo, setServiceInfo] = useState({ service: "auto-audit-v2", database_mode: "unknown", openrouter_enabled: false });
  const [serviceMessage, setServiceMessage] = useState("");
  const [cacheBusy, setCacheBusy] = useState(false);
  const [cacheStatus, setCacheStatus] = useState({ compare_cache_count: 0, audit_cache_count: 0 });
  const [ingestBusy, setIngestBusy] = useState(false);
  const [ingestMessage, setIngestMessage] = useState("");
  const [ingestResult, setIngestResult] = useState(null);
  const [selectedPath, setSelectedPath] = useState(sources[0]?.path || "");
  const [compareMode, setCompareMode] = useState("generic");
  const [compareUseLlm, setCompareUseLlm] = useState(false);
  const [compareLeftPath, setCompareLeftPath] = useState(sources[0]?.path || "");
  const [compareRightPath, setCompareRightPath] = useState(sources[1]?.path || sources[0]?.path || "");
  const [compareBusy, setCompareBusy] = useState(false);
  const [compareExportBusy, setCompareExportBusy] = useState(false);
  const [compareDocxExportBusy, setCompareDocxExportBusy] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [compareMessage, setCompareMessage] = useState("");
  const [versionCandidatesBusy, setVersionCandidatesBusy] = useState(false);
  const [versionCandidates, setVersionCandidates] = useState([]);
  const [auditBusy, setAuditBusy] = useState(false);
  const [auditExportBusy, setAuditExportBusy] = useState(false);
  const [auditResult, setAuditResult] = useState(null);
  const [auditMessage, setAuditMessage] = useState("");
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyMode, setHistoryMode] = useState("all");
  const [historyQuery, setHistoryQuery] = useState("");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyMessage, setHistoryMessage] = useState("");
  const [searchQuery, setSearchQuery] = useState("核准 版次 保存");
  const [searchBusy, setSearchBusy] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [qaQuestion, setQaQuestion] = useState("文件化資訊管制程序對保存與核准有什麼要求？");
  const [qaScope, setQaScope] = useState("selected");
  const [qaBusy, setQaBusy] = useState(false);
  const [qaResult, setQaResult] = useState(null);
  const [qaMessage, setQaMessage] = useState("");
  const [spcBusy, setSpcBusy] = useState(false);
  const [spcResult, setSpcResult] = useState(null);
  const [spcMessage, setSpcMessage] = useState("");
  const [spcForm, setSpcForm] = useState({
    parameter_name: "Thickness",
    csv_text: "10.1,10.0,9.9,10.2,10.1",
    lsl: "9.5",
    usl: "10.5",
    target: "10.0",
  });
  const [deviationBusy, setDeviationBusy] = useState(false);
  const [deviationResult, setDeviationResult] = useState(null);
  const [deviationMessage, setDeviationMessage] = useState("");
  const [deviationForm, setDeviationForm] = useState(() => ({
    issue_description: nonConformances[0]?.description || "",
    process_step: "AOI 檢驗",
    lot_no: "LOT-20260301-A",
    severity: "medium",
  }));

  // ── 文件 Markdown 抽取（ODL PoC Phase 4）──────────────────────
  const [mdExtractPath, setMdExtractPath] = useState(sources[0]?.path || "");
  const [mdExtractBusy, setMdExtractBusy] = useState(false);
  const [mdExtractResult, setMdExtractResult] = useState(null);
  const [mdExtractMsg, setMdExtractMsg] = useState("");

  async function runMarkdownExtract() {
    if (!mdExtractPath) return;
    setMdExtractBusy(true);
    setMdExtractResult(null);
    setMdExtractMsg("");
    try {
      const token = localStorage.getItem("qms_token") || "";
      const res = await fetch(`/api/document/extract-markdown?path=${encodeURIComponent(mdExtractPath)}`, {
        headers: { Authorization: "Bearer " + token },
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "抽取失敗");
      setMdExtractResult(data);
      setMdExtractMsg(`✓ ${data.method}｜${data.char_count.toLocaleString()} 字元${data.truncated ? "（已截斷）" : ""}`);
    } catch (e) {
      setMdExtractMsg("抽取失敗：" + e.message);
    } finally {
      setMdExtractBusy(false);
    }
  }

  useEffect(() => {
    saveStoredState("audit_v2_api_base", apiBase);
  }, [apiBase]);

  useEffect(() => {
    setVersionCandidates([]);
    if (compareMode === "version") {
      setCompareRightPath("");
    }
  }, [compareLeftPath, compareMode]);

  useEffect(() => {
    let cancelled = false;
    async function loadHealth() {
      try {
        const payload = await callV2("/health");
        if (!cancelled) {
          setServiceInfo(payload.data || {});
          setServiceMessage("");
        }
        const cachePayload = await callV2("/cache/status");
        if (!cancelled) {
          setCacheStatus(cachePayload.data || {});
        }
        const historyPayload = await callV2("/history/runs?mode=all&limit=12");
        if (!cancelled) {
          setHistoryItems(historyPayload.data?.items || []);
          setHistoryMessage("");
        }
      } catch (err) {
        if (!cancelled) setServiceMessage("V2 服務尚未就緒: " + err.message);
      }
    }
    loadHealth();
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  async function callV2(path, options = {}) {
    const response = await fetch(apiBase + path, options);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || payload.error || ("HTTP " + response.status));
    if (!payload.success) throw new Error(payload.message || payload.error_code || "V2 request failed");
    return payload;
  }

  async function runDocumentAudit() {
    if (!selectedPath) {
      setAuditMessage("請先選擇文件。");
      return;
    }
    setAuditBusy(true);
    setAuditMessage("");
    try {
      const payload = await callV2("/documents/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: selectedPath }),
      });
      setAuditResult(payload.data);
      setAuditMessage("文件稽核完成。");
      loadHistory(historyMode, historyQuery);
    } catch (err) {
      setAuditMessage("文件稽核失敗: " + err.message);
    } finally {
      setAuditBusy(false);
    }
  }

  async function exportDocumentAuditWordReport() {
    if (!selectedPath) {
      setAuditMessage("請先選擇文件。");
      return;
    }
    setAuditExportBusy(true);
    setAuditMessage("");
    try {
      const response = await fetch(apiBase + "/documents/audit/export/docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: selectedPath }),
      });
      if (!response.ok) {
        let payload = null;
        try {
          payload = await response.json();
        } catch (err) {
          payload = null;
        }
        throw new Error(payload?.message || ("HTTP " + response.status));
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "document_audit_report.docx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setAuditMessage("AI 文件稽核 Word 報告已下載。");
      loadHistory(historyMode, historyQuery);
    } catch (err) {
      setAuditMessage("AI 文件稽核 Word 報告下載失敗: " + err.message);
    } finally {
      setAuditExportBusy(false);
    }
  }

  async function runDocumentCompare() {
    if (!compareLeftPath || !compareRightPath) {
      setCompareMessage("請先選擇左右兩份文件。");
      return;
    }
    setCompareBusy(true);
    setCompareMessage("");
    try {
      const payload = await callV2("/documents/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ left_path: compareLeftPath, right_path: compareRightPath, use_llm: compareUseLlm }),
      });
      setCompareResult(payload.data);
      setCompareMessage("文件差異比對完成。");
      loadHistory(historyMode, historyQuery);
    } catch (err) {
      setCompareMessage("文件差異比對失敗: " + err.message);
    } finally {
      setCompareBusy(false);
    }
  }

  async function loadVersionCandidates() {
    if (!compareLeftPath) {
      setCompareMessage("請先選擇基準文件。");
      return;
    }
    setVersionCandidatesBusy(true);
    setCompareMessage("");
    try {
      const payload = await callV2("/documents/version-candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: compareLeftPath, limit: 12 }),
      });
      const candidates = payload.data?.candidates || [];
      setVersionCandidates(candidates);
      if (candidates[0]?.path) {
        setCompareRightPath(candidates[0].path);
      }
      setCompareMessage(candidates.length ? "已載入同文件版次候選。" : "找不到明顯的同文件版次候選。");
    } catch (err) {
      setCompareMessage("版次候選搜尋失敗: " + err.message);
    } finally {
      setVersionCandidatesBusy(false);
    }
  }

  async function exportDocumentCompareReport() {
    if (!compareLeftPath || !compareRightPath) {
      setCompareMessage("請先選擇左右兩份文件。");
      return;
    }
    setCompareExportBusy(true);
    setCompareMessage("");
    try {
      const response = await fetch(apiBase + "/documents/compare/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ left_path: compareLeftPath, right_path: compareRightPath, use_llm: compareUseLlm }),
      });
      if (!response.ok) {
        let payload = null;
        try {
          payload = await response.json();
        } catch (err) {
          payload = null;
        }
        throw new Error(payload?.message || ("HTTP " + response.status));
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "document_compare_report.xlsx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setCompareMessage("缺漏比對報告已下載。");
      loadHistory(historyMode, historyQuery);
    } catch (err) {
      setCompareMessage("缺漏比對報告下載失敗: " + err.message);
    } finally {
      setCompareExportBusy(false);
    }
  }

  async function exportDocumentCompareWordReport() {
    if (!compareLeftPath || !compareRightPath) {
      setCompareMessage("請先選擇左右兩份文件。");
      return;
    }
    setCompareDocxExportBusy(true);
    setCompareMessage("");
    try {
      const response = await fetch(apiBase + "/documents/compare/export/docx", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ left_path: compareLeftPath, right_path: compareRightPath, use_llm: compareUseLlm }),
      });
      if (!response.ok) {
        let payload = null;
        try {
          payload = await response.json();
        } catch (err) {
          payload = null;
        }
        throw new Error(payload?.message || ("HTTP " + response.status));
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "document_compare_report.docx";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      setCompareMessage("Word 比對報告已下載。");
      loadHistory(historyMode, historyQuery);
    } catch (err) {
      setCompareMessage("Word 比對報告下載失敗: " + err.message);
    } finally {
      setCompareDocxExportBusy(false);
    }
  }

  async function ingestPaths(paths) {
    if (!paths.length) {
      setIngestMessage("目前沒有可匯入的文件。");
      return;
    }
    setIngestBusy(true);
    setIngestMessage("");
    try {
      const payload = await callV2("/documents/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          paths,
          metadata: paths.reduce((acc, path) => {
            acc[path] = sourceMetadata[path] || {};
            return acc;
          }, {}),
        }),
      });
      setIngestResult(payload.data);
      setIngestMessage(`已完成 ${payload.data.ingested_count} 份文件匯入，失敗 ${payload.data.failed_count || 0} 份。`);
      const healthPayload = await callV2("/health");
      setServiceInfo(healthPayload.data || {});
      const cachePayload = await callV2("/cache/status");
      setCacheStatus(cachePayload.data || {});
    } catch (err) {
      setIngestMessage("批次匯入失敗: " + err.message);
    } finally {
      setIngestBusy(false);
    }
  }

  async function clearRuntimeCache(target) {
    setCacheBusy(true);
    setServiceMessage("");
    try {
      const payload = await callV2("/cache/clear?target=" + encodeURIComponent(target), { method: "POST" });
      const cachePayload = await callV2("/cache/status");
      setCacheStatus(cachePayload.data || {});
      setCompareResult(prev => prev ? { ...prev, cache_hit: false } : prev);
      setAuditResult(prev => prev ? { ...prev, cache_hit: false } : prev);
      setServiceMessage(`已清除 ${payload.data.deleted_compare_cache || 0} 筆文件比對快取、${payload.data.deleted_audit_cache || 0} 筆文件稽核快取。`);
    } catch (err) {
      setServiceMessage("快取清理失敗: " + err.message);
    } finally {
      setCacheBusy(false);
    }
  }

  async function loadHistory(mode = historyMode, query = historyQuery) {
    setHistoryBusy(true);
    setHistoryMessage("");
    try {
      const payload = await callV2("/history/runs?mode=" + encodeURIComponent(mode) + "&q=" + encodeURIComponent(query.trim()) + "&limit=20");
      setHistoryItems(payload.data?.items || []);
      setHistoryMessage((payload.data?.items || []).length ? "已載入結果歷史。" : "目前查無符合條件的歷史紀錄。");
    } catch (err) {
      setHistoryMessage("結果歷史讀取失敗: " + err.message);
    } finally {
      setHistoryBusy(false);
    }
  }

  async function runSearch() {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setSearchBusy(true);
    setServiceMessage("");
    try {
      const payload = await callV2("/documents/search?q=" + encodeURIComponent(searchQuery.trim()) + "&limit=8");
      setSearchResults(payload.data?.hits || []);
    } catch (err) {
      setServiceMessage("文件搜尋失敗: " + err.message);
    } finally {
      setSearchBusy(false);
    }
  }

  async function runKnowledgeQA() {
    if (!qaQuestion.trim()) {
      setQaMessage("請先輸入問題。");
      return;
    }
    setQaBusy(true);
    setQaMessage("");
    try {
      const qaPayload = { question: qaQuestion.trim(), limit: 5 };
      if (qaScope === "selected" && selectedPath) {
        qaPayload.path = selectedPath;
      }
      const payload = await callV2("/knowledge/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(qaPayload),
      });
      setQaResult(payload.data);
      setQaMessage("文件知識問答完成。");
    } catch (err) {
      setQaMessage("文件知識問答失敗: " + err.message);
    } finally {
      setQaBusy(false);
    }
  }

  async function runSpcAnalyze() {
    setSpcBusy(true);
    setSpcMessage("");
    try {
      const payload = await callV2("/spc/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parameter_name: spcForm.parameter_name,
          csv_text: spcForm.csv_text,
          lsl: spcForm.lsl === "" ? null : Number(spcForm.lsl),
          usl: spcForm.usl === "" ? null : Number(spcForm.usl),
          target: spcForm.target === "" ? null : Number(spcForm.target),
        }),
      });
      setSpcResult(payload.data);
      setSpcMessage("SPC 摘要完成。");
    } catch (err) {
      setSpcMessage("SPC 摘要失敗: " + err.message);
    } finally {
      setSpcBusy(false);
    }
  }

  async function runDeviationDraft() {
    setDeviationBusy(true);
    setDeviationMessage("");
    try {
      const payload = await callV2("/deviations/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(deviationForm),
      });
      setDeviationResult(payload.data);
      setDeviationMessage("異常草稿完成。");
    } catch (err) {
      setDeviationMessage("異常草稿失敗: " + err.message);
    } finally {
      setDeviationBusy(false);
    }
  }

  return (
    <div>
      <PageIntro
        eyebrow="AI Assisted QMS"
        title="AI 工作台（V2）"
        description="這一頁負責 AI 相關任務：文件稽核、文件比對、知識問答、SPC 摘要與異常草稿。建議先確認服務狀態，再進入個別任務區。"
      >
        <div style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
          <StatCard label="文件來源" value={sources.length} color="#38bdf8" sub="可直接送入文件稽核" />
          <StatCard label="資料庫模式" value={serviceInfo.database_mode || "unknown"} color={serviceInfo.database_mode === "postgresql" ? "#22c55e" : "#f59e0b"} sub={(serviceInfo.database_status && serviceInfo.database_status.using_fallback) ? "已退回 SQLite" : "正式資料庫已接線"} />
          <StatCard label="LLM 狀態" value={serviceInfo.openrouter_enabled ? "已啟用" : "未啟用"} color={serviceInfo.openrouter_enabled ? "#22c55e" : "#64748b"} sub="規則引擎仍可獨立運作" />
        </div>
      </PageIntro>

      <Panel
        title="文件 Markdown 抽取預覽（ODL）"
        description="使用 opendataloader-pdf 將文件轉為乾淨的 Markdown，適合作為 RAG / 文件稽核的輸入來源。PDF 優先走 ODL 解析，其他格式轉純文字。"
        accent="#a78bfa"
        style={{ marginBottom: 18 }}
      >
        <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
          <select value={mdExtractPath} onChange={e => setMdExtractPath(e.target.value)}
            style={{ ...inputStyle, flex:1, minWidth:200 }}>
            {sources.map(item => (
              <option key={item.id} value={item.path}>{item.id}｜{item.name}</option>
            ))}
          </select>
          <button onClick={runMarkdownExtract} disabled={mdExtractBusy || !mdExtractPath}
            style={{ background:"linear-gradient(135deg,#7c3aed,#a78bfa)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700, opacity: (mdExtractBusy || !mdExtractPath) ? 0.6 : 1, whiteSpace:"nowrap" }}>
            {mdExtractBusy ? "抽取中..." : "抽取 Markdown"}
          </button>
          {mdExtractResult && (
            <button onClick={() => {
              const blob = new Blob([mdExtractResult.markdown], { type: "text/markdown" });
              downloadBlob(blob, mdExtractResult.filename.replace(/\.[^.]+$/, "") + ".md");
            }} style={{ background:"rgba(167,139,250,0.12)", border:"1px solid rgba(167,139,250,0.3)", borderRadius:10, color:"#c4b5fd", cursor:"pointer", padding:"9px 14px", fontSize:12, fontWeight:700, whiteSpace:"nowrap" }}>
              ↓ 下載 .md
            </button>
          )}
        </div>
        {mdExtractMsg && (
          <div style={{ marginTop:8, fontSize:12, color: mdExtractMsg.startsWith("✓") ? "#86efac" : "#fca5a5" }}>
            {mdExtractMsg}
          </div>
        )}
        {mdExtractResult && (
          <div style={{ marginTop:12, background:"rgba(0,0,0,0.25)", borderRadius:10, border:"1px solid rgba(167,139,250,0.2)", padding:"12px 16px", maxHeight:320, overflow:"auto" }}>
            <pre style={{ margin:0, fontSize:12, lineHeight:1.65, color:"#e2e8f0", whiteSpace:"pre-wrap", wordBreak:"break-word", fontFamily:"'Cascadia Code','Fira Code',monospace" }}>
              {mdExtractResult.markdown.slice(0, 6000)}{mdExtractResult.markdown.length > 6000 ? "\n\n…（預覽截斷，完整內容請下載 .md 檔）" : ""}
            </pre>
          </div>
        )}
      </Panel>

      <Panel
        title="服務狀態與資料準備"
        description="先確認 V2 服務、資料庫與快取狀態。需要時可重新匯入文件，或清除快取後再重跑。"
        accent="#38bdf8"
        style={{ marginBottom: 18 }}
      >
        <div style={{ display:"grid", gridTemplateColumns:"1.2fr 0.8fr", gap:12, alignItems:"end" }}>
          <div>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>V2 API Base URL</div>
            <input value={apiBase} onChange={e => setApiBase(e.target.value.trim())} style={inputStyle} />
          </div>
          <button onClick={runSearch} disabled={searchBusy} style={buttonStyle("primary", searchBusy)}>{searchBusy ? "搜尋中..." : "測試文件搜尋"}</button>
        </div>
        <div style={{ marginTop:10, fontSize:12, color: serviceMessage ? "#fca5a5" : "#7dd3fc" }}>
          {serviceMessage || "V2 服務健康檢查已接線，預設使用 http://127.0.0.1:8890/api/v2。"}
        </div>
        {serviceInfo.database_status && (
          <div style={{ marginTop:8, fontSize:12, color:"#cbd5e1", lineHeight:1.7 }}>
            目前資料庫：{serviceInfo.database_status.active_database_url || "unknown"}
            {serviceInfo.database_status.using_fallback && serviceInfo.database_status.fallback_reason ? "；PostgreSQL 啟用失敗，原因：" + serviceInfo.database_status.fallback_reason : ""}
          </div>
        )}
        <div style={{ marginTop:10, display:"flex", gap:8, flexWrap:"wrap" }}>
          <Badge color="#14b8a6">比對快取 {cacheStatus.compare_cache_count || 0}</Badge>
          <Badge color="#38bdf8">稽核快取 {cacheStatus.audit_cache_count || 0}</Badge>
          {cacheStatus.latest_compare_cache_at && <Badge color="#64748b">比對快取更新 {cacheStatus.latest_compare_cache_at.slice(0, 19).replace("T", " ")}</Badge>}
          {cacheStatus.latest_audit_cache_at && <Badge color="#64748b">稽核快取更新 {cacheStatus.latest_audit_cache_at.slice(0, 19).replace("T", " ")}</Badge>}
        </div>
        <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginTop:12 }}>
          <button onClick={() => ingestPaths(sources.map(item => item.path))} disabled={ingestBusy || sources.length === 0} style={buttonStyle("success", ingestBusy || sources.length === 0)}>{ingestBusy ? "匯入中..." : "匯入全部 ISO 文件"}</button>
          <button onClick={() => ingestPaths(selectedPath ? [selectedPath] : [])} disabled={ingestBusy || !selectedPath} style={buttonStyle("secondary", ingestBusy || !selectedPath)}>只匯入目前選中文件</button>
          <button onClick={() => clearRuntimeCache("all")} disabled={cacheBusy} style={buttonStyle("danger", cacheBusy)}>{cacheBusy ? "清理中..." : "清除全部快取"}</button>
          <button onClick={() => clearRuntimeCache("compare")} disabled={cacheBusy} style={buttonStyle("warning", cacheBusy)}>只清比對快取</button>
          <button onClick={() => clearRuntimeCache("audit")} disabled={cacheBusy} style={buttonStyle("secondary", cacheBusy)}>只清稽核快取</button>
          {ingestMessage && <div style={{ fontSize:12, color:"#99f6e4", alignSelf:"center" }}>{ingestMessage}</div>}
        </div>
        {ingestResult && (
          <div style={{ marginTop:12, fontSize:12, color:"#cbd5e1", lineHeight:1.7 }}>
            已建立/更新 {ingestResult.ingested_count} 份文件，失敗 {ingestResult.failed_count || 0} 份，最近一次匯入首筆為 {ingestResult.documents?.[0]?.title || "n/a"}。
          </div>
        )}
      </Panel>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(320px, 1fr))", gap:16 }}>
        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>AI 文件稽核</div>
          <div style={{ fontSize:12, color:"#94a3b8", marginBottom:10 }}>選擇既有 SOP / 程序 / 三階文件，直接送入 V2 規則稽核。</div>
          <select value={selectedPath} onChange={e => setSelectedPath(e.target.value)} style={inputStyle}>
            {sources.map(item => (
              <option key={item.id} value={item.path}>{item.id}｜{item.name}</option>
            ))}
          </select>
          <div style={{ display:"flex", gap:10, marginTop:12, flexWrap:"wrap" }}>
            <button onClick={runDocumentAudit} disabled={auditBusy || !selectedPath} style={{ background:"linear-gradient(135deg,#2563eb,#38bdf8)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(auditBusy || !selectedPath) ? 0.6 : 1 }}>{auditBusy ? "稽核中..." : "執行文件稽核"}</button>
            <button onClick={exportDocumentAuditWordReport} disabled={auditExportBusy || !selectedPath} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.14)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(auditExportBusy || !selectedPath) ? 0.6 : 1 }}>{auditExportBusy ? "匯出中..." : "下載稽核 Word 報告"}</button>
          </div>
          {auditMessage && <div style={{ marginTop:10, fontSize:12, color:"#bae6fd" }}>{auditMessage}</div>}
          {auditResult && (
            <div style={{ marginTop:14, display:"flex", flexDirection:"column", gap:10 }}>
              <div style={{ fontSize:13, color:"#e2e8f0", lineHeight:1.7 }}>{auditResult.summary}</div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                <Badge color="#60a5fa">prompt {auditResult.prompt_version}</Badge>
                <Badge color={auditResult.needs_human_review ? "#f59e0b" : "#22c55e"}>{auditResult.needs_human_review ? "需人工覆核" : "可直接採用"}</Badge>
                {typeof auditResult.cache_hit === "boolean" && <Badge color={auditResult.cache_hit ? "#14b8a6" : "#64748b"}>{auditResult.cache_hit ? "命中快取" : "即時計算"}</Badge>}
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>問題清單</div>
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {(auditResult.issues || []).map(item => (
                    <div key={item.code} style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.18)", borderRadius:10, padding:"10px 12px" }}>
                      <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:4 }}>
                        <Badge color={item.severity === "high" ? "#ef4444" : "#f59e0b"}>{item.severity}</Badge>
                        <span style={{ fontSize:13, color:"#fecaca", fontWeight:700 }}>{item.title}</span>
                      </div>
                      <div style={{ fontSize:12, color:"#fca5a5" }}>{item.description}</div>
                    </div>
                  ))}
                  {(!auditResult.issues || auditResult.issues.length === 0) && <div style={{ fontSize:12, color:"#4ade80" }}>目前規則檢查未發現必要章節缺漏。</div>}
                </div>
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>引用片段</div>
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {(auditResult.citations || []).map((item, idx) => (
                    <div key={idx} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                      <div style={{ fontSize:12, color:"#7dd3fc", marginBottom:4 }}>{item.title}</div>
                      <div style={{ fontSize:11, color:"#94a3b8", marginBottom:4 }}>{item.source_path}</div>
                      <div style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>{item.preview}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>文件差異比對</div>
          <div style={{ fontSize:12, color:"#94a3b8", marginBottom:10 }}>比較兩份程序或表單的版本差異、缺漏規則與文字增減。</div>
          <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:10, padding:"10px 12px", background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10 }}>
            <input id="compare-llm-toggle" type="checkbox" checked={compareUseLlm} onChange={e => setCompareUseLlm(e.target.checked)} />
            <label htmlFor="compare-llm-toggle" style={{ fontSize:12, color:"#cbd5e1", cursor:"pointer" }}>啟用 LLM 摘要</label>
            <span style={{ fontSize:11, color:"#94a3b8" }}>預設關閉。關閉時只跑規則與文字差異，比較快。</span>
          </div>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:10 }}>
            <button onClick={() => setCompareMode("generic")} style={{ background:compareMode === "generic" ? "rgba(29,78,216,0.22)" : "rgba(255,255,255,0.04)", border:"1px solid " + (compareMode === "generic" ? "rgba(29,78,216,0.45)" : "rgba(255,255,255,0.1)"), borderRadius:999, color:compareMode === "generic" ? "#bfdbfe" : "#94a3b8", cursor:"pointer", padding:"6px 12px", fontSize:12, fontWeight:700 }}>一般比對</button>
            <button onClick={() => setCompareMode("version")} style={{ background:compareMode === "version" ? "rgba(124,58,237,0.22)" : "rgba(255,255,255,0.04)", border:"1px solid " + (compareMode === "version" ? "rgba(124,58,237,0.45)" : "rgba(255,255,255,0.1)"), borderRadius:999, color:compareMode === "version" ? "#ddd6fe" : "#94a3b8", cursor:"pointer", padding:"6px 12px", fontSize:12, fontWeight:700 }}>同文件不同版次</button>
          </div>
          {compareMode === "generic" ? (
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>左側文件</div>
                <select value={compareLeftPath} onChange={e => setCompareLeftPath(e.target.value)} style={inputStyle}>
                  {sources.map(item => (
                    <option key={"left-" + item.id} value={item.path}>{item.id}｜{item.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>右側文件</div>
                <select value={compareRightPath} onChange={e => setCompareRightPath(e.target.value)} style={inputStyle}>
                  {sources.map(item => (
                    <option key={"right-" + item.id} value={item.path}>{item.id}｜{item.name}</option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div style={{ display:"grid", gap:10 }}>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>基準文件</div>
                <select value={compareLeftPath} onChange={e => setCompareLeftPath(e.target.value)} style={inputStyle}>
                  {sources.map(item => (
                    <option key={"base-" + item.id} value={item.path}>{item.id}｜{item.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
                <button onClick={loadVersionCandidates} disabled={versionCandidatesBusy || !compareLeftPath} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.14)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(versionCandidatesBusy || !compareLeftPath) ? 0.6 : 1 }}>{versionCandidatesBusy ? "搜尋中..." : "尋找同文件版次"}</button>
                {versionCandidates.length > 0 && <div style={{ fontSize:12, color:"#cbd5e1", alignSelf:"center" }}>已找到 {versionCandidates.length} 個候選版本</div>}
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>候選版次</div>
                <select value={compareRightPath} onChange={e => setCompareRightPath(e.target.value)} style={inputStyle}>
                  <option value="">請選擇候選版本</option>
                  {versionCandidates.map(item => (
                    <option key={"candidate-" + item.path} value={item.path}>{item.title}{item.version_label ? "｜版次 " + item.version_label : ""}{item.extension ? "｜" + item.extension : ""}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
          <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginTop:12 }}>
            <button onClick={runDocumentCompare} disabled={compareBusy || !compareLeftPath || !compareRightPath} style={{ background:"linear-gradient(135deg,#1d4ed8,#7c3aed)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(compareBusy || !compareLeftPath || !compareRightPath) ? 0.6 : 1 }}>{compareBusy ? "比對中..." : "執行文件比對"}</button>
            <button onClick={exportDocumentCompareReport} disabled={compareExportBusy || !compareLeftPath || !compareRightPath} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.14)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(compareExportBusy || !compareLeftPath || !compareRightPath) ? 0.6 : 1 }}>{compareExportBusy ? "匯出中..." : "下載缺漏比對報告"}</button>
            <button onClick={exportDocumentCompareWordReport} disabled={compareDocxExportBusy || !compareLeftPath || !compareRightPath} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.14)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(compareDocxExportBusy || !compareLeftPath || !compareRightPath) ? 0.6 : 1 }}>{compareDocxExportBusy ? "匯出中..." : "下載 Word 比對報告"}</button>
          </div>
          {compareMessage && <div style={{ marginTop:10, fontSize:12, color:"#c4b5fd" }}>{compareMessage}</div>}
          {compareResult && (
            <div style={{ marginTop:14, display:"grid", gap:10 }}>
              {compareResult.version_change_conclusion && (
                <div style={{ background:"rgba(59,130,246,0.08)", border:"1px solid rgba(59,130,246,0.18)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#93c5fd", fontWeight:700, marginBottom:6 }}>版次結論</div>
                  <div style={{ fontSize:12, color:"#dbeafe", lineHeight:1.7 }}>{compareResult.version_change_conclusion}</div>
                  {compareResult.version_change_recommendation && <div style={{ marginTop:6, fontSize:12, color:"#bfdbfe" }}>{compareResult.version_change_recommendation}</div>}
                </div>
              )}
              <div style={{ fontSize:12, color:"#e9d5ff", lineHeight:1.8, whiteSpace:"pre-wrap" }}>{compareResult.summary}</div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                <Badge color="#7c3aed">相似度 {compareResult.similarity}</Badge>
                <Badge color="#60a5fa">prompt {compareResult.prompt_version}</Badge>
                {typeof compareResult.same_document_family === "boolean" && <Badge color={compareResult.same_document_family ? "#22c55e" : "#f59e0b"}>{compareResult.same_document_family ? "同文件版次" : "疑似不同文件"}</Badge>}
                {typeof compareResult.cache_hit === "boolean" && <Badge color={compareResult.cache_hit ? "#14b8a6" : "#64748b"}>{compareResult.cache_hit ? "命中快取" : "即時計算"}</Badge>}
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
                <div style={{ background:"rgba(245,158,11,0.08)", border:"1px solid rgba(245,158,11,0.18)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#fcd34d", fontWeight:700, marginBottom:6 }}>右側新增內容</div>
                  {(compareResult.added_lines || []).slice(0, 6).map((item, idx) => (
                    <div key={idx} style={{ fontSize:12, color:"#fde68a", lineHeight:1.6 }}>+ {item}</div>
                  ))}
                  {(!compareResult.added_lines || compareResult.added_lines.length === 0) && <div style={{ fontSize:12, color:"#94a3b8" }}>未偵測到明顯新增內容。</div>}
                </div>
                <div style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.18)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#fca5a5", fontWeight:700, marginBottom:6 }}>左側移除內容</div>
                  {(compareResult.removed_lines || []).slice(0, 6).map((item, idx) => (
                    <div key={idx} style={{ fontSize:12, color:"#fecaca", lineHeight:1.6 }}>- {item}</div>
                  ))}
                  {(!compareResult.removed_lines || compareResult.removed_lines.length === 0) && <div style={{ fontSize:12, color:"#94a3b8" }}>未偵測到明顯移除內容。</div>}
                </div>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
                <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#e2e8f0", fontWeight:700, marginBottom:6 }}>僅左側存在的規則缺口</div>
                  {(compareResult.left_only_issues || []).map(item => (
                    <div key={item.code} style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>- {item.title}</div>
                  ))}
                  {(!compareResult.left_only_issues || compareResult.left_only_issues.length === 0) && <div style={{ fontSize:12, color:"#94a3b8" }}>無。</div>}
                </div>
                <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#e2e8f0", fontWeight:700, marginBottom:6 }}>僅右側存在的規則缺口</div>
                  {(compareResult.right_only_issues || []).map(item => (
                    <div key={item.code} style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>- {item.title}</div>
                  ))}
                  {(!compareResult.right_only_issues || compareResult.right_only_issues.length === 0) && <div style={{ fontSize:12, color:"#94a3b8" }}>無。</div>}
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>結果歷史與查詢</div>
          <div style={{ fontSize:12, color:"#94a3b8", marginBottom:10 }}>查詢近期文件稽核、文件比對與報告匯出執行結果，方便覆核與追蹤。</div>
          <div style={{ display:"grid", gridTemplateColumns:"0.7fr 1.3fr auto", gap:10, alignItems:"end" }}>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>類型</div>
              <select value={historyMode} onChange={e => setHistoryMode(e.target.value)} style={inputStyle}>
                <option value="all">全部</option>
                <option value="audit">文件稽核</option>
                <option value="compare">文件比對</option>
                <option value="export">報告匯出</option>
              </select>
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>關鍵字</div>
              <input value={historyQuery} onChange={e => setHistoryQuery(e.target.value)} placeholder="可搜尋 task type、prompt version、request 摘要" style={inputStyle} />
            </div>
            <button onClick={() => loadHistory()} disabled={historyBusy} style={{ background:"linear-gradient(135deg,#475569,#0f172a)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: historyBusy ? 0.6 : 1 }}>{historyBusy ? "載入中..." : "查詢歷史"}</button>
          </div>
          {historyMessage && <div style={{ marginTop:10, fontSize:12, color:"#cbd5e1" }}>{historyMessage}</div>}
          <div style={{ marginTop:12, display:"flex", flexDirection:"column", gap:8 }}>
            {historyItems.map(item => (
              <div key={item.id} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                <div style={{ display:"flex", justifyContent:"space-between", gap:12, flexWrap:"wrap", marginBottom:6 }}>
                  <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                    <Badge color="#38bdf8">{item.task_type}</Badge>
                    <Badge color={item.result_status === "success" ? "#22c55e" : "#ef4444"}>{item.result_status}</Badge>
                    {item.prompt_version && <Badge color="#a78bfa">{item.prompt_version}</Badge>}
                  </div>
                  <div style={{ fontSize:11, color:"#94a3b8" }}>{item.created_at ? item.created_at.slice(0, 19).replace("T", " ") : ""}</div>
                </div>
                <div style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6, whiteSpace:"pre-wrap" }}>{item.request_summary || "無 request 摘要"}</div>
              </div>
            ))}
            {historyItems.length === 0 && <div style={{ fontSize:12, color:"#64748b" }}>目前尚無可顯示的歷史紀錄。</div>}
          </div>
        </div>

        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>SPC 摘要</div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
            <div style={{ gridColumn:"1 / -1" }}>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>參數名稱</div>
              <input value={spcForm.parameter_name} onChange={e => setSpcForm(prev => ({ ...prev, parameter_name: e.target.value }))} style={inputStyle} />
            </div>
            <div style={{ gridColumn:"1 / -1" }}>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>數值清單</div>
              <textarea value={spcForm.csv_text} onChange={e => setSpcForm(prev => ({ ...prev, csv_text: e.target.value }))} style={{ ...inputStyle, minHeight:84, resize:"vertical" }} />
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>LSL</div>
              <input value={spcForm.lsl} onChange={e => setSpcForm(prev => ({ ...prev, lsl: e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>USL</div>
              <input value={spcForm.usl} onChange={e => setSpcForm(prev => ({ ...prev, usl: e.target.value }))} style={inputStyle} />
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>Target</div>
              <input value={spcForm.target} onChange={e => setSpcForm(prev => ({ ...prev, target: e.target.value }))} style={inputStyle} />
            </div>
          </div>
          <button onClick={runSpcAnalyze} disabled={spcBusy} style={{ marginTop:12, background:"linear-gradient(135deg,#0f766e,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: spcBusy ? 0.6 : 1 }}>{spcBusy ? "分析中..." : "產生 SPC 摘要"}</button>
          {spcMessage && <div style={{ marginTop:10, fontSize:12, color:"#99f6e4" }}>{spcMessage}</div>}
          {spcResult && (
            <div style={{ marginTop:14, display:"flex", flexDirection:"column", gap:10 }}>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(3, minmax(0, 1fr))", gap:8 }}>
                {[
                  ["平均值", spcResult.metrics.mean],
                  ["標準差", spcResult.metrics.stdev],
                  ["Cpk", spcResult.metrics.cpk ?? "n/a"],
                  ["Cp", spcResult.metrics.cp ?? "n/a"],
                  ["超規筆數", spcResult.metrics.out_of_spec_count],
                  ["趨勢", spcResult.metrics.trend],
                ].map(([label, value]) => (
                  <div key={label} style={{ background:"rgba(20,184,166,0.08)", border:"1px solid rgba(20,184,166,0.16)", borderRadius:10, padding:"10px 12px" }}>
                    <div style={{ fontSize:11, color:"#99f6e4" }}>{label}</div>
                    <div style={{ fontSize:14, color:"#e2e8f0", fontWeight:700, marginTop:4 }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.7 }}>{spcResult.engineering_summary}</div>
              <div style={{ fontSize:12, color:"#fef3c7", lineHeight:1.7 }}>{spcResult.management_summary}</div>
            </div>
          )}
        </div>

        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>文件知識問答</div>
          <div style={{ fontSize:12, color:"#94a3b8", marginBottom:10 }}>只根據已匯入的文件片段回答，並保留引用來源。</div>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:10 }}>
            <button onClick={() => setQaScope("selected")} style={{ background:qaScope === "selected" ? "rgba(124,58,237,0.22)" : "rgba(255,255,255,0.04)", border:"1px solid " + (qaScope === "selected" ? "rgba(124,58,237,0.45)" : "rgba(255,255,255,0.1)"), borderRadius:999, color:qaScope === "selected" ? "#ddd6fe" : "#94a3b8", cursor:"pointer", padding:"6px 12px", fontSize:12, fontWeight:700 }}>限定目前文件</button>
            <button onClick={() => setQaScope("all")} style={{ background:qaScope === "all" ? "rgba(124,58,237,0.22)" : "rgba(255,255,255,0.04)", border:"1px solid " + (qaScope === "all" ? "rgba(124,58,237,0.45)" : "rgba(255,255,255,0.1)"), borderRadius:999, color:qaScope === "all" ? "#ddd6fe" : "#94a3b8", cursor:"pointer", padding:"6px 12px", fontSize:12, fontWeight:700 }}>搜尋全部文件</button>
          </div>
          {qaScope === "selected" && (
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:10 }}>
              目前限定文件：<span style={{ color:"#e9d5ff" }}>{sources.find(item => item.path === selectedPath)?.name || "未選擇"}</span>
            </div>
          )}
          <textarea value={qaQuestion} onChange={e => setQaQuestion(e.target.value)} style={{ ...inputStyle, minHeight:92, resize:"vertical" }} />
          <button onClick={runKnowledgeQA} disabled={qaBusy} style={{ marginTop:12, background:"linear-gradient(135deg,#7c3aed,#a855f7)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: qaBusy ? 0.6 : 1 }}>{qaBusy ? "回答中..." : "執行文件問答"}</button>
          {qaMessage && <div style={{ marginTop:10, fontSize:12, color:"#ddd6fe" }}>{qaMessage}</div>}
          {qaResult && (
            <div style={{ marginTop:14, display:"grid", gap:10 }}>
              <div style={{ fontSize:11, color:"#94a3b8" }}>回答範圍：{qaResult.scope || "全部已匯入文件"}</div>
              <div style={{ fontSize:12, color:"#e9d5ff", lineHeight:1.8, whiteSpace:"pre-wrap" }}>{qaResult.answer}</div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                <Badge color="#a855f7">prompt {qaResult.prompt_version}</Badge>
                <Badge color={qaResult.needs_human_review ? "#f59e0b" : "#22c55e"}>{qaResult.needs_human_review ? "需人工覆核" : "可直接採用"}</Badge>
              </div>
              {(qaResult.insufficient_evidence || []).length > 0 && (
                <div style={{ background:"rgba(245,158,11,0.08)", border:"1px solid rgba(245,158,11,0.18)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#fcd34d", fontWeight:700, marginBottom:6 }}>證據不足</div>
                  {(qaResult.insufficient_evidence || []).map((item, idx) => (
                    <div key={idx} style={{ fontSize:12, color:"#fde68a", lineHeight:1.6 }}>- {item}</div>
                  ))}
                </div>
              )}
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>引用片段</div>
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {(qaResult.citations || []).map((item, idx) => (
                    <div key={idx} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                      <div style={{ fontSize:12, color:"#c4b5fd", marginBottom:4 }}>{item.title}</div>
                      <div style={{ fontSize:11, color:"#94a3b8", marginBottom:4 }}>{item.source_path}</div>
                      <div style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>{item.preview}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
          <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>異常草稿</div>
          <div style={{ display:"grid", gap:10 }}>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>問題描述</div>
              <textarea value={deviationForm.issue_description} onChange={e => setDeviationForm(prev => ({ ...prev, issue_description: e.target.value }))} style={{ ...inputStyle, minHeight:88, resize:"vertical" }} />
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10 }}>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>製程步驟</div>
                <input value={deviationForm.process_step} onChange={e => setDeviationForm(prev => ({ ...prev, process_step: e.target.value }))} style={inputStyle} />
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>批號</div>
                <input value={deviationForm.lot_no} onChange={e => setDeviationForm(prev => ({ ...prev, lot_no: e.target.value }))} style={inputStyle} />
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>嚴重度</div>
                <select value={deviationForm.severity} onChange={e => setDeviationForm(prev => ({ ...prev, severity: e.target.value }))} style={inputStyle}>
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </div>
            </div>
          </div>
          <button onClick={runDeviationDraft} disabled={deviationBusy} style={{ marginTop:12, background:"linear-gradient(135deg,#dc2626,#f97316)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: deviationBusy ? 0.6 : 1 }}>{deviationBusy ? "產生中..." : "產生異常草稿"}</button>
          {deviationMessage && <div style={{ marginTop:10, fontSize:12, color:"#fdba74" }}>{deviationMessage}</div>}
          {deviationResult && (
            <div style={{ marginTop:14, display:"grid", gap:10 }}>
              <div style={{ fontSize:12, color:"#fde68a", lineHeight:1.7 }}>{deviationResult.draft_summary}</div>
              {[
                ["已知事實", deviationResult.known_facts],
                ["可能原因", deviationResult.possible_causes],
                ["暫時圍堵措施", deviationResult.containment_actions],
                ["永久對策方向", deviationResult.permanent_actions],
                ["驗證計畫", deviationResult.verification_plan],
              ].map(([label, items]) => (
                <div key={label} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:"10px 12px" }}>
                  <div style={{ fontSize:12, color:"#e2e8f0", fontWeight:700, marginBottom:6 }}>{label}</div>
                  <div style={{ display:"flex", flexDirection:"column", gap:4 }}>
                    {(items || []).map((item, idx) => (
                      <div key={idx} style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>- {item}</div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop:18, background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18 }}>
        <div style={{ display:"flex", justifyContent:"space-between", gap:12, flexWrap:"wrap", alignItems:"center", marginBottom:10 }}>
          <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0" }}>文件搜尋結果</div>
          <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} style={{ ...inputStyle, width:260 }} />
            <button onClick={runSearch} disabled={searchBusy} style={{ background:"rgba(56,189,248,0.16)", border:"1px solid rgba(56,189,248,0.3)", borderRadius:10, color:"#bae6fd", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: searchBusy ? 0.6 : 1 }}>{searchBusy ? "搜尋中..." : "重新搜尋"}</button>
          </div>
        </div>
        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          {searchResults.map((item, idx) => (
            <div key={idx} style={{ background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.06)", borderRadius:10, padding:"10px 12px" }}>
              <div style={{ fontSize:12, color:"#7dd3fc", marginBottom:4 }}>{item.title}</div>
              <div style={{ fontSize:11, color:"#94a3b8", marginBottom:4 }}>{item.source_path}</div>
              <div style={{ fontSize:12, color:"#cbd5e1", lineHeight:1.6 }}>{item.preview}</div>
            </div>
          ))}
          {searchResults.length === 0 && <div style={{ fontSize:12, color:"#64748b" }}>尚未查到結果，可用文件關鍵字測試搜尋與切片。</div>}
        </div>
      </div>
    </div>
  );
}
