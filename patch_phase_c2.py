"""
patch_phase_c2.py  – 為剩餘 Tab 加入全欄位編輯 Modal + 刪除功能
  · EquipmentTab
  · SupplierTab
  · NonConformanceTab
  · AuditPlanTab
  · TrainingTab
"""
SRC = r"C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx"

with open(SRC, encoding="utf-8-sig") as f:
    src = f.read()

def patch(text, old, new, name):
    if old in text:
        print(f"  [OK] {name}")
        return text.replace(old, new, 1)
    print(f"  [SKIP] not found: {name}")
    return text

# ─────────────────────────────────────────────────────────────────────────────
# EquipmentTab: add full edit modal + delete + add new
# ─────────────────────────────────────────────────────────────────────────────
EQ_OLD = '''// ─── EQUIPMENT TAB ────────────────────────────────────────────────────────────
function EquipmentTab({ equipment, setEquipment }) {
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({});
  const enriched = equipment.map(eq => {
    const nextDate = addDays(eq.lastMaintenance, eq.intervalDays);
    const days = daysUntil(nextDate);
    return { ...eq, nextDate, days };
  }).sort((a,b) => a.days-b.days);
  function handleUpdate() {
    setEquipment(prev => prev.map(e => e.id===modal.id ? { ...e, lastMaintenance: form.date } : e));
    setModal(null);
  }'''
EQ_NEW = '''// ─── EQUIPMENT TAB ────────────────────────────────────────────────────────────
function EquipmentTab({ equipment, setEquipment }) {
  const [modal, setModal]       = useState(null);   // null | eq-object | "add"
  const [form, setForm]         = useState({});
  const [editTarget, setEditTarget] = useState(null);
  const emptyEq = { id:"", name:"", location:"", lastMaintenance:"", intervalDays:90, nextItems:[] };
  const enriched = equipment.map(eq => {
    const nextDate = addDays(eq.lastMaintenance, eq.intervalDays);
    const days = daysUntil(nextDate);
    return { ...eq, nextDate, days };
  }).sort((a,b) => a.days-b.days);
  function handleUpdate() {
    setEquipment(prev => prev.map(e => e.id===modal.id ? { ...e, lastMaintenance: form.date } : e));
    setModal(null);
  }
  function saveEdit() {
    const items = typeof editTarget.nextItems === "string"
      ? editTarget.nextItems.split(/[,，\n]/).map(s=>s.trim()).filter(Boolean)
      : (editTarget.nextItems||[]);
    const updated = { ...editTarget, intervalDays:parseInt(editTarget.intervalDays)||90, nextItems:items };
    if (modal === "add") {
      setEquipment(prev => [...prev, updated]);
    } else {
      setEquipment(prev => prev.map(e => e.id===editTarget.id ? updated : e));
    }
    setEditTarget(null); setModal(null);
  }
  function deleteEq(id) {
    if (!confirm("確定刪除此設備？")) return;
    setEquipment(prev => prev.filter(e => e.id !== id));
  }'''

EQ_BTN_OLD = '''              <button onClick={() => { setModal(eq); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>記錄保養</button>'''
EQ_BTN_NEW = '''              <button onClick={() => { setModal(eq); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>記錄保養</button>
              <button onClick={() => { setEditTarget({...eq, nextItems:(eq.nextItems||[]).join(",")}); setModal("edit"); }} style={{ background:"rgba(96,165,250,0.1)", border:"1px solid rgba(96,165,250,0.3)", borderRadius:8, color:"#60a5fa", cursor:"pointer", padding:"6px 10px", fontSize:12 }}>✏</button>
              <button onClick={() => deleteEq(eq.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, color:"#f87171", cursor:"pointer", padding:"6px 10px", fontSize:12 }}>🗑</button>'''

EQ_MODAL_OLD = '''      {modal && (<Modal title={`記錄保養完成：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>保養完成日期</div><input type="date" value={form.date} onChange={e => setForm({...form,date:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(251,146,60,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#fb923c", fontWeight: 600, marginBottom: 8 }}>本次保養項目：</div>{modal.nextItems.map((item,i) => (<div key={i} style={{ color: "#fed7aa", fontSize: 13, marginBottom: 4 }}>☑ {item}</div>))}</div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #ea580c, #f97316)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認保養完成</button></div></Modal>)}
    </div>
  );
}'''
EQ_MODAL_NEW = '''      {modal && modal !== "edit" && modal !== "add" && (<Modal title={`記錄保養完成：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>保養完成日期</div><input type="date" value={form.date} onChange={e => setForm({...form,date:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(251,146,60,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#fb923c", fontWeight: 600, marginBottom: 8 }}>本次保養項目：</div>{(modal.nextItems||[]).map((item,i) => (<div key={i} style={{ color: "#fed7aa", fontSize: 13, marginBottom: 4 }}>☑ {item}</div>))}</div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #ea580c, #f97316)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認保養完成</button></div></Modal>)}
      {(modal === "edit" || modal === "add") && editTarget && (
        <Modal title={modal==="add"?"新增設備":`編輯設備：${editTarget.name}`} onClose={()=>{ setEditTarget(null); setModal(null); }}>
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {[["設備編號","id","text"],["設備名稱","name","text"],["位置","location","text"],["最近保養日","lastMaintenance","date"],["保養間隔(天)","intervalDays","number"]].map(([label,field,type])=>(
              <div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={editTarget[field]??""} onChange={e=>setEditTarget({...editTarget,[field]:e.target.value})} style={inputStyle} /></div>
            ))}
            <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>保養項目（逗號或換行分隔）</div><textarea value={typeof editTarget.nextItems==="string"?editTarget.nextItems:(editTarget.nextItems||[]).join(",")} onChange={e=>setEditTarget({...editTarget,nextItems:e.target.value})} rows={3} style={{ ...inputStyle, resize:"vertical" }} /></div>
            <div style={{ display:"flex", gap:10, marginTop:8 }}>
              <button onClick={saveEdit} style={{ flex:1, background:"linear-gradient(135deg,#ea580c,#f97316)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px", fontSize:14, fontWeight:700 }}>✓ 儲存</button>
              {modal==="edit" && <button onClick={()=>{ deleteEq(editTarget.id); setEditTarget(null); setModal(null); }} style={{ background:"rgba(239,68,68,0.15)", border:"1px solid rgba(239,68,68,0.4)", borderRadius:10, color:"#f87171", cursor:"pointer", padding:"12px 18px", fontSize:14, fontWeight:700 }}>🗑 刪除</button>}
            </div>
          </div>
        </Modal>
      )}
      <div style={{ display:"flex", justifyContent:"flex-end", marginTop:16 }}>
        <button onClick={()=>{ setEditTarget({...emptyEq}); setModal("add"); }} style={{ background:"linear-gradient(135deg,#ea580c,#f97316)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>＋ 新增設備</button>
      </div>
    </div>
  );
}'''

# ─────────────────────────────────────────────────────────────────────────────
# SupplierTab: add full edit modal + delete + add new
# ─────────────────────────────────────────────────────────────────────────────
SUP_OLD = '''// ─── SUPPLIER TAB (MP-10) ────────────────────────────────────────────────────
function SupplierTab({ suppliers, setSuppliers }) {
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({});
  const enriched = suppliers.map(s => {
    const nextEvalDate = addDays(s.lastEvalDate, s.evalIntervalDays);
    const days = daysUntil(nextEvalDate);
    return { ...s, nextEvalDate, days };
  }).sort((a,b) => a.days-b.days);
  function handleUpdate() {
    setSuppliers(prev => prev.map(s => s.id===modal.id ? { ...s, lastEvalDate: form.date, evalScore: parseInt(form.score), evalResult: parseInt(form.score)>=90?"優良":parseInt(form.score)>=80?"合格":parseInt(form.score)>=70?"條件合格":"不合格" } : s));
    setModal(null);
  }'''
SUP_NEW = '''// ─── SUPPLIER TAB (MP-10) ────────────────────────────────────────────────────
function SupplierTab({ suppliers, setSuppliers }) {
  const [modal, setModal]       = useState(null);
  const [form, setForm]         = useState({});
  const [editTarget, setEditTarget] = useState(null);
  const emptySupplier = { id:"", name:"", category:"", contact:"", lastEvalDate:"", evalIntervalDays:365, evalScore:80, evalResult:"合格", issues:[] };
  const enriched = suppliers.map(s => {
    const nextEvalDate = addDays(s.lastEvalDate, s.evalIntervalDays);
    const days = daysUntil(nextEvalDate);
    return { ...s, nextEvalDate, days };
  }).sort((a,b) => a.days-b.days);
  function handleUpdate() {
    const sc = parseInt(form.score);
    setSuppliers(prev => prev.map(s => s.id===modal.id ? { ...s, lastEvalDate:form.date, evalScore:sc, evalResult:sc>=90?"優良":sc>=80?"合格":sc>=70?"條件合格":"不合格" } : s));
    setModal(null);
  }
  function saveEdit() {
    const issues = typeof editTarget.issues==="string"
      ? editTarget.issues.split(/[,，\n]/).map(s=>s.trim()).filter(Boolean)
      : (editTarget.issues||[]);
    const sc = parseInt(editTarget.evalScore)||80;
    const updated = { ...editTarget, evalIntervalDays:parseInt(editTarget.evalIntervalDays)||365, evalScore:sc, evalResult:sc>=90?"優良":sc>=80?"合格":sc>=70?"條件合格":"不合格", issues };
    if (modal==="add") { setSuppliers(prev=>[...prev,updated]); }
    else { setSuppliers(prev=>prev.map(s=>s.id===editTarget.id?updated:s)); }
    setEditTarget(null); setModal(null);
  }
  function deleteSupplier(id) {
    if (!confirm("確定刪除此供應商？")) return;
    setSuppliers(prev=>prev.filter(s=>s.id!==id));
  }'''

SUP_BTN_OLD = '''              <button onClick={() => { setModal(s); setForm({ date: new Date().toISOString().split("T")[0], score: s.evalScore }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>更新評鑑</button>'''
SUP_BTN_NEW = '''              <button onClick={() => { setModal(s); setForm({ date: new Date().toISOString().split("T")[0], score: s.evalScore }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>更新評鑑</button>
              <button onClick={() => { setEditTarget({...s, issues:(s.issues||[]).join(",")}); setModal("edit"); }} style={{ background:"rgba(96,165,250,0.1)", border:"1px solid rgba(96,165,250,0.3)", borderRadius:8, color:"#60a5fa", cursor:"pointer", padding:"6px 10px", fontSize:12 }}>✏</button>
              <button onClick={() => deleteSupplier(s.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, color:"#f87171", cursor:"pointer", padding:"6px 10px", fontSize:12 }}>🗑</button>'''

SUP_MODAL_OLD = '''      {modal && (<Modal title={`更新評鑑：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑日期</div><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})} style={inputStyle} /></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑總分 (0-100)</div><input type="number" min="0" max="100" value={form.score} onChange={e=>setForm({...form,score:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(6,182,212,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#22d3ee", fontWeight: 600 }}>評定等級：{parseInt(form.score)>=90?"優良":parseInt(form.score)>=80?"合格":parseInt(form.score)>=70?"條件合格":"不合格"}</div><div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>90+優良 / 80-89合格 / 70-79條件合格 / 69以下不合格</div></div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #0891b2, #06b6d4)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認更新評鑑</button></div></Modal>)}
    </div>
  );
}'''
SUP_MODAL_NEW = '''      {modal && modal !== "edit" && modal !== "add" && (<Modal title={`更新評鑑：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑日期</div><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})} style={inputStyle} /></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑總分 (0-100)</div><input type="number" min="0" max="100" value={form.score} onChange={e=>setForm({...form,score:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(6,182,212,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#22d3ee", fontWeight: 600 }}>評定等級：{parseInt(form.score)>=90?"優良":parseInt(form.score)>=80?"合格":parseInt(form.score)>=70?"條件合格":"不合格"}</div><div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>90+優良 / 80-89合格 / 70-79條件合格 / 69以下不合格</div></div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #0891b2, #06b6d4)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認更新評鑑</button></div></Modal>)}
      {(modal==="edit"||modal==="add") && editTarget && (
        <Modal title={modal==="add"?"新增供應商":`編輯供應商：${editTarget.name}`} onClose={()=>{ setEditTarget(null); setModal(null); }}>
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {[["供應商編號","id","text"],["供應商名稱","name","text"],["類別","category","text"],["聯絡人","contact","text"],["最近評鑑日","lastEvalDate","date"],["評鑑間隔(天)","evalIntervalDays","number"],["評鑑分數(0-100)","evalScore","number"]].map(([label,field,type])=>(
              <div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={editTarget[field]??""} onChange={e=>setEditTarget({...editTarget,[field]:e.target.value})} style={inputStyle} /></div>
            ))}
            <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>問題項目（逗號分隔）</div><input value={typeof editTarget.issues==="string"?editTarget.issues:(editTarget.issues||[]).join(",")} onChange={e=>setEditTarget({...editTarget,issues:e.target.value})} style={inputStyle} /></div>
            <div style={{ display:"flex", gap:10, marginTop:8 }}>
              <button onClick={saveEdit} style={{ flex:1, background:"linear-gradient(135deg,#0891b2,#06b6d4)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px", fontSize:14, fontWeight:700 }}>✓ 儲存</button>
              {modal==="edit" && <button onClick={()=>{ deleteSupplier(editTarget.id); setEditTarget(null); setModal(null); }} style={{ background:"rgba(239,68,68,0.15)", border:"1px solid rgba(239,68,68,0.4)", borderRadius:10, color:"#f87171", cursor:"pointer", padding:"12px 18px", fontSize:14, fontWeight:700 }}>🗑 刪除</button>}
            </div>
          </div>
        </Modal>
      )}
      <div style={{ display:"flex", justifyContent:"flex-end", marginTop:16 }}>
        <button onClick={()=>{ setEditTarget({...emptySupplier}); setModal("add"); }} style={{ background:"linear-gradient(135deg,#0891b2,#06b6d4)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>＋ 新增供應商</button>
      </div>
    </div>
  );
}'''

# ─────────────────────────────────────────────────────────────────────────────
# NonConformanceTab: add edit + delete button
# ─────────────────────────────────────────────────────────────────────────────
NC_DETAIL_BTN_OLD = '''              <button onClick={() => setModal(nc)} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>詳情</button>'''
NC_DETAIL_BTN_NEW = '''              <button onClick={() => setModal(nc)} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>詳情</button>
              <button onClick={() => { if(confirm("確定刪除此不符合報告？")) setNcs(prev=>prev.filter(n=>n.id!==nc.id)); }} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, color:"#f87171", cursor:"pointer", padding:"6px 10px", fontSize:12 }}>🗑</button>'''

# In the detail modal, allow editing key fields
NC_MODAL_OLD = '''      {modal && (<Modal title={`不符合詳情：${modal.id}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 14 }}>{[["發現日期",formatDate(modal.date)],["發現部門",modal.dept],["不符合類型",modal.type],["嚴重度",modal.severity],["問題描述",modal.description],["根本原因",modal.rootCause],["矯正措施",modal.correctiveAction],["資任人",modal.responsible],["到期日期",formatDate(modal.dueDate)],["狀態",modal.status],["關閉日期",formatDate(modal.closeDate)],["有效性驗證",modal.effectiveness||"尚未驗證"]].map(([k,v]) => (<div key={k} style={{ display:"flex", gap:12 }}><div style={{ fontSize:12, color:"#64748b", minWidth:90 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:13 }}>{v}</div></div>))}{modal.status!=="已關閉" && (<button onClick={() => closeNc(modal)} style={{ background:"linear-gradient(135deg,#059669,#10b981)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700, marginTop:8 }}>✓ 標記為已關閉</button>)}</div></Modal>)}'''
NC_MODAL_NEW = '''      {modal && (<Modal title={`不符合詳情：${modal.id}`} onClose={() => setModal(null)}>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {[["發現日期","date","date"],["發現部門","dept","text"],["問題描述","description","text"],["根本原因","rootCause","text"],["矯正措施","correctiveAction","text"],["責任人","responsible","text"],["到期日期","dueDate","date"]].map(([label,field,type])=>(
            <div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div>
              <input type={type} value={modal[field]||""} onChange={e=>setModal({...modal,[field]:e.target.value})} style={inputStyle} />
            </div>
          ))}
          <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>不符合類型</div><select value={modal.type||""} onChange={e=>setModal({...modal,type:e.target.value})} style={inputStyle}><option>製程異常</option><option>量測異常</option><option>來料不合格</option><option>文件不符</option><option>客戶投訴</option></select></div>
          <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>嚴重度</div><select value={modal.severity||""} onChange={e=>setModal({...modal,severity:e.target.value})} style={inputStyle}><option>輕微</option><option>重大</option></select></div>
          <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>狀態</div><select value={modal.status||""} onChange={e=>setModal({...modal,status:e.target.value})} style={inputStyle}><option>待處理</option><option>處理中</option><option>已關閉</option></select></div>
          <div style={{ display:"flex", gap:10, marginTop:8 }}>
            <button onClick={()=>{ setNcs(prev=>prev.map(n=>n.id===modal.id?modal:n)); setModal(null); }} style={{ flex:1, background:"linear-gradient(135deg,#dc2626,#ef4444)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px", fontSize:14, fontWeight:700 }}>✓ 儲存變更</button>
            {modal.status!=="已關閉" && <button onClick={()=>closeNc(modal)} style={{ background:"linear-gradient(135deg,#059669,#10b981)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 18px", fontSize:13, fontWeight:700 }}>✓ 關閉</button>}
          </div>
        </div>
      </Modal>)}'''

# ─────────────────────────────────────────────────────────────────────────────
# AuditPlanTab: add new plan + delete
# ─────────────────────────────────────────────────────────────────────────────
AUDIT_ADD_OLD = '''  function markComplete(id) {
    setAuditPlans(prev => prev.map(a => a.id===id ? {...a, status:"已完成", actualDate: new Date().toISOString().split("T")[0]} : a));
    setModal(null);
  }'''
AUDIT_ADD_NEW = '''  const [showAdd, setShowAdd] = useState(false);
  const [newPlan, setNewPlan] = useState({ year:new Date().getFullYear(), period:"上半年", scheduledDate:"", dept:"", scope:"", auditor:"", auditee:"", status:"計畫中", findings:0, ncCount:0 });
  function markComplete(id) {
    setAuditPlans(prev => prev.map(a => a.id===id ? {...a, status:"已完成", actualDate: new Date().toISOString().split("T")[0]} : a));
    setModal(null);
  }
  function addPlan() {
    const id = "IA-" + newPlan.year + "-" + String(auditPlans.filter(a=>a.year===parseInt(newPlan.year)).length+1).padStart(2,"0");
    setAuditPlans(prev => [...prev, { ...newPlan, id, year:parseInt(newPlan.year), findings:0, ncCount:0 }]);
    setShowAdd(false);
    setNewPlan({ year:new Date().getFullYear(), period:"上半年", scheduledDate:"", dept:"", scope:"", auditor:"", auditee:"", status:"計畫中", findings:0, ncCount:0 });
  }
  function deleteAudit(id) {
    if (!confirm("確定刪除此稽核計畫？")) return;
    setAuditPlans(prev => prev.filter(a => a.id !== id));
  }'''

AUDIT_BTN_OLD = '''                <td style={{ padding:"10px 12px" }}><button onClick={()=>setModal(a)} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:6, color:"#94a3b8", cursor:"pointer", padding:"4px 10px", fontSize:11 }}>詳情</button></td>'''
AUDIT_BTN_NEW = '''                <td style={{ padding:"10px 12px", whiteSpace:"nowrap" }}>
                  <button onClick={()=>setModal(a)} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:6, color:"#94a3b8", cursor:"pointer", padding:"4px 10px", fontSize:11, marginRight:4 }}>詳情</button>
                  <button onClick={()=>deleteAudit(a.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:6, color:"#f87171", cursor:"pointer", padding:"4px 8px", fontSize:11 }}>🗑</button>
                </td>'''

AUDIT_MODAL_CLOSE = '''      {modal && (<Modal title={`稽核詳情：${modal.id}`} onClose={() => setModal(null)}><div style={{ display:"flex", flexDirection:"column", gap:14 }}>{[["稽核編號",modal.id],["稽核部門",modal.dept],["預定日期",formatDate(modal.scheduledDate)],["實際日期",formatDate(modal.actualDate)],["稽核員",modal.auditor],["稽核對象",modal.auditee],["稽核範圍",modal.scope],["狀態",modal.status],["發現項數",modal.findings+"項"],["不符合數",modal.ncCount+"項"]].map(([k,v]) => (<div key={k} style={{ display:"flex", gap:12 }}><div style={{ fontSize:12, color:"#64748b", minWidth:90 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:13 }}>{v}</div></div>))}{modal.status!=="已完成" && (<button onClick={()=>markComplete(modal.id)} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700, marginTop:8 }}>✓ 標記稽核已完成</button>)}</div></Modal>)}
    </div>
  );
}'''
AUDIT_MODAL_NEW = '''      {modal && (<Modal title={`稽核詳情：${modal.id}`} onClose={() => setModal(null)}><div style={{ display:"flex", flexDirection:"column", gap:14 }}>{[["稽核編號",modal.id],["稽核部門",modal.dept],["預定日期",formatDate(modal.scheduledDate)],["實際日期",formatDate(modal.actualDate)],["稽核員",modal.auditor],["稽核對象",modal.auditee],["稽核範圍",modal.scope],["狀態",modal.status],["發現項數",modal.findings+"項"],["不符合數",modal.ncCount+"項"]].map(([k,v]) => (<div key={k} style={{ display:"flex", gap:12 }}><div style={{ fontSize:12, color:"#64748b", minWidth:90 }}>{k}</div><div style={{ color:"#e2e8f0", fontWeight:600, fontSize:13 }}>{v}</div></div>))}{modal.status!=="已完成" && (<button onClick={()=>markComplete(modal.id)} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700, marginTop:8 }}>✓ 標記稽核已完成</button>)}</div></Modal>)}
      {showAdd && (<Modal title="新增稽核計畫" onClose={()=>setShowAdd(false)}>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {[["年度","year","number"],["預定日期","scheduledDate","date"],["稽核部門","dept","text"],["稽核範圍","scope","text"],["稽核員","auditor","text"],["被稽核員","auditee","text"]].map(([label,field,type])=>(
            <div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={newPlan[field]||""} onChange={e=>setNewPlan({...newPlan,[field]:e.target.value})} style={inputStyle} /></div>
          ))}
          <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>期間</div><select value={newPlan.period} onChange={e=>setNewPlan({...newPlan,period:e.target.value})} style={inputStyle}><option>上半年</option><option>下半年</option></select></div>
          <button onClick={addPlan} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8 }}>＋ 新增稽核計畫</button>
        </div>
      </Modal>)}
      <div style={{ display:"flex", justifyContent:"flex-end", marginTop:16 }}>
        <button onClick={()=>setShowAdd(true)} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>＋ 新增稽核計畫</button>
      </div>
    </div>
  );
}'''

# ─────────────────────────────────────────────────────────────────────────────
# TrainingTab: add delete employee + delete training record
# ─────────────────────────────────────────────────────────────────────────────
TRAIN_SELECTED_OLD = '''                  <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #059669, #10b981)", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", padding: "7px 14px", fontSize: 12, fontWeight: 700 }}>＋ 新增訓練</button>'''
TRAIN_SELECTED_NEW = '''                  <div style={{ display:"flex", gap:8 }}>
                    <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #059669, #10b981)", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", padding: "7px 14px", fontSize: 12, fontWeight: 700 }}>＋ 新增訓練</button>
                    <button onClick={()=>{ if(confirm(`確定刪除員工 ${selected.name} 的所有資料？`)) { setTraining(prev=>prev.filter(e=>e.id!==selected.id)); setSelected(null); } }} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, color:"#f87171", cursor:"pointer", padding:"7px 12px", fontSize:12 }}>🗑 刪除員工</button>
                  </div>'''

# Apply all patches
src = patch(src, EQ_OLD,               EQ_NEW,               "EquipmentTab header")
src = patch(src, EQ_BTN_OLD,           EQ_BTN_NEW,           "EquipmentTab row buttons")
src = patch(src, EQ_MODAL_OLD,         EQ_MODAL_NEW,         "EquipmentTab modal")
src = patch(src, SUP_OLD,              SUP_NEW,              "SupplierTab header")
src = patch(src, SUP_BTN_OLD,          SUP_BTN_NEW,          "SupplierTab row buttons")
src = patch(src, SUP_MODAL_OLD,        SUP_MODAL_NEW,        "SupplierTab modal")
src = patch(src, NC_DETAIL_BTN_OLD,    NC_DETAIL_BTN_NEW,    "NonConformanceTab delete btn")
src = patch(src, NC_MODAL_OLD,         NC_MODAL_NEW,         "NonConformanceTab modal (edit)")
src = patch(src, AUDIT_ADD_OLD,        AUDIT_ADD_NEW,        "AuditPlanTab add/delete functions")
src = patch(src, AUDIT_BTN_OLD,        AUDIT_BTN_NEW,        "AuditPlanTab row buttons")
src = patch(src, AUDIT_MODAL_CLOSE,    AUDIT_MODAL_NEW,      "AuditPlanTab add modal")
src = patch(src, TRAIN_SELECTED_OLD,   TRAIN_SELECTED_NEW,   "TrainingTab delete employee btn")

with open(SRC, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[DONE] Phase C2 patches applied. File size: {len(src)} chars")
