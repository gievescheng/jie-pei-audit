// ─── CALIBRATION TAB ─────────────────────────────────────────────────────────
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
  }
  return (
    <div>
      <SectionHeader title="量規儀器校正追蹤" count={enriched.length} color="#60a5fa" />
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <StatCard label="逾期" value={enriched.filter(i => i.days < 0).length} color="#ef4444" />
        <StatCard label="14天內到期" value={enriched.filter(i => i.days >= 0 && i.days <= 14).length} color="#f97316" />
        <StatCard label="正常" value={enriched.filter(i => i.days > 30).length} color="#22c55e" />
        <StatCard label="免校正" value={enriched.filter(i => i.status === "免校正").length} color="#6366f1" />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {enriched.map(inst => inst.status === "免校正" ? (
          <div key={inst.id} style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontWeight: 700, color: "#c7d2fe", fontSize: 14 }}>{inst.name}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{inst.id} · {inst.location}</div>
            </div>
            <Badge color="#6366f1">免校正</Badge>
          </div>
        ) : (
          <div key={inst.id} style={{ background: urgencyBg(inst.days), border: `1px solid ${urgencyColor(inst.days)}33`, borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 14 }}>{inst.name}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{inst.id} · {inst.location} · {inst.type}{inst.needsMSA && <span style={{ marginLeft: 8, color: "#818cf8", fontWeight: 700 }}>需 MSA</span>}</div>
            </div>
            <div style={{ textAlign: "right", minWidth: 120 }}>
              <div style={{ fontSize: 12, color: "#64748b" }}>下次校正</div>
              <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: 14 }}>{formatDate(inst.nextDate)}</div>
            </div>
            <Badge color={urgencyColor(inst.days)}>{urgencyLabel(inst.days)}</Badge>
            <button onClick={() => { setModal(inst); setForm({ date: new Date().toISOString().split("T")[0] }); }} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", borderRadius: 8, color: "#94a3b8", cursor: "pointer", padding: "6px 14px", fontSize: 12, fontWeight: 600 }}>更新校正</button>
          </div>
        ))}
      </div>
      {modal && (
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
}
