// ─── TRAINING TAB ─────────────────────────────────────────────────────────────
function TrainingTab({ training, setTraining }) {
  const [selected, setSelected] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newRecord, setNewRecord] = useState({ course: "", date: "", type: "內訓", result: "合格", cert: "無" });
  function addTraining() {
    setTraining(prev => prev.map(emp => emp.id === selected.id ? { ...emp, trainings: [...emp.trainings, { ...newRecord }] } : emp));
    setSelected(prev => ({ ...prev, trainings: [...prev.trainings, { ...newRecord }] }));
    setShowAdd(false);
    setNewRecord({ course: "", date: "", type: "內訓", result: "合格", cert: "無" });
  }
  return (
    <div>
      <SectionHeader title="人員訓練記錄" count={training.length} color="#34d399" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="員工人數" value={training.length} color="#34d399" />
        <StatCard label="訓練總筆數" value={training.reduce((s,e) => s+e.trainings.length,0)} color="#60a5fa" />
        <StatCard label="外訓筆數" value={training.reduce((s,e) => s+e.trainings.filter(t=>t.type==="外訓").length,0)} color="#a78bfa" />
        <StatCard label="有證書筆數" value={training.reduce((s,e) => s+e.trainings.filter(t=>t.cert==="有").length,0)} color="#f472b6" />
      </div>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div style={{ flex: "0 0 260px", display: "flex", flexDirection: "column", gap: 8 }}>
          {training.map(emp => {
            const hireMonths = Math.floor((today - new Date(emp.hireDate)) / (30*86400000));
            const isNew = hireMonths < 3;
            return (<div key={emp.id} onClick={() => setSelected(emp)} style={{ background: selected?.id===emp.id?"rgba(52,211,153,0.15)":"rgba(255,255,255,0.04)", border: `1px solid ${selected?.id===emp.id?"rgba(52,211,153,0.4)":"rgba(255,255,255,0.08)"}`, borderRadius: 12, padding: "14px 16px", cursor: "pointer" }}><div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div><div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 14 }}>{emp.name}</div><div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{emp.dept} · {emp.role}</div></div><div style={{ textAlign: "right" }}>{isNew&&<Badge color="#f97316">新進</Badge>}<div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>{emp.trainings.length} 筆訓練</div></div></div></div>);
          })}
        </div>
        <div style={{ flex: 1, minWidth: 280 }}>
          {selected ? (
            <div>
              <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 12, padding: 16, border: "1px solid rgba(255,255,255,0.08)", marginBottom: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#e2e8f0" }}>{selected.name}</div>
                    <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>{selected.id} · {selected.dept} · {selected.role}</div>
                    <div style={{ color: "#64748b", fontSize: 12, marginTop: 2 }}>到職日：{formatDate(selected.hireDate)}</div>
                  </div>
                  <button onClick={() => setShowAdd(true)} style={{ background: "linear-gradient(135deg, #059669, #10b981)", border: "none", borderRadius: 8, color: "#fff", cursor: "pointer", padding: "7px 14px", fontSize: 12, fontWeight: 700 }}>＋ 新增訓練</button>
                </div>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {selected.trainings.map((t,i) => (<div key={i} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 10, padding: "12px 16px", display: "flex", gap: 16, alignItems: "center" }}><div style={{ flex: 1 }}><div style={{ fontWeight: 600, color: "#e2e8f0", fontSize: 13 }}>{t.course}</div><div style={{ fontSize: 11, color: "#64748b", marginTop: 3 }}>{formatDate(t.date)} · {t.type}</div></div><Badge color={t.result==="合格"?"#22c55e":"#ef4444"}>{t.result}</Badge>{t.cert==="有"&&<Badge color="#a78bfa">有證書</Badge>}</div>))}
              </div>
            </div>
          ) : (<div style={{ textAlign: "center", padding: "60px 20px", color: "#475569" }}>← 點選左側員工以查看訓練記錄</div>)}
        </div>
      </div>
      {showAdd && selected && (<Modal title={`新增訓練記錄：${selected.name}`} onClose={() => setShowAdd(false)}><div style={{ display: "flex", flexDirection: "column", gap: 12 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 5 }}>課程名稱</div><input value={newRecord.course} onChange={e => setNewRecord({...newRecord,course:e.target.value})} style={inputStyle} /></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 5 }}>訓練日期</div><input type="date" value={newRecord.date} onChange={e => setNewRecord({...newRecord,date:e.target.value})} style={inputStyle} /></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 5 }}>訓練類型</div><select value={newRecord.type} onChange={e => setNewRecord({...newRecord,type:e.target.value})} style={inputStyle}><option>內訓</option><option>外訓</option></select></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 5 }}>評估結果</div><select value={newRecord.result} onChange={e => setNewRecord({...newRecord,result:e.target.value})} style={inputStyle}><option>合格</option><option>不合格</option><option>待評估</option></select></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 5 }}>是否有結業證書</div><select value={newRecord.cert} onChange={e => setNewRecord({...newRecord,cert:e.target.value})} style={inputStyle}><option>無</option><option>有</option></select></div><button onClick={addTraining} style={{ background: "linear-gradient(135deg, #059669, #10b981)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700, marginTop: 8 }}>✓ 儲存訓練記錄</button></div></Modal>)}
    </div>
  );
}
