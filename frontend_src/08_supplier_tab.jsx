// ─── SUPPLIER TAB (MP-10) ────────────────────────────────────────────────────
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
  }
  const scoreColor = s => s>=90?"#22c55e":s>=80?"#60a5fa":s>=70?"#eab308":"#ef4444";
  return (
    <div>
      <SectionHeader title="供應商評鑑管理（MP-10）" count={suppliers.length} color="#06b6d4" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="供應商總數" value={suppliers.length} color="#06b6d4" />
        <StatCard label="優良" value={enriched.filter(s=>s.evalResult==="優良").length} color="#22c55e" />
        <StatCard label="條件合格" value={enriched.filter(s=>s.evalResult==="條件合格").length} color="#eab308" />
        <StatCard label="評鑑逾期" value={enriched.filter(s=>s.days<0).length} color="#ef4444" />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {enriched.map(s => (
          <div key={s.id} style={{ background: urgencyBg(s.days), border: `1px solid ${urgencyColor(s.days)}33`, borderRadius: 12, padding: "16px 18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: s.issues.length>0?10:0 }}>
              <div style={{ flex: 1, minWidth: 200 }}>
                <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 14 }}>{s.name}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{s.id} · {s.category} · 聯絡人：{s.contact}</div>
              </div>
              <div style={{ textAlign: "right", minWidth: 90 }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: scoreColor(s.evalScore), fontFamily: "monospace" }}>{s.evalScore}</div>
                <div style={{ fontSize: 11, color: "#64748b" }}>分</div>
              </div>
              <Badge color={s.evalResult==="優良"?"#22c55e":s.evalResult==="合格"?"#60a5fa":s.evalResult==="條件合格"?"#eab308":"#ef4444"}>{s.evalResult}</Badge>
              <div style={{ textAlign: "right", minWidth: 120 }}>
                <div style={{ fontSize: 12, color: "#64748b" }}>下次評鑑</div>
                <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 13 }}>{formatDate(s.nextEvalDate)}</div>
              </div>
              <Badge color={urgencyColor(s.days)}>{urgencyLabel(s.days)}</Badge>
              <button onClick={() => { setModal(s); setForm({ date: new Date().toISOString().split("T")[0], score: s.evalScore }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>更新評鑑</button>
            </div>
            {s.issues.length>0 && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <span style={{ fontSize: 11, color: "#ef4444", fontWeight: 600 }}>問題項目：</span>
                {s.issues.map((issue,i) => (<span key={i} style={{ fontSize: 11, background: "rgba(239,68,68,0.1)", color: "#f87171", borderRadius: 6, padding: "2px 8px", border: "1px solid rgba(239,68,68,0.2)" }}>{issue}</span>))}
              </div>
            )}
          </div>
        ))}
      </div>
      {modal && (<Modal title={`更新評鑑：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑日期</div><input type="date" value={form.date} onChange={e=>setForm({...form,date:e.target.value})} style={inputStyle} /></div><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>評鑑總分 (0-100)</div><input type="number" min="0" max="100" value={form.score} onChange={e=>setForm({...form,score:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(6,182,212,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#22d3ee", fontWeight: 600 }}>評定等級：{parseInt(form.score)>=90?"優良":parseInt(form.score)>=80?"合格":parseInt(form.score)>=70?"條件合格":"不合格"}</div><div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>90+優良 / 80-89合格 / 70-79條件合格 / 69以下不合格</div></div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #0891b2, #06b6d4)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認更新評鑑</button></div></Modal>)}
    </div>
  );
}
