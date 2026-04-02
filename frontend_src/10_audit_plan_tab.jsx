function AuditPlanTab({ auditPlans, setAuditPlans }) {
  const [modal, setModal] = useState(null);
  const [filter, setFilter] = useState("all");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [attachmentBusy, setAttachmentBusy] = useState(false);
  const [importRecords, setImportRecords] = useState([]);
  const statusColor = s => s==="已完成"?"#22c55e":s==="執行中"?"#60a5fa":s==="計畫中"?"#f97316":"#ef4444";
  const filtered = filter==="all" ? auditPlans : auditPlans.filter(item=>item.status===filter);
  const upcoming = auditPlans.filter(item=>item.status==="計畫中" && daysUntil(item.scheduledDate)<=30 && daysUntil(item.scheduledDate)>=0);

  useEffect(() => {
    let cancelled = false;
    async function loadAttachments() {
      if (!modal) {
        setAttachments([]);
        return;
      }
      setAttachmentBusy(true);
      try {
        const payload = await apiJson("/api/audit-plans/" + encodeURIComponent(modal.id) + "/attachments");
        if (!cancelled) setAttachments(payload.attachments || []);
      } catch (err) {
        if (!cancelled) {
          setAttachments([]);
          setMessage("附件讀取失敗：" + err.message);
        }
      } finally {
        if (!cancelled) setAttachmentBusy(false);
      }
    }
    loadAttachments();
    return () => { cancelled = true; };
  }, [modal && modal.id]);

  async function persistRecords(records, doneMessage) {
    setBusy("save");
    setMessage("");
    try {
      const payload = await apiJson("/api/audit-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ records }),
      });
      setAuditPlans(payload.items || []);
      setMessage(doneMessage);
      return true;
    } catch (err) {
      setMessage("存檔失敗：" + err.message);
      return false;
    } finally {
      setBusy("");
    }
  }

  async function markComplete(plan) {
    const ok = await persistRecords([{ ...plan, status:"已完成", actualDate:new Date().toISOString().split("T")[0] }], "已更新稽核計畫。");
    if (ok) setModal(null);
  }

  async function deletePlan(id) {
    if (!window.confirm("確定要刪除這筆稽核計畫嗎？")) return;
    setBusy("delete");
    try {
      const payload = await apiJson("/api/audit-plans/" + encodeURIComponent(id), { method:"DELETE" });
      setAuditPlans(payload.items || []);
      setModal(null);
      setMessage("已刪除稽核計畫。");
    } catch (err) {
      setMessage("刪除失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function importPlanFile(file) {
    if (!file) return;
    setBusy("import");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const payload = await apiJson("/api/audit-plans/import", { method:"POST", body:formData });
      setImportRecords(payload.records || []);
      setMessage((payload.records || []).length ? "已讀取稽核計畫檔，請確認後再存入。" : "檔案已上傳，但目前沒有辨識到可匯入的稽核計畫資料。請確認檔案內容是否已填寫。");
    } catch (err) {
      setMessage("匯入失敗：" + err.message);
    } finally {
      setBusy("");
    }
  }

  async function confirmImportPlans() {
    if (!importRecords.length) return;
    const records = importRecords.map(({ missing_fields, ...record }) => record);
    const ok = await persistRecords(records, "已匯入稽核計畫。");
    if (ok) setImportRecords([]);
  }

  function updateImportRecord(field, value) {
    if (importRecords.length !== 1) return;
    setImportRecords([{ ...importRecords[0], [field]: value }]);
  }

  return (
    <div>
      <SectionHeader title="稽核計畫（MP-09）" count={auditPlans.length} color="#8b5cf6" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="全部計畫" value={auditPlans.length} color="#8b5cf6" />
        <StatCard label="已完成" value={auditPlans.filter(item=>item.status==="已完成").length} color="#22c55e" />
        <StatCard label="執行中" value={auditPlans.filter(item=>item.status==="執行中").length} color="#60a5fa" />
        <StatCard label="30 天內到期" value={upcoming.length} color="#f97316" sub="需排程確認" />
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, marginBottom:16, flexWrap:"wrap" }}>
        <div style={{ color:"#c4b5fd", fontSize:12 }}>{message || "可上傳稽核計畫表先解析，再確認存入；詳情內可預覽關聯文件。"}</div>
        <label style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>
          {busy==="import" ? "讀取中..." : "上傳稽核計畫檔"}
          <input type="file" accept=".docx,.xlsx,.pdf" onChange={e => importPlanFile(e.target.files && e.target.files[0])} style={{ display:"none" }} />
        </label>
      </div>
      {upcoming.length>0 && (
        <div style={{ background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: 12, padding: 16, marginBottom: 20 }}>
          <div style={{ fontSize: 13, color: "#fb923c", fontWeight: 700, marginBottom: 10 }}>30 天內即將執行</div>
          {upcoming.map(item => (<div key={item.id} style={{ display:"flex", gap:12, alignItems:"center", marginBottom:6 }}><span style={{ color:"#60a5fa", fontFamily:"monospace", fontSize:12 }}>{item.id}</span><span style={{ color:"#e2e8f0", fontSize:13 }}>{item.dept} · {formatDate(item.scheduledDate)}</span><Badge color="#f97316">剩 {daysUntil(item.scheduledDate)} 天</Badge></div>))}
        </div>
      )}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        {["all","計畫中","執行中","已完成"].map(key => (<button key={key} onClick={()=>setFilter(key)} style={{ background:filter===key?"rgba(139,92,246,0.2)":"rgba(255,255,255,0.04)", border:`1px solid ${filter===key?"rgba(139,92,246,0.5)":"rgba(255,255,255,0.1)"}`, borderRadius:8, color:filter===key?"#c4b5fd":"#64748b", cursor:"pointer", padding:"6px 14px", fontSize:12, fontWeight:600 }}>{key==="all"?"全部":key}</button>))}
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}>
          <thead><tr>{["編號","年度","期別","預定日期","部門","受稽人","稽核員","範圍","狀態","發現數","NC 數",""].map(h => (<th key={h} style={{ textAlign:"left", padding:"10px 12px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>))}</tr></thead>
          <tbody>
            {filtered.map((item,i) => (
              <tr key={item.id} style={{ background:i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                <td style={{ padding:"10px 12px", color:"#8b5cf6", fontWeight:700, fontFamily:"monospace", whiteSpace:"nowrap" }}>{item.id}</td>
                <td style={{ padding:"10px 12px", color:"#94a3b8" }}>{item.year}</td>
                <td style={{ padding:"10px 12px" }}><Badge color={item.period==="上半年"?"#60a5fa":"#f97316"}>{item.period}</Badge></td>
                <td style={{ padding:"10px 12px", color:"#94a3b8", whiteSpace:"nowrap" }}>{formatDate(item.scheduledDate)}</td>
                <td style={{ padding:"10px 12px", color:"#e2e8f0", fontWeight:600 }}>{item.dept}</td>
                <td style={{ padding:"10px 12px", color:"#94a3b8" }}>{item.auditee}</td>
                <td style={{ padding:"10px 12px", color:"#94a3b8" }}>{item.auditor}</td>
                <td style={{ padding:"10px 12px", color:"#64748b", fontSize:11 }}>{item.scope}</td>
                <td style={{ padding:"10px 12px" }}><Badge color={statusColor(item.status)}>{item.status}</Badge></td>
                <td style={{ padding:"10px 12px", textAlign:"center", color:item.findings>0?"#f97316":"#94a3b8", fontWeight:700 }}>{item.findings}</td>
                <td style={{ padding:"10px 12px", textAlign:"center", color:item.ncCount>0?"#ef4444":"#94a3b8", fontWeight:700 }}>{item.ncCount}</td>
                <td style={{ padding:"10px 12px" }}><div style={{ display:"flex", gap:8 }}><button onClick={()=>setModal(item)} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:6, color:"#94a3b8", cursor:"pointer", padding:"4px 10px", fontSize:11 }}>詳情</button><button onClick={() => deletePlan(item.id)} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:6, color:"#fca5a5", cursor:"pointer", padding:"4px 10px", fontSize:11 }}>刪除</button></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {modal && (<Modal title={`稽核計畫：${modal.id}`} onClose={() => setModal(null)}><div style={{ display:"flex", flexDirection:"column", gap:14 }}>{[["計畫編號",modal.id],["受稽部門",modal.dept],["預定日期",formatDate(modal.scheduledDate)],["實際日期",formatDate(modal.actualDate)],["稽核員",modal.auditor],["受稽人",modal.auditee],["稽核範圍",modal.scope],["狀態",modal.status],["發現數",String(modal.findings)],["NC 數",String(modal.ncCount)]].map(([k,v]) => (<div key={k} style={{ display:"flex", gap:12 }}><div style={{ fontSize:12, color:"#64748b", minWidth:90 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:13 }}>{v}</div></div>))}<div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:12 }}><div style={{ fontSize:12, color:"#c4b5fd", marginBottom:8 }}>關聯文件</div>{attachmentBusy ? <div style={{ color:"#94a3b8", fontSize:12 }}>讀取中...</div> : attachments.length===0 ? <div style={{ color:"#94a3b8", fontSize:12 }}>找不到關聯文件。</div> : <div style={{ display:"flex", flexDirection:"column", gap:10 }}>{attachments.map(item => (<div key={item.path} style={{ border:"1px solid rgba(255,255,255,0.08)", borderRadius:8, padding:10 }}><div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, flexWrap:"wrap" }}><div><div style={{ color:"#e2e8f0", fontSize:13, fontWeight:600 }}>{item.name}</div><div style={{ color:item.exists?"#64748b":"#fca5a5", fontSize:11 }}>{item.exists ? (item.previewable ? "可直接預覽 PDF" : item.text_previewable ? "可直接預覽文字內容" : "可開啟或下載") : "找不到文件"}</div></div>{item.exists && <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}><a href={item.download_url} style={{ color:"#93c5fd", fontSize:12, textDecoration:"none" }}>下載</a>{item.previewable && <a href={item.view_url} target="_blank" rel="noreferrer" style={{ color:"#c4b5fd", fontSize:12, textDecoration:"none" }}>新頁預覽</a>}{item.text_previewable && <a href={item.preview_text_url} target="_blank" rel="noreferrer" style={{ color:"#c4b5fd", fontSize:12, textDecoration:"none" }}>文字預覽</a>}</div>}</div>{item.previewable && item.exists && <iframe src={item.view_url} title={item.name} style={{ width:"100%", height:260, marginTop:10, border:"1px solid rgba(255,255,255,0.08)", borderRadius:8, background:"#fff" }} />}{item.text_previewable && item.exists && <iframe src={item.preview_text_url} title={item.name + "-text"} style={{ width:"100%", height:260, marginTop:10, border:"1px solid rgba(255,255,255,0.08)", borderRadius:8, background:"#fff" }} />}</div>))}</div>}</div><div style={{ display:"flex", gap:10, flexWrap:"wrap", marginTop:8 }}>{modal.status!=="已完成" && (<button onClick={()=>markComplete(modal)} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>標記完成</button>)}<button onClick={()=>deletePlan(modal.id)} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.28)", borderRadius:10, color:"#fca5a5", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>刪除這筆資料</button></div></div></Modal>)}
      {importRecords.length>0 && (<Modal title="匯入預覽" onClose={() => setImportRecords([])}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{importRecords.length===1 ? <div style={{ display:"flex", flexDirection:"column", gap:12 }}>{importRecords[0].missing_fields?.length>0 && <div style={{ background:"rgba(250,204,21,0.1)", border:"1px solid rgba(250,204,21,0.24)", borderRadius:8, padding:10, color:"#fde68a", fontSize:12 }}>以下欄位未完整讀取：{importRecords[0].missing_fields.join("、")}</div>}{[["預定日期","scheduledDate","date"],["受稽部門","dept","text"],["稽核員","auditor","text"],["受稽人","auditee","text"],["稽核範圍","scope","text"]].map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={importRecords[0][field]||""} onChange={e=>updateImportRecord(field, e.target.value)} style={inputStyle} /></div>))}</div> : <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:10, padding:12 }}><div style={{ color:"#e2e8f0", fontWeight:700, marginBottom:8 }}>本次共讀到 {importRecords.length} 筆資料</div>{importRecords.slice(0,8).map(item => (<div key={item.id} style={{ display:"flex", justifyContent:"space-between", gap:12, borderBottom:"1px solid rgba(255,255,255,0.05)", padding:"8px 0" }}><span style={{ color:"#c4b5fd", fontFamily:"monospace", fontSize:12 }}>{item.id}</span><span style={{ color:"#94a3b8", fontSize:12 }}>{item.dept || "未讀到部門"}</span><span style={{ color:"#94a3b8", fontSize:12 }}>{formatDate(item.scheduledDate)}</span></div>))}</div>}<button onClick={confirmImportPlans} disabled={busy==="save"} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8, opacity:busy==="save"?0.6:1 }}>{busy==="save"?"存檔中...":"確認存入"}</button></div></Modal>)}
    </div>
  );
}
