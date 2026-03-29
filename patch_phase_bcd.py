"""
patch_phase_bcd.py
一次性在 audit-dashboard.jsx 加入：
  B: ProductionTab (XLSX 匯入 + 下載)
  C: LocalStorage 持久化 + 全欄位編輯 Modal
  D: NotificationTab (Google Calendar / Email / Notion)
"""
import re, sys

SRC = r"C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx"

with open(SRC, encoding="utf-8-sig") as f:
    src = f.read()

# ═══════════════════════════════════════════════════════════════
# STEP 1: Replace EnvironmentTab with XLSX-import + edit/delete
# ═══════════════════════════════════════════════════════════════
ENV_OLD = '''// ─── ENVIRONMENT TAB (MP-06) ─────────────────────────────────────────────────
function EnvironmentTab({ envRecords, setEnvRecords }) {'''
ENV_NEW = r'''// ─── ENVIRONMENT TAB (MP-06) ─────────────────────────────────────────────────
function EnvironmentTab({ envRecords, setEnvRecords }) {
  const [showAdd, setShowAdd] = useState(false);
  const [editTarget, setEditTarget] = useState(null);
  const [newRec, setNewRec] = useState({ date:"", location:"潔淨室A區", particles05:0, particles1:0, particles5:0, temp:22.0, humidity:45.0, pressure:12.5, operator:"", result:"合格" });
  const sorted = [...envRecords].sort((a,b) => new Date(b.date)-new Date(a.date));
  const resultColor = r => r==="合格"?"#22c55e":r==="警告"?"#eab308":"#ef4444";
  function autoResult(rec) {
    const p05=parseInt(rec.particles05), p5=parseInt(rec.particles5), temp=parseFloat(rec.temp), hum=parseFloat(rec.humidity);
    if(p05>1000||p5>35||temp>23||temp<21||hum>50||hum<40) return "不合格";
    if(p05>800||p5>20||temp>22.5||hum>48) return "警告";
    return "合格";
  }
  function addRec() {
    const id = "ENV-" + String(envRecords.length+1).padStart(3,"0");
    const result = autoResult(newRec);
    setEnvRecords(prev => [...prev, { ...newRec, id, result, particles05:parseInt(newRec.particles05), particles1:parseInt(newRec.particles1), particles5:parseInt(newRec.particles5), temp:parseFloat(newRec.temp), humidity:parseFloat(newRec.humidity), pressure:parseFloat(newRec.pressure) }]);
    setShowAdd(false);
    setNewRec({ date:"", location:"潔淨室A區", particles05:0, particles1:0, particles5:0, temp:22.0, humidity:45.0, pressure:12.5, operator:"", result:"合格" });
  }
  function saveEdit() {
    setEnvRecords(prev => prev.map(r => r.id===editTarget.id ? { ...editTarget, particles05:parseFloat(editTarget.particles05)||0, particles1:parseFloat(editTarget.particles1)||0, particles5:parseFloat(editTarget.particles5)||0, temp:parseFloat(editTarget.temp)||0, humidity:parseFloat(editTarget.humidity)||0, pressure:parseFloat(editTarget.pressure)||0 } : r));
    setEditTarget(null);
  }
  function deleteRec(id) {
    if (!confirm("確定刪除此筆監測紀錄？")) return;
    setEnvRecords(prev => prev.filter(r => r.id !== id));
  }
  async function importXlsx(file) {
    if (!window.XLSX) { alert("SheetJS 未載入"); return; }
    const ab = await file.arrayBuffer();
    const wb = window.XLSX.read(ab, { type:"array", cellDates:true });
    const rows = window.XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { defval:"" });
    const newRecs = rows.map((r, i) => {
      const date = r["日期"] ? (r["日期"] instanceof Date ? r["日期"].toISOString().split("T")[0] : String(r["日期"]).substring(0,10)) : "";
      const temp = parseFloat(r["實際溫度(°C)"] ?? r["溫度"] ?? 22) || 22;
      const humidity = parseFloat(r["濕度(%RH)"] ?? r["濕度"] ?? 45) || 45;
      const pressure = parseFloat(r["壓差"] ?? r["正壓"] ?? 12) || 12;
      const result = r["溫度是否合格"]==="是"&&r["濕度是否合格"]==="是" ? "合格" : (r["結果"]||"合格");
      return { id:`ENV-IMP-${Date.now()}-${i}`, date, location:"潔淨室", particles05:0, particles1:0, particles5:0, temp, humidity, pressure, operator:r["記錄者"]||r["operator"]||"", result };
    }).filter(r => r.date);
    setEnvRecords(prev => [...prev, ...newRecs]);
    alert(`✓ 匯入 ${newRecs.length} 筆環境監測紀錄`);
  }
  const passRate = envRecords.length>0?Math.round(envRecords.filter(r=>r.result==="合格").length/envRecords.length*100):0;
  const envFields = [["監測日期","date","date"],["地點","location","text"],["≥ 0.5μm 個數","particles05","number"],["≥ 1μm 個數","particles1","number"],["≥ 5μm 個數","particles5","number"],["溫度 (°C)","temp","number"],["濕度 (%)","humidity","number"],["正壓 (Pa)","pressure","number"],["記錄者","operator","text"]];
  return (
    <div>
      <SectionHeader title="工作環境監控（MP-06）" count={envRecords.length} color="#14b8a6" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="監測總筆數" value={envRecords.length} color="#14b8a6" />
        <StatCard label="合格筆數" value={envRecords.filter(r=>r.result==="合格").length} color="#22c55e" />
        <StatCard label="警告筆數" value={envRecords.filter(r=>r.result==="警告").length} color="#eab308" />
        <StatCard label="不合格筆數" value={envRecords.filter(r=>r.result==="不合格").length} color="#ef4444" />
        <StatCard label="整體合格率" value={`${passRate}%`} color={passRate>=90?"#22c55e":passRate>=80?"#eab308":"#ef4444"} sub="全期監測計" />
      </div>
      <div style={{ background: "rgba(20,184,166,0.06)", border: "1px solid rgba(20,184,166,0.2)", borderRadius: 12, padding: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: "#2dd4bf", fontWeight: 700, marginBottom: 8 }}>[Class 1000] 潔淨室標準指引</div>
        <div style={{ display:"flex", gap:24, flexWrap:"wrap", fontSize:12, color:"#64748b" }}>
          <span>≥ 0.5μm粒子：≤ 1,000 個/立方尺</span><span>≥ 5μm粒子：≤ 35 個/立方尺</span>
          <span>溫度：21–23°C</span><span>濕度：40–50% RH</span><span>正壓：≥ 10 Pa</span>
        </div>
      </div>
      <div style={{ display:"flex", gap:10, justifyContent:"flex-end", marginBottom:14, flexWrap:"wrap" }}>
        <label style={{ background:"linear-gradient(135deg,#0d9488,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700, display:"flex", alignItems:"center", gap:6 }}>
          📥 匯入 XLSX
          <input type="file" accept=".xlsx,.xls" style={{ display:"none" }} onChange={e=>{ if(e.target.files[0]) importXlsx(e.target.files[0]); e.target.value=""; }} />
        </label>
        <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #0d9488, #14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>＋ 新增監測紀錄</button>
      </div>
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
          <thead><tr>{["編號","日期","地點","≥ 0.5μm","≥ 1μm","≥ 5μm","溫度(°C)","濕度(%)","正壓(Pa)","記錄者","結果","操作"].map(h => (<th key={h} style={{ textAlign:"left", padding:"8px 10px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>))}</tr></thead>
          <tbody>
            {sorted.map((r,i) => (
              <tr key={r.id} style={{ background:i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                <td style={{ padding:"8px 10px", color:"#14b8a6", fontFamily:"monospace" }}>{r.id}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8", whiteSpace:"nowrap" }}>{formatDate(r.date)}</td>
                <td style={{ padding:"8px 10px", color:"#e2e8f0" }}>{r.location}</td>
                <td style={{ padding:"8px 10px", color:(r.particles05||0)>1000?"#ef4444":(r.particles05||0)>800?"#eab308":"#94a3b8" }}>{(r.particles05||0).toLocaleString()}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{(r.particles1||0).toLocaleString()}</td>
                <td style={{ padding:"8px 10px", color:(r.particles5||0)>35?"#ef4444":(r.particles5||0)>20?"#eab308":"#94a3b8" }}>{r.particles5||0}</td>
                <td style={{ padding:"8px 10px", color:r.temp>23||r.temp<21?"#ef4444":"#94a3b8" }}>{Number(r.temp||0).toFixed(1)}</td>
                <td style={{ padding:"8px 10px", color:r.humidity>50||r.humidity<40?"#ef4444":"#94a3b8" }}>{Number(r.humidity||0).toFixed(1)}</td>
                <td style={{ padding:"8px 10px", color:(r.pressure||0)<10?"#ef4444":"#94a3b8" }}>{Number(r.pressure||0).toFixed(1)}</td>
                <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.operator}</td>
                <td style={{ padding:"8px 10px" }}><Badge color={resultColor(r.result)}>{r.result}</Badge></td>
                <td style={{ padding:"8px 10px", whiteSpace:"nowrap" }}>
                  <button onClick={() => setEditTarget({...r})} style={{ background:"rgba(96,165,250,0.1)", border:"1px solid rgba(96,165,250,0.3)", borderRadius:6, color:"#60a5fa", cursor:"pointer", padding:"2px 8px", fontSize:11, marginRight:4 }}>✏</button>
                  <button onClick={() => deleteRec(r.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:6, color:"#f87171", cursor:"pointer", padding:"2px 8px", fontSize:11 }}>🗑</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {showAdd && (<Modal title="新增環境監測紀錄" onClose={() => setShowAdd(false)}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{envFields.map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={newRec[field]} onChange={e=>setNewRec({...newRec,[field]:e.target.value})} step={type==="number"?"0.1":undefined} style={inputStyle} /></div>))}<div style={{ background:"rgba(20,184,166,0.1)", borderRadius:8, padding:10, fontSize:12, color:"#2dd4bf" }}>系統將根據監測數據自動判定結果（合格 / 警告 / 不合格）</div><button onClick={addRec} style={{ background:"linear-gradient(135deg,#0d9488,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:15, fontWeight:700, marginTop:8 }}>✓ 儲存監測紀錄</button></div></Modal>)}
      {editTarget && (<Modal title={`編輯紀錄：${editTarget.id}`} onClose={() => setEditTarget(null)}><div style={{ display:"flex", flexDirection:"column", gap:12 }}>{envFields.map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={editTarget[field]??""} onChange={e=>setEditTarget({...editTarget,[field]:e.target.value})} step={type==="number"?"0.1":undefined} style={inputStyle} /></div>))}<div style={{ display:"flex", gap:10, marginTop:8 }}><button onClick={saveEdit} style={{ flex:1, background:"linear-gradient(135deg,#0d9488,#14b8a6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px", fontSize:14, fontWeight:700 }}>✓ 儲存</button><button onClick={() => { deleteRec(editTarget.id); setEditTarget(null); }} style={{ background:"rgba(239,68,68,0.15)", border:"1px solid rgba(239,68,68,0.4)", borderRadius:10, color:"#f87171", cursor:"pointer", padding:"12px 18px", fontSize:14, fontWeight:700 }}>🗑 刪除</button></div></div></Modal>)}
    </div>
  );
}'''

# ─── CALIBRATION TAB: add full edit modal ───────────────────────────────────
CALIB_OLD = '''// ─── CALIBRATION TAB ─────────────────────────────────────────────────────────
function CalibrationTab({ instruments, setInstruments }) {
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState({});
  const enriched = instruments.map(i => {
    const nextDate = i.status === "免校正" ? null : addDays(i.calibratedDate, i.intervalDays);
    const days = nextDate ? daysUntil(nextDate) : 9999;
    return { ...i, nextDate, days };
  }).sort((a, b) => a.days - b.days);
  function handleUpdate() {
    setInstruments(prev => prev.map(i => i.id === modal.id ? { ...i, calibratedDate: form.date, status: "合格" } : i));
    setModal(null);
  }'''
CALIB_NEW = '''// ─── CALIBRATION TAB ─────────────────────────────────────────────────────────
function CalibrationTab({ instruments, setInstruments }) {
  const [modal, setModal] = useState(null);    // "update" | "edit" | "add"
  const [form, setForm] = useState({});
  const [editTarget, setEditTarget] = useState(null);
  const emptyInst = { id:"", name:"", type:"", location:"", keeper:"", brand:"", model:"", serialNo:"", calibMethod:"外校", calibratedDate:"", intervalDays:365, status:"合格", needsMSA:false };
  const enriched = instruments.map(i => {
    const nextDate = i.status === "免校正" ? null : addDays(i.calibratedDate, i.intervalDays);
    const days = nextDate ? daysUntil(nextDate) : 9999;
    return { ...i, nextDate, days };
  }).sort((a, b) => a.days - b.days);
  function handleUpdate() {
    setInstruments(prev => prev.map(i => i.id === modal.id ? { ...i, calibratedDate: form.date, status: "合格" } : i));
    setModal(null);
  }
  function saveEdit() {
    if (modal === "add") {
      setInstruments(prev => [...prev, { ...editTarget, intervalDays: parseInt(editTarget.intervalDays)||365, needsMSA: !!editTarget.needsMSA }]);
    } else {
      setInstruments(prev => prev.map(i => i.id === editTarget.id ? { ...editTarget, intervalDays: parseInt(editTarget.intervalDays)||365 } : i));
    }
    setEditTarget(null); setModal(null);
  }
  function deleteInst(id) {
    if (!confirm("確定刪除此儀器？")) return;
    setInstruments(prev => prev.filter(i => i.id !== id));
  }
  const instFields = [["儀器編號","id","text"],["儀器名稱","name","text"],["類型","type","text"],["位置","location","text"],["保管人","keeper","text"],["品牌","brand","text"],["型號","model","text"],["序號","serialNo","text"],["校驗方式","calibMethod","text"],["最近校正日","calibratedDate","date"],["校驗間隔(天)","intervalDays","number"]];'''

# ─── CALIBRATION TAB: update the return JSX to add edit/add buttons ─────────
CALIB_RETURN_OLD = '''  return (
    <div>
      <SectionHeader title="量規儀器校正追蹤" count={enriched.length} color="#60a5fa" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="逾期" value={enriched.filter(i => i.days < 0).length} color="#ef4444" />
        <StatCard label="14天內到期" value={enriched.filter(i => i.days >= 0 && i.days <= 14).length} color="#f97316" />
        <StatCard label="正常" value={enriched.filter(i => i.days > 30).length} color="#22c55e" />'''
CALIB_RETURN_NEW = '''  return (
    <div>
      <SectionHeader title="量規儀器校正追蹤" count={enriched.length} color="#60a5fa" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="逾期" value={enriched.filter(i => i.days < 0).length} color="#ef4444" />
        <StatCard label="14天內到期" value={enriched.filter(i => i.days >= 0 && i.days <= 14).length} color="#f97316" />
        <StatCard label="正常" value={enriched.filter(i => i.days > 30).length} color="#22c55e" />'''

# ─── CALIBRATION TAB: add edit button to each instrument row ─────────────────
CALIB_BTN_OLD = '''            <button onClick={() => { setModal(inst); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12, fontWeight: 600 }}>更新校正</button>'''
CALIB_BTN_NEW = '''            <button onClick={() => { setModal(inst); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12, fontWeight: 600 }}>更新校正</button>
            <button onClick={() => { setEditTarget({...inst}); setModal("edit"); }} style={{ background: "rgba(96,165,250,0.1)", border: "1px solid rgba(96,165,250,0.3)", borderRadius: 8, color: "#60a5fa", cursor: "pointer", padding: "6px 10px", fontSize: 12 }}>✏</button>
            <button onClick={() => deleteInst(inst.id)} style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: 8, color: "#f87171", cursor: "pointer", padding: "6px 10px", fontSize: 12 }}>🗑</button>'''

# ─── CALIBRATION TAB: add edit modal + add button before closing </div> ──────
CALIB_MODAL_OLD = '''      {modal && (
        <Modal title={`更新校正記錄：${modal.name}`} onClose={() => setModal(null)}>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>儀器編號</div><div style={{ color: "#e2e8f0", fontWeight: 600 }}>{modal.id}</div></div>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>本次校正日期</div><input type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} style={inputStyle} /></div>
            <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.2)", borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 12, color: "#4ade80", fontWeight: 600 }}>更新後，下次校正日期將為：</div>
              <div style={{ color: "#86efac", fontWeight: 700, fontSize: 16, marginTop: 4 }}>{formatDate(addDays(form.date || modal.calibratedDate, modal.intervalDays))}</div>
            </div>
            <button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #3b82f6, #6366f1)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認更新校正記錄</button>
          </div>
        </Modal>
      )}
    </div>
  );
}'''
CALIB_MODAL_NEW = '''      {modal && modal !== "edit" && modal !== "add" && (
        <Modal title={`更新校正記錄：${modal.name}`} onClose={() => setModal(null)}>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>儀器編號</div><div style={{ color: "#e2e8f0", fontWeight: 600 }}>{modal.id}</div></div>
            <div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>本次校正日期</div><input type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} style={inputStyle} /></div>
            <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.2)", borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 12, color: "#4ade80", fontWeight: 600 }}>更新後，下次校正日期將為：</div>
              <div style={{ color: "#86efac", fontWeight: 700, fontSize: 16, marginTop: 4 }}>{formatDate(addDays(form.date || modal.calibratedDate, modal.intervalDays))}</div>
            </div>
            <button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #3b82f6, #6366f1)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認更新校正記錄</button>
          </div>
        </Modal>
      )}
      {(modal === "edit" || modal === "add") && editTarget && (
        <Modal title={modal==="add"?"新增儀器":`編輯儀器：${editTarget.name}`} onClose={() => { setEditTarget(null); setModal(null); }}>
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {instFields.map(([label,field,type]) => (<div key={field}><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div><input type={type} value={editTarget[field]??""} onChange={e=>setEditTarget({...editTarget,[field]:e.target.value})} style={inputStyle} /></div>))}
            <div><div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>狀態</div><select value={editTarget.status||"合格"} onChange={e=>setEditTarget({...editTarget,status:e.target.value})} style={inputStyle}><option>合格</option><option>不合格</option><option>免校正</option></select></div>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}><input type="checkbox" checked={!!editTarget.needsMSA} onChange={e=>setEditTarget({...editTarget,needsMSA:e.target.checked})} /><span style={{ color:"#94a3b8", fontSize:13 }}>需要 MSA 分析</span></div>
            <div style={{ display:"flex", gap:10, marginTop:8 }}><button onClick={saveEdit} style={{ flex:1, background:"linear-gradient(135deg,#3b82f6,#6366f1)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px", fontSize:14, fontWeight:700 }}>✓ 儲存</button>{modal==="edit" && <button onClick={() => { deleteInst(editTarget.id); setEditTarget(null); setModal(null); }} style={{ background:"rgba(239,68,68,0.15)", border:"1px solid rgba(239,68,68,0.4)", borderRadius:10, color:"#f87171", cursor:"pointer", padding:"12px 18px", fontSize:14, fontWeight:700 }}>🗑 刪除</button>}</div>
          </div>
        </Modal>
      )}
      <div style={{ display:"flex", justifyContent:"flex-end", marginTop:16 }}>
        <button onClick={() => { setEditTarget({...emptyInst}); setModal("add"); }} style={{ background:"linear-gradient(135deg,#3b82f6,#6366f1)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>＋ 新增儀器</button>
      </div>
    </div>
  );
}'''

# ═══════════════════════════════════════════════════════════════
# STEP 2: Replace App() with LocalStorage + new tabs
# ═══════════════════════════════════════════════════════════════
APP_OLD = '''// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [instruments, setInstruments] = useState(initialInstruments);
  const [documents, setDocuments] = useState(initialDocuments);
  const [training, setTraining] = useState(initialTraining);
  const [equipment, setEquipment] = useState(initialEquipment);
  const [suppliers, setSuppliers] = useState(initialSuppliers);
  const [nonConformances, setNonConformances] = useState(initialNonConformances);
  const [auditPlans, setAuditPlans] = useState(initialAuditPlans);
  const [envRecords, setEnvRecords] = useState(initialEnvRecords);
  const [manuals] = useState(initialManuals);

  const tabs = [
    { id: "home",           label: "主控台",   icon: "⌂" },
    { id: "calibration",    label: "校正管理", icon: "◎" },
    { id: "documents",      label: "文件管理", icon: "≡" },
    { id: "library",        label: "文件庫",   icon: "📂" },
    { id: "training",       label: "訓練管理", icon: "□" },
    { id: "equipment",      label: "設備保養", icon: "⚙" },
    { id: "supplier",       label: "供應商管理", icon: "◈" },
    { id: "nonconformance", label: "不符合管理", icon: "⚠" },
    { id: "auditplan",      label: "稽核計畫", icon: "✓" },
    { id: "environment",    label: "環境監測", icon: "◉" },
    { id: "report",         label: "稽核報告", icon: "☰" },
  ];

  function renderTab() {
    switch(activeTab) {
      case "home":           return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setActiveTab} />;
      case "calibration":    return <CalibrationTab instruments={instruments} setInstruments={setInstruments} />;
      case "documents":      return <DocumentsTab documents={documents} setDocuments={setDocuments} />;
      case "library":        return <LibraryTab documents={documents} manuals={manuals} />;
      case "training":       return <TrainingTab training={training} setTraining={setTraining} />;
      case "equipment":      return <EquipmentTab equipment={equipment} setEquipment={setEquipment} />;
      case "supplier":       return <SupplierTab suppliers={suppliers} setSuppliers={setSuppliers} />;
      case "nonconformance": return <NonConformanceTab nonConformances={nonConformances} setNonConformances={setNonConformances} />;
      case "auditplan":      return <AuditPlanTab auditPlans={auditPlans} setAuditPlans={setAuditPlans} />;
      case "environment":    return <EnvironmentTab envRecords={envRecords} setEnvRecords={setEnvRecords} />;
      case "report":         return <ReportTab instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} />;
      default:               return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setActiveTab} />;
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #0a0f1e 0%, #0d1117 50%, #080d1a 100%)", color: "#e2e8f0", fontFamily: "'Noto Sans TC', sans-serif" }}>
      <div style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "0 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "16px 16px", fontSize: 12, fontWeight: 600,
              color: activeTab === t.id ? "#60a5fa" : "#64748b",
              borderBottom: activeTab === t.id ? "2px solid #60a5fa" : "2px solid transparent",
              whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 6,
              transition: "color 0.2s"
            }}>
              <span style={{ fontSize: 14 }}>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </div>
      </div>
      <div style={{ maxWidth: 1400, margin: "0 auto", padding: "28px 24px" }}>
        {renderTab()}
      </div>
    </div>
  );
}'''

APP_NEW = '''// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState("home");

  // Phase C: LocalStorage-backed state for all modules
  function ls(key, init) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : init; } catch(e) { return init; }
  }
  const [instruments, setInstruments] = useState(() => ls("audit_instruments", initialInstruments));
  const [documents,   setDocuments]   = useState(() => ls("audit_documents",   initialDocuments));
  const [training,    setTraining]    = useState(() => ls("audit_training",    initialTraining));
  const [equipment,   setEquipment]   = useState(() => ls("audit_equipment",   initialEquipment));
  const [suppliers,   setSuppliers]   = useState(() => ls("audit_suppliers",   initialSuppliers));
  const [nonConformances, setNonConformances] = useState(() => ls("audit_ncs",      initialNonConformances));
  const [auditPlans,  setAuditPlans]  = useState(() => ls("audit_auditPlans",  initialAuditPlans));
  const [envRecords,  setEnvRecords]  = useState(() => ls("audit_envRecords",  initialEnvRecords));
  const [prodRecords, setProdRecords] = useState(() => ls("audit_prodRecords", []));
  const [manuals] = useState(initialManuals);

  // Auto-save to localStorage on every change
  useEffect(() => { try { localStorage.setItem("audit_instruments", JSON.stringify(instruments)); } catch(e) {} }, [instruments]);
  useEffect(() => { try { localStorage.setItem("audit_documents",   JSON.stringify(documents));   } catch(e) {} }, [documents]);
  useEffect(() => { try { localStorage.setItem("audit_training",    JSON.stringify(training));    } catch(e) {} }, [training]);
  useEffect(() => { try { localStorage.setItem("audit_equipment",   JSON.stringify(equipment));   } catch(e) {} }, [equipment]);
  useEffect(() => { try { localStorage.setItem("audit_suppliers",   JSON.stringify(suppliers));   } catch(e) {} }, [suppliers]);
  useEffect(() => { try { localStorage.setItem("audit_ncs",         JSON.stringify(nonConformances)); } catch(e) {} }, [nonConformances]);
  useEffect(() => { try { localStorage.setItem("audit_auditPlans",  JSON.stringify(auditPlans));  } catch(e) {} }, [auditPlans]);
  useEffect(() => { try { localStorage.setItem("audit_envRecords",  JSON.stringify(envRecords));  } catch(e) {} }, [envRecords]);
  useEffect(() => { try { localStorage.setItem("audit_prodRecords", JSON.stringify(prodRecords)); } catch(e) {} }, [prodRecords]);

  function resetAllData() {
    if (!confirm("確定要重置所有資料至初始狀態？此操作無法復原！")) return;
    ["audit_instruments","audit_documents","audit_training","audit_equipment","audit_suppliers","audit_ncs","audit_auditPlans","audit_envRecords","audit_prodRecords"].forEach(k => { try { localStorage.removeItem(k); } catch(e) {} });
    window.location.reload();
  }

  const tabs = [
    { id: "home",           label: "主控台",   icon: "⌂" },
    { id: "calibration",    label: "校正管理", icon: "◎" },
    { id: "documents",      label: "文件管理", icon: "≡" },
    { id: "library",        label: "文件庫",   icon: "📂" },
    { id: "training",       label: "訓練管理", icon: "□" },
    { id: "equipment",      label: "設備保養", icon: "⚙" },
    { id: "supplier",       label: "供應商管理", icon: "◈" },
    { id: "nonconformance", label: "不符合管理", icon: "⚠" },
    { id: "auditplan",      label: "稽核計畫", icon: "✓" },
    { id: "environment",    label: "環境監測", icon: "◉" },
    { id: "production",     label: "生產品質", icon: "📊" },
    { id: "notification",   label: "通知提醒", icon: "🔔" },
    { id: "report",         label: "稽核報告", icon: "☰" },
  ];

  function renderTab() {
    switch(activeTab) {
      case "home":           return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setActiveTab} />;
      case "calibration":    return <CalibrationTab instruments={instruments} setInstruments={setInstruments} />;
      case "documents":      return <DocumentsTab documents={documents} setDocuments={setDocuments} />;
      case "library":        return <LibraryTab documents={documents} manuals={manuals} />;
      case "training":       return <TrainingTab training={training} setTraining={setTraining} />;
      case "equipment":      return <EquipmentTab equipment={equipment} setEquipment={setEquipment} />;
      case "supplier":       return <SupplierTab suppliers={suppliers} setSuppliers={setSuppliers} />;
      case "nonconformance": return <NonConformanceTab nonConformances={nonConformances} setNonConformances={setNonConformances} />;
      case "auditplan":      return <AuditPlanTab auditPlans={auditPlans} setAuditPlans={setAuditPlans} />;
      case "environment":    return <EnvironmentTab envRecords={envRecords} setEnvRecords={setEnvRecords} />;
      case "production":     return <ProductionTab prodRecords={prodRecords} setProdRecords={setProdRecords} />;
      case "notification":   return <NotificationTab instruments={instruments} equipment={equipment} suppliers={suppliers} auditPlans={auditPlans} />;
      case "report":         return <ReportTab instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} />;
      default:               return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setActiveTab} />;
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "linear-gradient(135deg, #0a0f1e 0%, #0d1117 50%, #080d1a 100%)", color: "#e2e8f0", fontFamily: "'Noto Sans TC', sans-serif" }}>
      <div style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.08)", padding: "0 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto" }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "16px 14px", fontSize: 12, fontWeight: 600,
              color: activeTab === t.id ? "#60a5fa" : "#64748b",
              borderBottom: activeTab === t.id ? "2px solid #60a5fa" : "2px solid transparent",
              whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 6,
              transition: "color 0.2s"
            }}>
              <span style={{ fontSize: 13 }}>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
          <div style={{ marginLeft:"auto", flexShrink:0 }}>
            <button onClick={resetAllData} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, color:"#f87171", cursor:"pointer", padding:"6px 12px", fontSize:11, fontWeight:600, whiteSpace:"nowrap", margin:"0 8px" }}>🔄 重置資料</button>
          </div>
        </div>
      </div>
      <div style={{ maxWidth: 1400, margin: "0 auto", padding: "28px 24px" }}>
        {renderTab()}
      </div>
    </div>
  );
}'''

# ═══════════════════════════════════════════════════════════════
# STEP 3: Insert ProductionTab + NotificationTab before DashboardHome
# ═══════════════════════════════════════════════════════════════
NEW_COMPONENTS = r'''
// ─── PRODUCTION TAB (MP-11/12) ───────────────────────────────────────────────
function ProductionTab({ prodRecords, setProdRecords }) {
  const [downloading, setDownloading] = useState(false);
  const prodRecs = prodRecords.filter(r => r.type === "production");
  const qcRecs   = prodRecords.filter(r => r.type === "quality");
  const avgYield = prodRecs.length
    ? (prodRecs.reduce((s,r) => s + (parseFloat(r.yieldRate) || (r.input>0 ? r.good/r.input*100 : 0)), 0) / prodRecs.length).toFixed(1)
    : 0;

  async function importXlsx(file, type) {
    if (!window.XLSX) { alert("SheetJS 未載入，請確認 CDN 已載入"); return; }
    const ab = await file.arrayBuffer();
    const wb = window.XLSX.read(ab, { type:"array", cellDates:true });
    const rows = window.XLSX.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { defval:"" });
    if (type === "production") {
      const newRecs = rows.map((r,i) => ({
        id: `PROD-${Date.now()}-${i}`, type:"production",
        lot: String(r["批次號碼"]||r["Lot"]||r["waferBoatLot"]||""),
        customer: String(r["客戶代號"]||r["客戶"]||""),
        product: String(r["產品名稱"]||r["產品"]||""),
        input: parseInt(r["投入數"]||r["input"]||0)||0,
        good: parseInt(r["良品數"]||r["good"]||0)||0,
        defect: parseInt(r["不良品數"]||r["defect"]||0)||0,
        yieldRate: parseFloat(r["良率"]||r["yieldRate"]||0)||0,
        defectReasons: String(r["不良原因"]||"").split(/[,，;；]/).filter(Boolean),
        operator: String(r["操作員"]||r["operator"]||""),
        note: String(r["備註"]||""),
        importedAt: new Date().toISOString().split("T")[0],
      }));
      setProdRecords(prev => [...prev, ...newRecs]);
      alert(`✓ 已匯入 ${newRecs.length} 筆生產記錄`);
    } else {
      const newRecs = rows.map((r,i) => ({
        id: `QC-${Date.now()}-${i}`, type:"quality",
        materialName: String(r["原料名稱"]||r["名稱"]||""),
        batchNo: String(r["原料批號"]||r["批號"]||""),
        quantity: String(r["原料數量"]||r["數量"]||""),
        spec: String(r["規格"]||""),
        ph: String(r["PH值"]||r["pH"]||""),
        density: String(r["比重值"]||r["比重"]||""),
        ri: String(r["RI值"]||r["RI"]||""),
        result: String(r["檢驗結果"]||r["result"]||"合格"),
        note: String(r["備註"]||""),
        importedAt: new Date().toISOString().split("T")[0],
      }));
      setProdRecords(prev => [...prev, ...newRecs]);
      alert(`✓ 已匯入 ${newRecs.length} 筆品質記錄`);
    }
  }

  async function downloadRecords(type) {
    const data = prodRecords.filter(r => r.type === type);
    if (!data.length) { alert("目前沒有資料可下載"); return; }
    setDownloading(true);
    try {
      const resp = await fetch("/api/generate", {
        method:"POST", headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ type, data })
      });
      if (!resp.ok) { const t = await resp.text(); throw new Error(t); }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = type === "production" ? "生產日報記錄表_已填.xlsx" : "品質管理記錄表_已填.xlsx";
      a.click(); URL.revokeObjectURL(url);
    } catch(e) { alert("下載失敗: " + e.message); }
    setDownloading(false);
  }

  function deleteRec(id) {
    if (!confirm("確定刪除此筆記錄？")) return;
    setProdRecords(prev => prev.filter(r => r.id !== id));
  }

  const btnBase = { border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700, display:"flex", alignItems:"center", gap:6 };
  return (
    <div>
      <SectionHeader title="生產品質記錄（MP-11 / MP-12）" count={prodRecords.length} color="#f59e0b" />
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <StatCard label="生產批次" value={prodRecs.length} color="#f59e0b" />
        <StatCard label="平均良率" value={`${avgYield}%`} color={avgYield>=90?"#22c55e":avgYield>=80?"#eab308":"#ef4444"} />
        <StatCard label="原料品質筆數" value={qcRecs.length} color="#60a5fa" />
        <StatCard label="不合格品質" value={qcRecs.filter(r=>r.result==="不合格"||r.result==="NG").length} color="#ef4444" />
      </div>
      <div style={{ display:"flex", gap:10, marginBottom:20, flexWrap:"wrap" }}>
        <label style={{ ...btnBase, background:"linear-gradient(135deg,#d97706,#f59e0b)" }}>
          📥 匯入生產日報
          <input type="file" accept=".xlsx,.xls" style={{ display:"none" }} onChange={e=>{ if(e.target.files[0]) importXlsx(e.target.files[0],"production"); e.target.value=""; }} />
        </label>
        <label style={{ ...btnBase, background:"linear-gradient(135deg,#0891b2,#06b6d4)" }}>
          📥 匯入品質記錄
          <input type="file" accept=".xlsx,.xls" style={{ display:"none" }} onChange={e=>{ if(e.target.files[0]) importXlsx(e.target.files[0],"quality"); e.target.value=""; }} />
        </label>
        <button onClick={() => downloadRecords("production")} disabled={downloading} style={{ ...btnBase, background:"linear-gradient(135deg,#059669,#10b981)" }}>⬇ 下載生產日報</button>
        <button onClick={() => downloadRecords("quality")} disabled={downloading} style={{ ...btnBase, background:"linear-gradient(135deg,#7c3aed,#8b5cf6)" }}>⬇ 下載品質報告</button>
      </div>

      {prodRecs.length > 0 && (
        <div style={{ marginBottom:24 }}>
          <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>生產批次記錄（{prodRecs.length} 筆）</div>
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
              <thead><tr>{["批次號碼","客戶","產品","投入","良品","不良","良率","不良原因","操作員","日期",""].map(h=><th key={h} style={{ textAlign:"left", padding:"8px 10px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>)}</tr></thead>
              <tbody>{prodRecs.map((r,i)=>{
                const yr = r.yieldRate || (r.input>0 ? Math.round(r.good/r.input*100) : 0);
                return <tr key={r.id} style={{ background:i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                  <td style={{ padding:"8px 10px", color:"#f59e0b", fontFamily:"monospace" }}>{r.lot}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.customer}</td>
                  <td style={{ padding:"8px 10px", color:"#e2e8f0" }}>{r.product}</td>
                  <td style={{ padding:"8px 10px", textAlign:"right", color:"#94a3b8" }}>{(r.input||0).toLocaleString()}</td>
                  <td style={{ padding:"8px 10px", textAlign:"right", color:"#22c55e" }}>{(r.good||0).toLocaleString()}</td>
                  <td style={{ padding:"8px 10px", textAlign:"right", color:"#ef4444" }}>{(r.defect||0).toLocaleString()}</td>
                  <td style={{ padding:"8px 10px", textAlign:"right" }}><Badge color={yr>=95?"#22c55e":yr>=90?"#60a5fa":yr>=80?"#eab308":"#ef4444"}>{yr}%</Badge></td>
                  <td style={{ padding:"8px 10px", color:"#64748b", fontSize:11 }}>{(r.defectReasons||[]).join(", ")}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.operator}</td>
                  <td style={{ padding:"8px 10px", color:"#64748b" }}>{r.importedAt}</td>
                  <td style={{ padding:"8px 10px" }}><button onClick={() => deleteRec(r.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:6, color:"#f87171", cursor:"pointer", padding:"2px 8px", fontSize:11 }}>🗑</button></td>
                </tr>;
              })}</tbody>
            </table>
          </div>
        </div>
      )}

      {qcRecs.length > 0 && (
        <div>
          <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>原料品質記錄（{qcRecs.length} 筆）</div>
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
              <thead><tr>{["原料名稱","批號","數量","規格","PH","比重","RI","結果","備註","日期",""].map(h=><th key={h} style={{ textAlign:"left", padding:"8px 10px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>)}</tr></thead>
              <tbody>{qcRecs.map((r,i)=>(
                <tr key={r.id} style={{ background:i%2===0?"rgba(255,255,255,0.02)":"transparent" }}>
                  <td style={{ padding:"8px 10px", color:"#60a5fa" }}>{r.materialName}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8", fontFamily:"monospace" }}>{r.batchNo}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.quantity}</td>
                  <td style={{ padding:"8px 10px", color:"#64748b" }}>{r.spec}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.ph}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.density}</td>
                  <td style={{ padding:"8px 10px", color:"#94a3b8" }}>{r.ri}</td>
                  <td style={{ padding:"8px 10px" }}><Badge color={r.result==="合格"?"#22c55e":"#ef4444"}>{r.result}</Badge></td>
                  <td style={{ padding:"8px 10px", color:"#64748b", fontSize:11 }}>{r.note}</td>
                  <td style={{ padding:"8px 10px", color:"#64748b" }}>{r.importedAt}</td>
                  <td style={{ padding:"8px 10px" }}><button onClick={() => deleteRec(r.id)} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:6, color:"#f87171", cursor:"pointer", padding:"2px 8px", fontSize:11 }}>🗑</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {prodRecords.length === 0 && (
        <div style={{ textAlign:"center", padding:"60px 20px", color:"#475569" }}>
          <div style={{ fontSize:36, marginBottom:12 }}>📊</div>
          <div style={{ fontSize:16, fontWeight:600, marginBottom:8 }}>尚無生產品質資料</div>
          <div style={{ fontSize:13 }}>請使用上方按鈕匯入 XLSX 記錄表，或直接點「下載」由後端產生空白範本</div>
        </div>
      )}
    </div>
  );
}

// ─── NOTIFICATION TAB ────────────────────────────────────────────────────────
function NotificationTab({ instruments, equipment, suppliers, auditPlans }) {
  const [settings, setSettings] = useState(() => {
    try { return JSON.parse(localStorage.getItem("audit_notifSettings")||"{}"); } catch(e) { return {}; }
  });
  const [showSettings, setShowSettings] = useState(false);
  const [sending, setSending] = useState({});
  const [msg, setMsg] = useState("");

  useEffect(() => {
    try { localStorage.setItem("audit_notifSettings", JSON.stringify(settings)); } catch(e) {}
  }, [settings]);

  function aggregateDeadlines() {
    const items = [];
    instruments.filter(i => i.status !== "免校正").forEach(i => {
      const next = addDays(i.calibratedDate, i.intervalDays);
      if (!next) return;
      const d = daysUntil(next);
      if (d <= 30) items.push({ id:i.id, label:`儀器校正：${i.name}`, date:next, module:"校正管理", responsible:i.keeper||"", days:d });
    });
    equipment.forEach(e => {
      const next = addDays(e.lastMaintenance, e.intervalDays);
      if (!next) return;
      const d = daysUntil(next);
      if (d <= 30) items.push({ id:e.id, label:`設備保養：${e.name}`, date:next, module:"設備保養", responsible:"", days:d });
    });
    suppliers.forEach(s => {
      const next = addDays(s.lastEvalDate, s.evalIntervalDays);
      if (!next) return;
      const d = daysUntil(next);
      if (d <= 30) items.push({ id:s.id, label:`供應商評鑑：${s.name}`, date:next, module:"供應商管理", responsible:s.contact||"", days:d });
    });
    auditPlans.filter(a => a.status === "計畫中").forEach(a => {
      const d = daysUntil(a.scheduledDate);
      if (d >= 0 && d <= 30) items.push({ id:a.id, label:`內部稽核：${a.dept}`, date:a.scheduledDate, module:"稽核計畫", responsible:a.auditor||"", days:d });
    });
    return items.sort((a,b) => a.days - b.days);
  }

  const deadlines = aggregateDeadlines();

  function gcalUrl(item) {
    const d = item.date.replace(/-/g,"");
    const title = encodeURIComponent(`[潔沛] ${item.label}`);
    const details = encodeURIComponent(`到期日：${item.date}\n模組：${item.module}\n負責人：${item.responsible}`);
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${d}/${d}&details=${details}`;
  }

  function mailtoUrl(item) {
    const sub = encodeURIComponent(`[提醒] ${item.label} — 到期日 ${item.date}`);
    const body = encodeURIComponent(`您好，\n\n以下項目即將到期，請安排處理：\n\n項目：${item.label}\n到期日：${item.date}\n負責人：${item.responsible||"（未指定）"}\n\n此為系統自動提醒。`);
    const to = encodeURIComponent(settings.email||"");
    return `mailto:${to}?subject=${sub}&body=${body}`;
  }

  async function sendToNotion(item) {
    if (!settings.notionToken||!settings.notionDbId) {
      alert("請先在設定面板填入 Notion API Token 和 Database ID");
      return;
    }
    setSending(prev => ({ ...prev, [item.id]:true }));
    try {
      const resp = await fetch("/api/notion", {
        method:"POST", headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({
          token: settings.notionToken, db_id: settings.notionDbId,
          properties: {
            "名稱": { title:[{ text:{ content:item.label } }] },
            "到期日": { date:{ start:item.date } },
            "模組": { select:{ name:item.module } },
            "負責人": { rich_text:[{ text:{ content:item.responsible||"" } }] }
          }
        })
      });
      const json = await resp.json();
      if (resp.ok) { setMsg(`✓ 已新增至 Notion：${item.label}`); setTimeout(()=>setMsg(""),4000); }
      else { alert("Notion 錯誤：" + (json.message||JSON.stringify(json))); }
    } catch(e) { alert("連線失敗：" + e.message); }
    setSending(prev => ({ ...prev, [item.id]:false }));
  }

  function createAllCalendar() {
    if (!deadlines.length) { alert("目前沒有到期項目"); return; }
    deadlines.forEach((item,i) => setTimeout(() => window.open(gcalUrl(item), "_blank"), i*400));
  }

  return (
    <div>
      <SectionHeader title="通知與提醒（30天內到期）" count={deadlines.length} color="#f472b6" />
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <StatCard label="逾期項目" value={deadlines.filter(d=>d.days<0).length} color="#ef4444" sub="需立即處理" />
        <StatCard label="14天內" value={deadlines.filter(d=>d.days>=0&&d.days<=14).length} color="#f97316" sub="即將到期" />
        <StatCard label="30天內" value={deadlines.filter(d=>d.days>14&&d.days<=30).length} color="#eab308" sub="需提前準備" />
        <StatCard label="提醒總數" value={deadlines.length} color="#f472b6" />
      </div>

      {msg && <div style={{ background:"rgba(34,197,94,0.1)", border:"1px solid rgba(34,197,94,0.3)", borderRadius:10, padding:"10px 16px", color:"#4ade80", fontSize:13, marginBottom:16 }}>{msg}</div>}

      <div style={{ display:"flex", gap:10, marginBottom:20, flexWrap:"wrap" }}>
        <button onClick={createAllCalendar} disabled={!deadlines.length} style={{ background:"linear-gradient(135deg,#1a73e8,#4285f4)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>📅 一鍵建立全部 Google 行事曆</button>
        <button onClick={() => setShowSettings(s=>!s)} style={{ background:showSettings?"rgba(148,163,184,0.2)":"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"9px 18px", fontSize:13, fontWeight:700 }}>⚙ {showSettings?"收起設定":"展開設定"}</button>
      </div>

      {showSettings && (
        <div style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:14, padding:20, marginBottom:20 }}>
          <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0", marginBottom:16 }}>⚙ 提醒設定</div>
          <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
            {[["預設 Email 收件人","email","text","example@company.com"],["Notion API Token","notionToken","text","secret_xxx..."],["Notion Database ID","notionDbId","text","xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"]].map(([label,field,type,ph])=>(
              <div key={field}>
                <div style={{ fontSize:12, color:"#64748b", marginBottom:5 }}>{label}</div>
                <input type={type} value={settings[field]||""} placeholder={ph} onChange={e=>setSettings(s=>({...s,[field]:e.target.value}))} style={inputStyle} />
              </div>
            ))}
          </div>
          <div style={{ marginTop:10, fontSize:11, color:"#64748b" }}>⚠ Notion 整合需在 server.py 啟動（Flask port 8888）· 設定自動存於 localStorage</div>
        </div>
      )}

      {deadlines.length === 0 && (
        <div style={{ textAlign:"center", padding:"60px 20px", color:"#475569" }}>
          <div style={{ fontSize:36, marginBottom:12 }}>🎉</div>
          <div style={{ fontSize:16, fontWeight:600, marginBottom:8 }}>目前沒有 30 天內到期項目</div>
          <div style={{ fontSize:13 }}>所有校正、保養、評鑑與稽核均在期限內，系統運作正常</div>
        </div>
      )}

      <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
        {deadlines.map(item => (
          <div key={`${item.id}-${item.module}`} style={{
            background: item.days<0?"rgba(239,68,68,0.1)":item.days<=14?"rgba(249,115,22,0.08)":"rgba(234,179,8,0.06)",
            border:`1px solid ${item.days<0?"rgba(239,68,68,0.3)":item.days<=14?"rgba(249,115,22,0.3)":"rgba(234,179,8,0.2)"}`,
            borderRadius:12, padding:"14px 18px", display:"flex", alignItems:"center", gap:14, flexWrap:"wrap"
          }}>
            <div style={{ flex:1, minWidth:200 }}>
              <div style={{ fontWeight:700, color:"#e2e8f0", fontSize:14 }}>{item.label}</div>
              <div style={{ fontSize:12, color:"#64748b", marginTop:2 }}>模組：{item.module} · 負責人：{item.responsible||"未指定"} · 到期：{formatDate(item.date)}</div>
            </div>
            <Badge color={urgencyColor(item.days)}>{urgencyLabel(item.days)}</Badge>
            <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
              <a href={gcalUrl(item)} target="_blank" rel="noopener noreferrer" style={{ background:"linear-gradient(135deg,#1a73e8,#4285f4)", color:"#fff", padding:"6px 12px", borderRadius:8, fontSize:12, fontWeight:700, textDecoration:"none" }}>📅 行事曆</a>
              <a href={mailtoUrl(item)} style={{ background:"linear-gradient(135deg,#0891b2,#06b6d4)", color:"#fff", padding:"6px 12px", borderRadius:8, fontSize:12, fontWeight:700, textDecoration:"none" }}>✉ Email</a>
              <button onClick={() => sendToNotion(item)} disabled={!!sending[item.id]} style={{ background:sending[item.id]?"rgba(99,102,241,0.3)":"linear-gradient(135deg,#4f46e5,#6366f1)", border:"none", borderRadius:8, color:"#fff", cursor:"pointer", padding:"6px 12px", fontSize:12, fontWeight:700 }}>🔗 {sending[item.id]?"傳送中…":"Notion"}</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

'''

DASHBOARD_MARKER = "// ─── DASHBOARD HOME ──────────────────────────────────────────────────────────"

# ═══════════════════════════════════════════════════════════════
# Apply all patches
# ═══════════════════════════════════════════════════════════════
def patch(src, old, new, name):
    if old in src:
        print(f"  [OK] patching: {name}")
        return src.replace(old, new, 1)
    print(f"  [SKIP] not found (already patched?): {name}")
    return src

src = patch(src, ENV_OLD,          ENV_NEW,          "EnvironmentTab header")
src = patch(src, CALIB_OLD,        CALIB_NEW,        "CalibrationTab header")
src = patch(src, CALIB_BTN_OLD,    CALIB_BTN_NEW,    "CalibrationTab row buttons")
src = patch(src, CALIB_MODAL_OLD,  CALIB_MODAL_NEW,  "CalibrationTab modal")
src = patch(src, APP_OLD,          APP_NEW,          "App() function")
src = patch(src, DASHBOARD_MARKER, NEW_COMPONENTS + DASHBOARD_MARKER, "ProductionTab + NotificationTab insert")

with open(SRC, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n[DONE] audit-dashboard.jsx updated ({len(src)} chars)")
