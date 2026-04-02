// ─── NON-CONFORMANCE TAB (MP-15) ─────────────────────────────────────────────
function NonConformanceTab({ nonConformances: items, setNonConformances: setItems, highlightNcId, onHighlightDone, expandNcId, onExpandDone }) {
  const emptyDraft = { id:"", date:"", dept:"", type:"製程異常", description:"", severity:"輕微", rootCause:"", correctiveAction:"", responsible:"", dueDate:"", status:"待處理", closeDate:"", effectiveness:"" };
  const [modal, setModal] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState(emptyDraft);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [importDraft, setImportDraft] = useState(null);
  const [importMissing, setImportMissing] = useState([]);
  const rowRefs = useRef({});

  useEffect(() => {
    if (!highlightNcId) return;
    const el = rowRefs.current[highlightNcId];
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.style.outline = "2px solid #f59e0b";
      el.style.outlineOffset = "3px";
      el.style.transition = "outline 0.2s";
      const t = setTimeout(() => {
        el.style.outline = "";
        el.style.outlineOffset = "";
        onHighlightDone?.();
      }, 2500);
      return () => clearTimeout(t);
    }
  }, [highlightNcId]);

  useEffect(() => {
    if (!expandNcId) return;
    const nc = items.find(item => String(item.id) === String(expandNcId));
    if (nc) {
      setModal(nc);
      onExpandDone?.();
    }
  }, [expandNcId]);

  const statusColor = s => s==="已關閉"?"#22c55e":s==="處理中"?"#f97316":s==="待處理"?"#ef4444":"#eab308";
  const sevColor = s => s==="重大"?"#ef4444":s==="中度"?"#eab308":"#60a5fa";
  const enriched = items.map(item => ({ ...item, overdue: item.status !== "已關閉" && daysUntil(item.dueDate) < 0 }));

  async function persistRecord(record, doneMessage) {
    setBusy("save");
    setMessage("");
    try {
      const payload = await apiJson("/api/nonconformances", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ record }),
      });
      setItems(payload.items || []);
      setMessage(doneMessage);
      return true;
    } catch (err) {
      setMessage("存檔失敗：" + err.message);
      return false;
    } finally {
      setBusy("");
    }
  }

  async function addRecord() {
    const ok = await persistRecord(draft, "已新增不符合報告。");
    if (!ok) return;
    setShowAdd(false);
    setDraft(emptyDraft);
  }

  async function closeRecord(item) {
    const ok = await persistRecord({ ...item, status: "已關閉", closeDate: new Date().toISOString().split("T")[0], effectiveness: item.effectiveness || "有效" }, "已更新為結案。");
    if (ok) setModal(null);
  }

  async function deleteRecord(id) {
    if (!window.confirm("確定要刪除這筆不符合報告嗎？")) return;
    setBusy("delete");
    setMessage("");
    try {
      const payload = await apiJson("/api/nonconformances/" + encodeURIComponent(id), { method: "DELETE" });
      setItems(payload.items || []);
      setModal(null);
      setMessage("已刪除不符合報告。");
    } catch (err) {
      setMessage("刪除失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function importFile(file) {
    if (!file) return;
    setBusy("import");
    setMessage("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const payload = await apiJson("/api/nonconformances/import", { method: "POST", body: formData });
      setImportDraft(payload.draft || null);
      setImportMissing(payload.missing_fields || []);
      setMessage("已讀取檔案，請確認資料後再存入。");
    } catch (err) {
      setMessage("匯入失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function confirmImport() {
    if (!importDraft) return;
    const ok = await persistRecord(importDraft, "已匯入不符合報告。");
    if (!ok) return;
    setImportDraft(null);
    setImportMissing([]);
  }

  return (
    <div>
      <SectionHeader title="不符合管理（MP-15）" count={items.length} color="#f87171" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="待處理" value={items.filter(item=>item.status==="待處理").length} color="#ef4444" sub="尚未開始" />
        <StatCard label="處理中" value={items.filter(item=>item.status==="處理中").length} color="#f97316" sub="追蹤中" />
        <StatCard label="已關閉" value={items.filter(item=>item.status==="已關閉").length} color="#22c55e" sub="已完成" />
        <StatCard label="已逾期" value={enriched.filter(item=>item.overdue).length} color="#ef4444" sub="需優先處理" />
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, marginBottom:14, flexWrap:"wrap" }}>
        <div style={{ color:"#fca5a5", fontSize:12 }}>{message || "可刪除錯誤資料，也可上傳報告檔先解析再確認。"}</div>
        <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
          <label style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>
            {busy==="import" ? "讀取中..." : "上傳報告檔"}
            <input type="file" accept=".docx,.xlsx,.pdf" onChange={e => importFile(e.target.files && e.target.files[0])} style={{ display:"none" }} />
          </label>
          <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #dc2626, #ef4444)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "9px 18px", fontSize: 13, fontWeight: 700 }}>新增報告</button>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {enriched.map(item => (
          <div key={item.id} ref={el => { rowRefs.current[item.id] = el; }} style={{ background: item.overdue?"rgba(239,68,68,0.12)":"rgba(255,255,255,0.03)", border: `1px solid ${item.overdue?"rgba(239,68,68,0.3)":"rgba(255,255,255,0.08)"}`, borderRadius: 12, padding: "14px 18px" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 260 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6, flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 700, color: "#60a5fa", fontFamily: "monospace", fontSize: 13 }}>{item.id}</span>
                  <Badge color={sevColor(item.severity)}>{item.severity}</Badge>
                  <Badge color={statusColor(item.status)}>{item.status}</Badge>
                  {item.overdue && <Badge color="#ef4444">已逾期</Badge>}
                </div>
                <div style={{ color: "#e2e8f0", fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{item.description}</div>
                <div style={{ fontSize: 12, color: "#64748b" }}>{item.dept} · {item.type} · 發生日 {formatDate(item.date)} · 責任人 {item.responsible || "未填"}</div>
              </div>
              <div style={{ textAlign: "right", minWidth: 120 }}>
                <div style={{ fontSize: 12, color: "#64748b" }}>到期日</div>
                <div style={{ fontWeight: 700, color: item.overdue?"#ef4444":"#e2e8f0", fontSize: 13 }}>{formatDate(item.dueDate)}</div>
                {item.status==="已關閉" && <div style={{ fontSize: 11, color: "#4ade80", marginTop: 4 }}>結案 {formatDate(item.closeDate)}</div>}
              </div>
              <div style={{ display:"flex", gap:8 }}>
                <button onClick={() => setModal(item)} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>詳情</button>
                <button onClick={() => deleteRecord(item.id)} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:8, color:"#fca5a5", cursor:"pointer", padding:"6px 14px", fontSize:12 }}>刪除</button>
              </div>
            </div>
          </div>
        ))}
      </div>
      {modal && (<Modal title={`不符合報告：${modal.id}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 14 }}>{[["發生日",formatDate(modal.date)],["部門",modal.dept],["類型",modal.type],["嚴重度",modal.severity],["問題描述",modal.description],["原因分析",modal.rootCause],["改善措施",modal.correctiveAction],["責任人",modal.responsible],["到期日",formatDate(modal.dueDate)],["狀態",modal.status],["結案日",formatDate(modal.closeDate)],["有效性",modal.effectiveness||"未填"]].map(([k,v]) => (<div key={k} style={{ display:"flex", gap:12 }}><div style={{ fontSize:12, color:"#64748b", minWidth:90 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:13 }}>{v}</div></div>))}<div style={{ display:"flex", gap:10, flexWrap:"wrap", marginTop:8 }}>{modal.status!=="已關閉" && (<button onClick={() => closeRecord(modal)} style={{ background:"linear-gradient(135deg,#059669,#10b981)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>標記結案</button>)}<button onClick={() => deleteRecord(modal.id)} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:10, color:"#fca5a5", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>刪除這筆資料</button></div></div></Modal>)}
      {showAdd && (<Modal title="新增不符合報告" onClose={() => setShowAdd(false)}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{[["發生日","date","date"],["部門","dept","text"],["問題描述","description","text"],["原因分析","rootCause","text"],["改善措施","correctiveAction","text"],["責任人","responsible","text"],["到期日","dueDate","date"]].map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={draft[field]} onChange={e=>setDraft({...draft,[field]:e.target.value})} style={inputStyle} /></div>))}<div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>類型</div><select value={draft.type} onChange={e=>setDraft({...draft,type:e.target.value})} style={inputStyle}><option>製程異常</option><option>文件不符</option><option>人員作業</option><option>客戶投訴</option><option>量測異常</option><option>來料不合格</option></select></div><div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>嚴重度</div><select value={draft.severity} onChange={e=>setDraft({...draft,severity:e.target.value})} style={inputStyle}><option>輕微</option><option>中度</option><option>重大</option></select></div><button onClick={addRecord} disabled={busy==="save"} style={{ background:"linear-gradient(135deg,#dc2626,#ef4444)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8, opacity:busy==="save"?0.6:1 }}>{busy==="save"?"存檔中...":"確認新增"}</button></div></Modal>)}
      {importDraft && (<Modal title="匯入預覽" onClose={() => { setImportDraft(null); setImportMissing([]); }}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{importMissing.length>0 && <div style={{ background:"rgba(250,204,21,0.1)", border:"1px solid rgba(250,204,21,0.24)", borderRadius:8, padding:10, color:"#fde68a", fontSize:12 }}>以下欄位未完整讀取：{importMissing.join("、")}，請先補齊。</div>}{[["發生日","date","date"],["部門","dept","text"],["問題描述","description","text"],["原因分析","rootCause","text"],["改善措施","correctiveAction","text"],["責任人","responsible","text"],["到期日","dueDate","date"]].map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={importDraft[field]||""} onChange={e=>setImportDraft({...importDraft,[field]:e.target.value})} style={inputStyle} /></div>))}<div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>類型</div><select value={importDraft.type||"製程異常"} onChange={e=>setImportDraft({...importDraft,type:e.target.value})} style={inputStyle}><option>製程異常</option><option>文件不符</option><option>人員作業</option><option>客戶投訴</option><option>量測異常</option><option>來料不合格</option></select></div><div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>嚴重度</div><select value={importDraft.severity||"輕微"} onChange={e=>setImportDraft({...importDraft,severity:e.target.value})} style={inputStyle}><option>輕微</option><option>中度</option><option>重大</option></select></div><button onClick={confirmImport} disabled={busy==="save"} style={{ background:"linear-gradient(135deg,#dc2626,#ef4444)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8, opacity:busy==="save"?0.6:1 }}>{busy==="save"?"存檔中...":"確認存入"}</button></div></Modal>)}
    </div>
  );
}
