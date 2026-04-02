// ─── DOCUMENTS TAB ───────────────────────────────────────────────────────────
function DocumentsTab({ documents, setDocuments }) {
  const [modal, setModal]       = useState(null);
  const [mode, setMode]         = useState(null);   // null | "single" | "bulk"
  const [err, setErr]           = useState("");
  const [dragOver, setDragOver] = useState(false);

  // ── Single-add state ──────────────────────────────────────────────────────
  const emptyDoc = { id:"", name:"", type:"管理程序", version:"1.0", department:"", createdDate:"", author:"", retentionYears:16, fileName:"", fileSize:"", fileType:"", fileData:"" };
  const [newDoc, setNewDoc] = useState({ ...emptyDoc });

  // ── Bulk-upload state ─────────────────────────────────────────────────────
  const [bulkItems, setBulkItems] = useState([]);   // array of draft doc objects
  const [bulkDone,  setBulkDone]  = useState(false);

  // ── Helpers ───────────────────────────────────────────────────────────────
  const enriched = documents.map(d => {
    const expiryDate = new Date(d.createdDate);
    expiryDate.setFullYear(expiryDate.getFullYear() + (d.retentionYears || 16));
    const expiryStr = expiryDate.toISOString().split("T")[0];
    return { ...d, expiryStr, daysToExpiry: daysUntil(expiryStr) };
  });

  function parseDocxMeta(ab) {
    try {
      const raw = new TextDecoder("utf-8", { fatal: false }).decode(new Uint8Array(ab));
      const g = re => (raw.match(re)||[])[1]||"";
      return {
        title:    g(/<dc:title[^>]*>([^<]*)<\/dc:title>/),
        creator:  g(/<dc:creator[^>]*>([^<]*)<\/dc:creator>/) || g(/<cp:lastModifiedBy[^>]*>([^<]*)<\/cp:lastModifiedBy>/),
        revision: g(/<cp:revision[^>]*>([^<]*)<\/cp:revision>/),
        created:  g(/<dcterms:created[^>]*>([^<]*)<\/dcterms:created>/),
        modified: g(/<dcterms:modified[^>]*>([^<]*)<\/dcterms:modified>/),
      };
    } catch(e) { return {}; }
  }
  function parsePdfMeta(ab) {
    try {
      const raw = new TextDecoder("latin1", { fatal: false }).decode(new Uint8Array(ab));
      const g = re => (raw.match(re)||[])[1]||"";
      const d = g(/\/CreationDate\s*\(D:(\d{8})/);
      return { title: g(/\/Title\s*\(([^)]+)\)/), author: g(/\/Author\s*\(([^)]+)\)/),
               date: d.length===8 ? `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}` : "" };
    } catch(e) { return {}; }
  }

  // Process one File object → return a draft doc object (with fileData)
  function processFile(file) {
    return new Promise(resolve => {
      const ext     = file.name.split(".").pop().toLowerCase();
      const sizeStr = file.size > 1048576 ? (file.size/1048576).toFixed(1)+" MB" : (file.size/1024).toFixed(0)+" KB";
      const baseName = file.name.replace(/\.[^.]+$/, "");
      const draft = {
        id: "", name: baseName, type: "管理程序", version: "1.0",
        department: "", createdDate: "", author: "",
        retentionYears: 16, fileName: file.name, fileSize: sizeStr,
        fileType: ext.toUpperCase(), fileData: "", _status: "pending"
      };
      // Read as ArrayBuffer for metadata, then as DataURL for storage
      const arrReader = new FileReader();
      arrReader.onload = ev => {
        const ab = ev.target.result;
        // Extract metadata
        if (["docx","xlsx","pptx"].includes(ext)) {
          const m = parseDocxMeta(ab);
          if (m.title)    draft.name        = m.title;
          if (m.creator)  draft.author      = m.creator;
          if (m.revision) draft.version     = parseInt(m.revision)>0 ? `1.${parseInt(m.revision)-1}` : "1.0";
          if (m.created||m.modified) draft.createdDate = (m.created||m.modified).substring(0,10);
        } else if (ext === "pdf") {
          const m = parsePdfMeta(ab);
          if (m.title)  draft.name        = m.title  || draft.name;
          if (m.author) draft.author      = m.author;
          if (m.date)   draft.createdDate = m.date;
        }
        // Now read as DataURL
        const b64r = new FileReader();
        b64r.onload = e2 => { draft.fileData = e2.target.result; resolve(draft); };
        b64r.readAsDataURL(file);
      };
      arrReader.readAsArrayBuffer(file);
    });
  }

  // ── Single upload handler ─────────────────────────────────────────────────
  async function handleSingleFileUpload(e) {
    const file = e.target.files[0]; if (!file) return;
    const draft = await processFile(file);
    setNewDoc(prev => ({ ...prev, ...draft }));
  }
  function handleSingleAdd() {
    if (!newDoc.id.trim()||!newDoc.name.trim()||!newDoc.department.trim()||!newDoc.createdDate) {
      setErr("請填寫所有必填欄位：文件編號、名稱、制定部門、制定日期"); return;
    }
    setErr("");
    setDocuments(prev => [...prev, { ...newDoc, retentionYears: parseInt(newDoc.retentionYears)||16 }]);
    setMode(null); setNewDoc({ ...emptyDoc });
  }

  // ── Bulk upload handlers ──────────────────────────────────────────────────
  async function handleBulkFiles(files) {
    if (!files || files.length === 0) return;
    setBulkDone(false);
    const drafts = await Promise.all(Array.from(files).map(processFile));
    setBulkItems(prev => [...prev, ...drafts]);
  }
  function updateBulkItem(idx, field, value) {
    setBulkItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  }
  function removeBulkItem(idx) {
    setBulkItems(prev => prev.filter((_, i) => i !== idx));
  }
  function confirmBulkUpload() {
    const valid = bulkItems.filter(d => d.id.trim() && d.name.trim() && d.department.trim() && d.createdDate);
    const invalid = bulkItems.length - valid.length;
    if (invalid > 0) { setErr(`尚有 ${invalid} 筆資料未填完整（需：編號、名稱、部門、日期）`); return; }
    setErr("");
    setDocuments(prev => [...prev, ...valid.map(d => ({ ...d, retentionYears: parseInt(d.retentionYears)||16, _status: undefined }))]);
    setBulkItems([]); setBulkDone(true);
    setTimeout(() => { setMode(null); setBulkDone(false); }, 1500);
  }
  function closeModal() { setMode(null); setNewDoc({ ...emptyDoc }); setBulkItems([]); setErr(""); setBulkDone(false); }

  // ── Shared styles ─────────────────────────────────────────────────────────
  const dropZoneStyle = over => ({
    display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center",
    gap:10, background: over?"rgba(124,58,237,0.12)":"rgba(255,255,255,0.03)",
    border:`2px dashed ${over?"rgba(124,58,237,0.9)":"rgba(124,58,237,0.4)"}`,
    borderRadius:14, padding:"28px 20px", cursor:"pointer", transition:"all 0.2s", textAlign:"center"
  });

  return (
    <div>
      <SectionHeader title="文件版本管控" count={documents.length} color="#a78bfa" />
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <StatCard label="管理手冊"  value={documents.filter(d=>d.type==="管理手冊").length}  color="#a78bfa" />
        <StatCard label="管理程序"  value={documents.filter(d=>d.type==="管理程序").length}  color="#60a5fa" />
        <StatCard label="作業指導書" value={documents.filter(d=>d.type==="作業指導書").length} color="#34d399" />
        <StatCard label="總文件數"  value={documents.length} color="#f97316" />
      </div>

      {/* Action buttons */}
      <div style={{ display:"flex", gap:10, justifyContent:"flex-end", marginBottom:14 }}>
        <button onClick={() => { setMode("bulk"); setErr(""); }} style={{ background:"linear-gradient(135deg,#0891b2,#06b6d4)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>
          &#128229; 批量上傳
        </button>
        <button onClick={() => { setMode("single"); setErr(""); }} style={{ background:"linear-gradient(135deg,#7c3aed,#4f46e5)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>
          ＋ 新增文件
        </button>
      </div>

      {/* Document table */}
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}>
          <thead><tr>{["文件編號","文件名稱","類別","版本","制定部門","制定日期","制定者","保存至","檔案",""].map(h=>(
            <th key={h} style={{ textAlign:"left", padding:"10px 12px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>
          ))}</tr></thead>
          <tbody>
            {enriched.map((doc, i) => (
              <tr key={doc.id} style={{ background: i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                <td style={{ padding:"10px 12px", color:"#60a5fa", fontWeight:700, fontFamily:"monospace" }}>{doc.id}</td>
                <td style={{ padding:"10px 12px", color:"#e2e8f0", fontWeight:600 }}>{doc.name}</td>
                <td style={{ padding:"10px 12px" }}><Badge color={doc.type==="管理手冊"?"#a78bfa":"#60a5fa"}>{doc.type}</Badge></td>
                <td style={{ padding:"10px 12px" }}><span style={{ background:"rgba(34,197,94,0.1)", color:"#4ade80", borderRadius:6, padding:"2px 8px", fontWeight:700, fontFamily:"monospace" }}>v{doc.version}</span></td>
                <td style={{ padding:"10px 12px", color:"#94a3b8" }}>{doc.department}</td>
                <td style={{ padding:"10px 12px", color:"#94a3b8", whiteSpace:"nowrap" }}>{formatDate(doc.createdDate)}</td>
                <td style={{ padding:"10px 12px", color:"#94a3b8" }}>{doc.author}</td>
                <td style={{ padding:"10px 12px", whiteSpace:"nowrap" }}><span style={{ color:doc.daysToExpiry<365?"#f97316":"#64748b", fontFamily:"monospace", fontSize:12 }}>{formatDate(doc.expiryStr)}</span></td>
                <td style={{ padding:"10px 12px" }}>
                  {doc.pdfPath ? (<a href={encodeURI(doc.pdfPath)} target="_blank" rel="noopener noreferrer" style={{ color:"#fca5a5", fontSize:11, textDecoration:"none", background:"rgba(239,68,68,0.1)", borderRadius:6, padding:"3px 8px", border:"1px solid rgba(239,68,68,0.3)", marginRight:4 }}>&#128196; PDF</a>) : null}
                  {doc.fileData ? (<a href={doc.fileData} download={doc.fileName||doc.id} style={{ color:"#60a5fa", fontSize:11, textDecoration:"none", background:"rgba(96,165,250,0.1)", borderRadius:6, padding:"3px 8px", border:"1px solid rgba(96,165,250,0.3)" }}>&#8595; {doc.fileType||"下載"}</a>) : null}
                  {!doc.pdfPath && !doc.fileData && <span style={{ color:"#374151", fontSize:11 }}>無檔案</span>}
                </td>
                <td style={{ padding:"10px 12px" }}><button onClick={() => setModal(doc)} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:6, color:"#94a3b8", cursor:"pointer", padding:"4px 10px", fontSize:11 }}>詳情</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail modal */}
      {modal && (
        <Modal title={`文件詳情：${modal.id}`} onClose={() => setModal(null)}>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16 }}>
            {[["文件編號",modal.id],["文件名稱",modal.name],["類別",modal.type],["版本",`v${modal.version}`],["制定部門",modal.department],["制定日期",formatDate(modal.createdDate)],["制定者",modal.author],["保存年限",`${modal.retentionYears} 年`],["保存到期日",formatDate(modal.expiryStr)],["距到期",`${modal.daysToExpiry} 天`]].map(([k,v]) => (
              <div key={k}><div style={{ fontSize:11, color:"#64748b", marginBottom:4 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:14 }}>{v}</div></div>
            ))}
          </div>
          {modal.pdfPath && (
            <div style={{ background:"rgba(239,68,68,0.07)", border:"1px solid rgba(239,68,68,0.25)", borderRadius:10, padding:14, display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:8 }}>
              <div>
                <div style={{ fontSize:12, color:"#fca5a5", fontWeight:700, marginBottom:3 }}>&#128196; PDF 原始檔案</div>
                <div style={{ fontSize:11, color:"#64748b" }}>{modal.pdfPath.split("/").pop()}</div>
              </div>
              <a href={encodeURI(modal.pdfPath)} target="_blank" rel="noopener noreferrer" style={{ background:"linear-gradient(135deg,#dc2626,#ef4444)", color:"#fff", padding:"8px 18px", borderRadius:8, fontSize:13, fontWeight:700, textDecoration:"none", whiteSpace:"nowrap" }}>&#128065; 開啟 PDF</a>
            </div>
          )}
          {modal.fileName && (
            <div style={{ background:"rgba(96,165,250,0.07)", border:"1px solid rgba(96,165,250,0.2)", borderRadius:10, padding:14, display:"flex", alignItems:"center", justifyContent:"space-between" }}>
              <div>
                <div style={{ fontSize:13, color:"#93c5fd", fontWeight:700 }}>{modal.fileName}</div>
                <div style={{ fontSize:11, color:"#64748b", marginTop:4 }}>{modal.fileType} • {modal.fileSize}</div>
              </div>
              {modal.fileData && <a href={modal.fileData} download={modal.fileName} style={{ background:"linear-gradient(135deg,#7c3aed,#4f46e5)", color:"#fff", padding:"8px 18px", borderRadius:8, fontSize:13, fontWeight:700, textDecoration:"none" }}>&#8595; 下載檔案</a>}
            </div>
          )}
        </Modal>
      )}

      {/* ── SINGLE ADD MODAL ─────────────────────────────────────────────────── */}
      {mode === "single" && (
        <Modal title="新增文件" onClose={closeModal}>
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            <div>
              <div style={{ fontSize:12, color:"#64748b", marginBottom:6, fontWeight:600 }}>上傳文件（可自動讀取 Word / PDF Metadata）</div>
              <label style={{ display:"flex", alignItems:"center", gap:12, background:"rgba(255,255,255,0.03)", border:"2px dashed rgba(124,58,237,0.4)", borderRadius:12, padding:"14px 18px", cursor:"pointer" }}
                onMouseEnter={e=>e.currentTarget.style.borderColor="rgba(124,58,237,0.8)"}
                onMouseLeave={e=>e.currentTarget.style.borderColor="rgba(124,58,237,0.4)"}>
                <input type="file" accept=".pdf,.docx,.xlsx,.pptx,.doc,.txt" onChange={handleSingleFileUpload} style={{ display:"none" }} />
                <span style={{ fontSize:28 }}>&#128196;</span>
                <div>
                  {newDoc.fileName
                    ? <><div style={{ color:"#a78bfa", fontWeight:700 }}>{newDoc.fileName}</div><div style={{ color:"#64748b", fontSize:12 }}>{newDoc.fileType} • {newDoc.fileSize}</div></>
                    : <><div style={{ color:"#94a3b8", fontWeight:600 }}>點擊選擇單一檔案</div><div style={{ color:"#475569", fontSize:12, marginTop:3 }}>PDF、DOCX、XLSX…</div></>
                  }
                </div>
              </label>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
              {[["文件編號 *","id","text"],["版本 *","version","text"],["制定部門 *","department","text"],["制定者","author","text"]].map(([label,field,type]) => (
                <div key={field}>
                  <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div>
                  <input type={type} value={newDoc[field]} onChange={e=>setNewDoc({...newDoc,[field]:e.target.value})} style={inputStyle} placeholder={field==="id"?"MP-XX":""} />
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>文件名稱 *</div>
              <input type="text" value={newDoc.name} onChange={e=>setNewDoc({...newDoc,name:e.target.value})} style={inputStyle} />
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12 }}>
              <div>
                <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>制定日期 *</div>
                <input type="date" value={newDoc.createdDate} onChange={e=>setNewDoc({...newDoc,createdDate:e.target.value})} style={inputStyle} />
              </div>
              <div>
                <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>保存年限（年）</div>
                <input type="number" value={newDoc.retentionYears} onChange={e=>setNewDoc({...newDoc,retentionYears:e.target.value})} style={inputStyle} min="1" max="99" />
              </div>
              <div>
                <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>類別</div>
                <select value={newDoc.type} onChange={e=>setNewDoc({...newDoc,type:e.target.value})} style={inputStyle}>
                  <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>
                </select>
              </div>
            </div>
            {err && <div style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, padding:"10px 14px", color:"#fca5a5", fontSize:13 }}>{err}</div>}
            <button onClick={handleSingleAdd} style={{ background:"linear-gradient(135deg,#7c3aed,#4f46e5)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"13px 24px", fontSize:15, fontWeight:700 }}>＋ 確認新增文件</button>
          </div>
        </Modal>
      )}

      {/* ── BULK UPLOAD MODAL ────────────────────────────────────────────────── */}
      {mode === "bulk" && (
        <Modal title={`批量上傳文件（已選 ${bulkItems.length} 筆）`} onClose={closeModal}>
          <div style={{ display:"flex", flexDirection:"column", gap:16 }}>

            {/* Drop zone */}
            <div
              style={dropZoneStyle(dragOver)}
              onDragOver={e=>{ e.preventDefault(); setDragOver(true); }}
              onDragLeave={()=>setDragOver(false)}
              onDrop={e=>{ e.preventDefault(); setDragOver(false); handleBulkFiles(e.dataTransfer.files); }}
            >
              <span style={{ fontSize:40 }}>&#128229;</span>
              <div style={{ color:"#a78bfa", fontWeight:700, fontSize:15 }}>拖曳多個檔案到此處</div>
              <div style={{ color:"#64748b", fontSize:12 }}>支援 PDF、DOCX、XLSX、PPTX、TXT，自動解析 Metadata</div>
              <label style={{ marginTop:6, background:"rgba(124,58,237,0.15)", border:"1px solid rgba(124,58,237,0.5)", borderRadius:8, color:"#a78bfa", cursor:"pointer", padding:"8px 20px", fontSize:13, fontWeight:700 }}>
                <input type="file" multiple accept=".pdf,.docx,.xlsx,.pptx,.doc,.txt" onChange={e=>handleBulkFiles(e.target.files)} style={{ display:"none" }} />
                或點擊選擇檔案
              </label>
            </div>

            {/* Item list */}
            {bulkItems.length > 0 && (
              <div style={{ display:"flex", flexDirection:"column", gap:10, maxHeight:420, overflowY:"auto", paddingRight:4 }}>
                {/* Header row */}
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 0.8fr 0.7fr 0.7fr 28px", gap:6, fontSize:11, color:"#64748b", fontWeight:600, padding:"0 2px" }}>
                  <span>文件編號 *</span><span>名稱 *</span><span>部門 *</span><span>日期 *</span><span>版本 / 類別</span><span></span>
                </div>
                {bulkItems.map((item, idx) => (
                  <div key={idx} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)", borderRadius:10, padding:"10px 12px" }}>
                    {/* File info row */}
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                        <span style={{ fontSize:16 }}>&#128196;</span>
                        <span style={{ fontSize:12, color:"#a78bfa", fontWeight:600 }}>{item.fileName}</span>
                        <span style={{ fontSize:11, color:"#475569" }}>{item.fileSize} • {item.fileType}</span>
                      </div>
                      <button onClick={()=>removeBulkItem(idx)} style={{ background:"rgba(239,68,68,0.15)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:6, color:"#fca5a5", cursor:"pointer", padding:"2px 8px", fontSize:12 }}>✕</button>
                    </div>
                    {/* Editable fields */}
                    <div style={{ display:"grid", gridTemplateColumns:"0.8fr 1.5fr 0.9fr 0.85fr 0.6fr 0.6fr", gap:6 }}>
                      <input value={item.id} onChange={e=>updateBulkItem(idx,"id",e.target.value)} placeholder="編號 *" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <input value={item.name} onChange={e=>updateBulkItem(idx,"name",e.target.value)} placeholder="名稱 *" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <input value={item.department} onChange={e=>updateBulkItem(idx,"department",e.target.value)} placeholder="部門 *" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <input type="date" value={item.createdDate} onChange={e=>updateBulkItem(idx,"createdDate",e.target.value)} style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <input value={item.version} onChange={e=>updateBulkItem(idx,"version",e.target.value)} placeholder="版本" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <select value={item.type} onChange={e=>updateBulkItem(idx,"type",e.target.value)} style={{ ...inputStyle, fontSize:11, padding:"6px 4px" }}>
                        <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>
                      </select>
                    </div>
                    {/* Author & retention (collapsed row) */}
                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6, marginTop:6 }}>
                      <input value={item.author} onChange={e=>updateBulkItem(idx,"author",e.target.value)} placeholder="制定者" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} />
                      <input type="number" value={item.retentionYears} onChange={e=>updateBulkItem(idx,"retentionYears",e.target.value)} placeholder="保存年限" style={{ ...inputStyle, fontSize:12, padding:"6px 8px" }} min="1" max="99" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {bulkItems.length === 0 && (
              <div style={{ textAlign:"center", color:"#475569", fontSize:13, padding:"10px 0" }}>尚未選擇任何檔案</div>
            )}

            {err && <div style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, padding:"10px 14px", color:"#fca5a5", fontSize:13 }}>{err}</div>}
            {bulkDone && <div style={{ background:"rgba(34,197,94,0.1)", border:"1px solid rgba(34,197,94,0.3)", borderRadius:8, padding:"10px 14px", color:"#86efac", fontSize:13 }}>✓ 已成功匯入 {bulkItems.length} 筆文件！</div>}

            <div style={{ display:"flex", gap:10 }}>
              <button onClick={closeModal} style={{ flex:1, background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:10, color:"#94a3b8", cursor:"pointer", padding:"12px 0", fontSize:14, fontWeight:600 }}>取消</button>
              <button onClick={confirmBulkUpload} disabled={bulkItems.length===0} style={{ flex:2, background: bulkItems.length===0?"rgba(124,58,237,0.3)":"linear-gradient(135deg,#0891b2,#06b6d4)", border:"none", borderRadius:10, color:"#fff", cursor: bulkItems.length===0?"not-allowed":"pointer", padding:"12px 0", fontSize:15, fontWeight:700 }}>
                &#128229; 確認匯入全部 {bulkItems.length} 筆文件
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
