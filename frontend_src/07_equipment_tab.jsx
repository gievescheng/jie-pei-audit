// ─── EQUIPMENT TAB ────────────────────────────────────────────────────────────
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
  }
  return (
    <div>
      <SectionHeader title="設備保養追蹤" count={equipment.length} color="#fb923c" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="逾期保養" value={enriched.filter(e=>e.days<0).length} color="#ef4444" />
        <StatCard label="本月到期" value={enriched.filter(e=>e.days>=0&&e.days<=30).length} color="#f97316" />
        <StatCard label="正常" value={enriched.filter(e=>e.days>30).length} color="#22c55e" />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {enriched.map(eq => (
          <div key={eq.id} style={{ background: urgencyBg(eq.days), border: `1px solid ${urgencyColor(eq.days)}33`, borderRadius: 12, padding: "16px 18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: 10 }}>
              <div style={{ flex: 1, minWidth: 200 }}><div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 14 }}>{eq.name}</div><div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{eq.id} · {eq.location} · 每 {eq.intervalDays} 天保養一次</div></div>
              <div style={{ textAlign: "right", minWidth: 120 }}><div style={{ fontSize: 12, color: "#64748b" }}>下次保養</div><div style={{ fontWeight: 700, color: "#e2e8f0" }}>{formatDate(eq.nextDate)}</div></div>
              <Badge color={urgencyColor(eq.days)}>{urgencyLabel(eq.days)}</Badge>
              <button onClick={() => { setModal(eq); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12 }}>記錄保養</button>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>保養項目：</span>
              {eq.nextItems.map((item,i) => (<span key={i} style={{ fontSize: 11, background: "rgba(251,146,60,0.1)", color: "#fb923c", borderRadius: 6, padding: "2px 8px", border: "1px solid rgba(251,146,60,0.2)" }}>{item}</span>))}
            </div>
          </div>
        ))}
      </div>
      {modal && (<Modal title={`記錄保養完成：${modal.name}`} onClose={() => setModal(null)}><div style={{ display: "flex", flexDirection: "column", gap: 16 }}><div><div style={{ fontSize: 12, color: "#64748b", marginBottom: 6 }}>保養完成日期</div><input type="date" value={form.date} onChange={e => setForm({...form,date:e.target.value})} style={inputStyle} /></div><div style={{ background: "rgba(251,146,60,0.1)", borderRadius: 8, padding: 12 }}><div style={{ fontSize: 12, color: "#fb923c", fontWeight: 600, marginBottom: 8 }}>本次保養項目：</div>{modal.nextItems.map((item,i) => (<div key={i} style={{ color: "#fed7aa", fontSize: 13, marginBottom: 4 }}>☑ {item}</div>))}</div><button onClick={handleUpdate} style={{ background: "linear-gradient(135deg, #ea580c, #f97316)", border: "none", borderRadius: 10, color: "#fff", cursor: "pointer", padding: "12px 24px", fontSize: 15, fontWeight: 700 }}>✓ 確認保養完成</button></div></Modal>)}
    </div>
  );
}
