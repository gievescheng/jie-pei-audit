function EnvironmentTab({ envRecords, setEnvRecords }) {
  const emptyDraft = { date:"", measuredAt:"", location:"潔淨室A區", point:"", particles03:0, particles05:0, particles5:0, temp:"", humidity:"", pressure:"", operator:"", result:"" };
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [rangeStart, setRangeStart] = useState("");
  const [rangeEnd, setRangeEnd] = useState("");
  const [summary, setSummary] = useState({ total: envRecords.length, passed: envRecords.filter(r=>r.result==="合格").length, warning: envRecords.filter(r=>r.result==="警告").length, failed: envRecords.filter(r=>r.result==="不合格").length });
  const [showAdd, setShowAdd] = useState(false);
  const [draft, setDraft] = useState(emptyDraft);
  const [importPreview, setImportPreview] = useState([]);
  const [importSummary, setImportSummary] = useState(null);
  const environmentSortKey = (item) => {
    const measuredAt = String(item?.measuredAt || "").trim();
    if (measuredAt) {
      const measuredValue = Date.parse(measuredAt);
      if (!Number.isNaN(measuredValue)) return measuredValue;
    }
    const datePart = String(item?.date || "").trim();
    const timeMatch = String(item?.location || "").match(/(\d{1,2}:\d{2}:\d{2})/);
    const timePart = timeMatch ? timeMatch[1] : "00:00:00";
    const candidate = `${datePart}T${timePart}`;
    const value = Date.parse(candidate);
    return Number.isNaN(value) ? 0 : value;
  };
  const sorted = [...envRecords].sort((a, b) => environmentSortKey(a) - environmentSortKey(b));
  const resultColor = r => r==="合格"?"#22c55e":r==="警告"?"#eab308":"#ef4444";

  useEffect(() => {
    const nextSummary = {
      total: envRecords.length,
      passed: envRecords.filter(item=>item.result==="合格").length,
      warning: envRecords.filter(item=>item.result==="警告").length,
      failed: envRecords.filter(item=>item.result==="不合格").length,
    };
    setSummary(nextSummary);
  }, [envRecords]);

  function buildRecord(record) {
    const point = String(record.point || "").trim();
    const measuredAt = String(record.measuredAt || "").trim();
    const particles03 = parseInt(record.particles03 || 0, 10) || 0;
    const particles05 = parseInt(record.particles05 || 0, 10) || 0;
    const particles5 = parseInt(record.particles5 || 0, 10) || 0;
    const temp = record.temp === "" ? "" : parseFloat(record.temp || 0) || 0;
    const humidity = record.humidity === "" ? "" : parseFloat(record.humidity || 0) || 0;
    const pressure = record.pressure === "" ? "" : parseFloat(record.pressure || 0) || 0;
    let result = record.result;
    if (!result) {
      if (particles05 > 1000 || particles5 > 35 || (temp !== "" && (temp > 23 || temp < 21)) || (humidity !== "" && (humidity > 50 || humidity < 40)) || (pressure !== "" && pressure < 10)) result = "不合格";
      else if (particles05 > 800 || particles5 > 20 || (temp !== "" && temp > 22.5) || (humidity !== "" && humidity > 48)) result = "警告";
      else result = "合格";
    }
    return { ...record, point, measuredAt, particles03, particles05, particles1:0, particles5, temp, humidity, pressure, result };
  }

  async function saveRecords(records, doneMessage, replaceSourceFile = "") {
    setBusy("save");
    setMessage("");
    try {
      const payload = await apiJson("/api/environment-records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records, replace_source_file: replaceSourceFile }),
      });
      setEnvRecords(payload.items || []);
      setSummary(payload.summary || { total:0, passed:0, warning:0, failed:0 });
      setMessage(doneMessage);
      return true;
    } catch (err) {
      setMessage("存檔失敗：" + err.message);
      return false;
    } finally {
      setBusy("");
    }
  }

  async function loadRange(start = rangeStart, end = rangeEnd) {
    setBusy("query");
    setMessage("");
    try {
      const params = new URLSearchParams();
      if (start) params.set("start", start);
      if (end) params.set("end", end);
      const payload = await apiJson("/api/environment-records" + (params.toString() ? "?" + params.toString() : ""));
      setEnvRecords(payload.items || []);
      setSummary(payload.summary || { total:0, passed:0, warning:0, failed:0 });
      setMessage("已依時間區間讀取資料。");
    } catch (err) {
      setMessage("讀取失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function addRecord() {
    const ok = await saveRecords([buildRecord(draft)], "已新增環境監控資料。");
    if (!ok) return;
    setShowAdd(false);
    setDraft(emptyDraft);
  }

  async function deleteRecord(id) {
    if (!window.confirm("確定要刪除這筆監控資料嗎？")) return;
    setBusy("delete");
    try {
      const payload = await apiJson("/api/environment-records/" + encodeURIComponent(id), { method:"DELETE" });
      setEnvRecords(payload.items || []);
      setSummary(payload.summary || { total:0, passed:0, warning:0, failed:0 });
      setMessage("已刪除監控資料。");
    } catch (err) {
      setMessage("刪除失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function deleteRange() {
    if (!rangeStart && !rangeEnd) {
      setMessage("請先選擇要刪除的日期區間。");
      return;
    }
    if (!window.confirm("確定要刪除此時間區間的所有監控資料嗎？")) return;
    setBusy("delete-range");
    try {
      const payload = await apiJson("/api/environment-records/delete-range", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start: rangeStart, end: rangeEnd }),
      });
      setEnvRecords(payload.items || []);
      setSummary(payload.summary || { total:0, passed:0, warning:0, failed:0 });
      setMessage(`已刪除 ${payload.deleted || 0} 筆資料。`);
    } catch (err) {
      setMessage("區間刪除失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function importFile(file) {
    if (!file) return;
    setBusy("import");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const payload = await apiJson("/api/environment-records/import", { method:"POST", body:formData });
      setImportPreview(payload.records || []);
      setImportSummary(payload.summary || null);
      setMessage((payload.records || []).length ? "已讀取原始資料，請確認後再存入。" : "檔案已上傳，但目前沒有辨識到可匯入的環境監控資料。請確認原始檔格式。");
    } catch (err) {
      setMessage("匯入失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function confirmImport() {
    if (!importPreview.length) return;
    const replaceSourceFile = importPreview[0]?.source_file || "";
    const records = importPreview.map(({ missing_fields, id, ...record }) => record);
    const ok = await saveRecords(records, `已匯入 ${records.length} 筆環境監控資料。`, replaceSourceFile);
    if (!ok) return;
    setImportPreview([]);
    setImportSummary(null);
  }

  const passRate = summary.total > 0 ? Math.round((summary.passed / summary.total) * 100) : 0;
  const formatMaybeNumber = (value, digits = 1) => {
    if (value === "" || value === null || value === undefined) return "—";
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric.toFixed(digits) : "—";
  };
  const formatMaybeInteger = (value) => {
    if (value === "" || value === null || value === undefined) return "—";
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric.toLocaleString() : "—";
  };

  return (
    <div>
      <SectionHeader title="工作環境監控（MP-06）" count={envRecords.length} color="#14b8a6" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="總筆數" value={summary.total} color="#14b8a6" />
        <StatCard label="合格" value={summary.passed} color="#22c55e" />
        <StatCard label="警告" value={summary.warning} color="#eab308" />
        <StatCard label="不合格" value={summary.failed} color="#ef4444" />
        <StatCard label="合格率" value={`${passRate}%`} color={passRate>=90?"#22c55e":passRate>=80?"#eab308":"#ef4444"} sub="目前篩選結果" />
      </div>
      <div style={{ background: "rgba(20,184,166,0.06)", border: "1px solid rgba(20,184,166,0.2)", borderRadius: 12, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: "#2dd4bf", fontWeight: 700, marginBottom: 8 }}>Class 1000 參考標準</div>
        <div style={{ display:"flex", gap:24, flexWrap:"wrap", fontSize:12, color:"#64748b" }}>
          <span>0.5μm 粒子 ≤ 1000</span>
          <span>5μm 粒子 ≤ 35</span>
          <span>溫度 21–23°C</span>
          <span>濕度 40–50% RH</span>
          <span>正壓 ≥ 10 Pa</span>
        </div>
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, marginBottom:14, flexWrap:"wrap" }}>
        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
          <input type="date" value={rangeStart} onChange={e => setRangeStart(e.target.value)} style={{ ...inputStyle, width:170 }} />
          <span style={{ color:"#64748b", fontSize:12 }}>至</span>
          <input type="date" value={rangeEnd} onChange={e => setRangeEnd(e.target.value)} style={{ ...inputStyle, width:170 }} />
          <button onClick={() => loadRange()} style={{ background:"rgba(20,184,166,0.14)", border:"1px solid rgba(20,184,166,0.28)", borderRadius:10, color:"#99f6e4", cursor:"pointer", padding:"9px 16px", fontSize:13, fontWeight:700 }}>查詢區間</button>
          <button onClick={() => { setRangeStart(""); setRangeEnd(""); loadRange("", ""); }} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:10, color:"#cbd5e1", cursor:"pointer", padding:"9px 16px", fontSize:13, fontWeight:700 }}>清除篩選</button>
        </div>
        <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
          <label style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>
            {busy==="import" ? "讀取中..." : "上傳原始資料"}
            <input type="file" accept=".xlsx,.csv" onChange={e => importFile(e.target.files && e.target.files[0])} style={{ display:"none" }} />
          </label>
          <button onClick={deleteRange} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:10, color:"#fca5a5", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>刪除此區間</button>
          <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #0d9488, #14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>新增監控資料</button>
        </div>
      </div>
      <div style={{ color:"#99f6e4", fontSize:12, marginBottom:14 }}>{message || "可依日期區間查詢或刪除，也可上傳 Excel/CSV 先讀取再存入。"}</div>
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
          <thead><tr>{["編號","日期","點位","地點","0.3μm","0.5μm","5.0μm","溫度","濕度","正壓","記錄者","結果",""].map(h => (<th key={h} style={{ textAlign:"left", padding:"8px 10px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>))}</tr></thead>
          <tbody>
            {sorted.map((item,i) => (
              <tr key={item.id} style={{ background:i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                <td style={{ padding:"8px 10px", color:"#14b8a6", fontFamily:"monospace" }}>{item.id}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8", whiteSpace:"nowrap" }}>{formatDate(item.date)}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{item.point || "—"}</td>
                <td style={{ padding:"8px 10px", color:"#e2e8f0" }}>{item.location}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{formatMaybeInteger(item.particles03)}</td>
                <td style={{ padding:"8px 10px", color:item.particles05>1000?"#ef4444":item.particles05>800?"#eab308":"#94a3b8", fontWeight:item.particles05>800?700:400 }}>{formatMaybeInteger(item.particles05)}</td>
                <td style={{ padding:"8px 10px", color:item.particles5>35?"#ef4444":item.particles5>20?"#eab308":"#94a3b8", fontWeight:item.particles5>20?700:400 }}>{formatMaybeInteger(item.particles5)}</td>
                <td style={{ padding:"8px 10px", color:item.temp === "" || item.temp === null || item.temp === undefined ? "#64748b" : item.temp>23||item.temp<21?"#ef4444":"#94a3b8" }}>{formatMaybeNumber(item.temp)}</td>
                <td style={{ padding:"8px 10px", color:item.humidity === "" || item.humidity === null || item.humidity === undefined ? "#64748b" : item.humidity>50||item.humidity<40?"#ef4444":"#94a3b8" }}>{formatMaybeNumber(item.humidity)}</td>
                <td style={{ padding:"8px 10px", color:item.pressure === "" || item.pressure === null || item.pressure === undefined ? "#64748b" : item.pressure<10?"#ef4444":"#94a3b8" }}>{formatMaybeNumber(item.pressure)}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{item.operator || "—"}</td>
                <td style={{ padding:"8px 10px" }}><Badge color={resultColor(item.result)}>{item.result}</Badge></td>
                <td style={{ padding:"8px 10px" }}><button onClick={() => deleteRecord(item.id)} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:8, color:"#fca5a5", cursor:"pointer", padding:"6px 12px", fontSize:11 }}>刪除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {showAdd && (<Modal title="新增環境監控資料" onClose={() => setShowAdd(false)}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{[["日期","date","date"],["量測時間","measuredAt","datetime-local"],["點位","point","text"],["地點","location","text"],["0.3μm 粒子","particles03","number"],["0.5μm 粒子","particles05","number"],["5.0μm 粒子","particles5","number"],["溫度","temp","number"],["濕度","humidity","number"],["正壓","pressure","number"],["記錄者","operator","text"]].map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={draft[field]} onChange={e=>setDraft({...draft,[field]:e.target.value})} style={inputStyle} /></div>))}<button onClick={addRecord} disabled={busy==="save"} style={{ background:"linear-gradient(135deg,#0d9488,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8, opacity:busy==="save"?0.6:1 }}>{busy==="save"?"存檔中...":"確認新增"}</button></div></Modal>)}
      {importPreview.length>0 && (<Modal title="匯入預覽" onClose={() => { setImportPreview([]); setImportSummary(null); }}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{importSummary && <div style={{ background:"rgba(20,184,166,0.08)", border:"1px solid rgba(20,184,166,0.24)", borderRadius:8, padding:10, color:"#99f6e4", fontSize:12 }}>本次解析：{importSummary.total} 筆，合格 {importSummary.passed}、警告 {importSummary.warning}、不合格 {importSummary.failed}</div>}<div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:12, maxHeight:340, overflowY:"auto" }}>{importPreview.slice(0,20).map(item => (<div key={item.id || item.source_file + item.date} style={{ display:"grid", gridTemplateColumns:"110px 1fr 120px", gap:12, borderBottom:"1px solid rgba(255,255,255,0.05)", padding:"8px 0" }}><span style={{ color:"#5eead4", fontFamily:"monospace", fontSize:12 }}>{formatDate(item.date)}</span><span style={{ color:"#94a3b8", fontSize:12 }}>點位 {item.point || "—"} · {item.location} · 0.3μm {formatMaybeInteger(item.particles03)} · 0.5μm {formatMaybeInteger(item.particles05)}</span><span style={{ color:item.missing_fields?.length?"#fde68a":"#cbd5e1", fontSize:12, textAlign:"right" }}>{item.missing_fields?.length ? `需補 ${item.missing_fields.join("/")}` : item.result}</span></div>))}</div><button onClick={confirmImport} disabled={busy==="save"} style={{ background:"linear-gradient(135deg,#0d9488,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8, opacity:busy==="save"?0.6:1 }}>{busy==="save"?"存檔中...":"確認存入"}</button></div></Modal>)}
    </div>
  );
}
