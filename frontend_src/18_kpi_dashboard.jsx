// ─── KPI DASHBOARD ───────────────────────────────────────────────────────────

function KpiDashboard({ instruments, suppliers, nonConformances, auditPlans, envRecords, prodRecords, qualityRecords }) {
  const safeArr = v => (Array.isArray(v) ? v : []);
  const prods    = safeArr(prodRecords);
  const ncs      = safeArr(nonConformances);
  const envs     = safeArr(envRecords);
  const supps    = safeArr(suppliers);
  const audits   = safeArr(auditPlans);
  const qrs      = safeArr(qualityRecords);

  // ── SPC Cpk（從歷史記錄 API 抓最新一筆）──────────────────────
  const [latestCpk, setLatestCpk] = useState(null);
  useEffect(() => {
    fetch("/api/spc/history")
      .then(r => r.json())
      .then(d => {
        const items = d.items || [];
        if (items.length > 0) setLatestCpk({ thickness: items[0].thickness_cpk, ttv: items[0].ttv_cpk, batch: items[0].batch_id });
      })
      .catch(() => {});
  }, []);

  // ── 良品率折線 ──────────────────────────────────────────────
  const yieldData = prods.map(r => ({
    label: (r.lot || "").length >= 11 ? (r.lot || "").substring(7, 11) : (r.lot || "").substring(0, 6) || "?",
    value: parseFloat(r.yieldRate) || 0,
  }));
  const avgYield = yieldData.length > 0
    ? (yieldData.reduce((s, d) => s + d.value, 0) / yieldData.length).toFixed(1) : null;

  // ── NC 月度柱狀 ─────────────────────────────────────────────
  const ncByMonth = {};
  ncs.forEach(nc => {
    const m = (nc.date || "").substring(0, 7) || "未知";
    ncByMonth[m] = (ncByMonth[m] || 0) + 1;
  });
  const ncMonthData = Object.entries(ncByMonth).sort().slice(-6)
    .map(([k, v]) => ({ label: k.substring(5) + "月", value: v }));
  const openNc = ncs.filter(n => n.status !== "已關閉").length;

  // ── 環境合格率（粒子計數器 Model 9303）──────────────────────
  const envParticleTotal  = ENV_PARTICLE_DATA.length;
  const envParticlePass   = ENV_PARTICLE_DATA.filter(ENV_PARTICLE_OK).length;
  const envPassRate = Math.round(envParticlePass / envParticleTotal * 100);
  // 各月合格率 for mini bar chart
  const envMonthBars = ["2025-11","2025-12","2026-01","2026-02","2026-03"].map(m => {
    const mrs = ENV_PARTICLE_DATA.filter(r => r.date.startsWith(m));
    const mp  = mrs.filter(ENV_PARTICLE_OK).length;
    return { label: m.slice(2,4)+"/"+m.slice(5), value: mrs.length > 0 ? Math.round(mp/mrs.length*100) : 0 };
  });

  // ── 供應商 ──────────────────────────────────────────────────
  const avgSupplierScore = supps.length > 0
    ? (supps.reduce((s, x) => s + (parseFloat(x.score) || 0), 0) / supps.length).toFixed(0) : null;

  // ── 稽核完成率 ──────────────────────────────────────────────
  const auditTotal = audits.length;
  const auditDone  = audits.filter(a => a.status === "已完成").length;
  const auditRate  = auditTotal > 0 ? Math.round(auditDone / auditTotal * 100) : null;
  const auditSlices = [
    { label: "已完成", value: auditDone,                                               color: "#22c55e" },
    { label: "進行中", value: audits.filter(a => a.status === "進行中").length,         color: "#3b82f6" },
    { label: "計畫中", value: audits.filter(a => a.status === "計畫中").length,         color: "#6366f1" },
    { label: "逾期",   value: audits.filter(a => a.status === "逾期").length,           color: "#ef4444" },
  ].filter(s => s.value > 0);

  // ── 不良原因 Pareto ─────────────────────────────────────────
  const defectCount = {};
  prods.forEach(r => (r.defectReasons || []).forEach(reason => { defectCount[reason] = (defectCount[reason] || 0) + 1; }));
  const paretoData = Object.entries(defectCount).sort((a, b) => b[1] - a[1]).slice(0, 6)
    .map(([k, v]) => ({ label: k.length > 8 ? k.substring(0, 8) + "…" : k, value: v }));

  // ── 進料合格率 ──────────────────────────────────────────────
  const qcTotal = qrs.length;
  const qcPass  = qrs.filter(r => (r.result || "").toUpperCase() === "PASS").length;
  const qcRate  = qcTotal > 0 ? Math.round(qcPass / qcTotal * 100) : null;

  // ── KPI hero cards ──────────────────────────────────────────
  const heroCards = [
    {
      label: "平均良品率",
      value: avgYield !== null ? avgYield + "%" : "–",
      color: avgYield === null ? "#475569" : parseFloat(avgYield) >= 98 ? "#22c55e" : parseFloat(avgYield) >= 95 ? "#f59e0b" : "#ef4444",
      desc:  `${prods.length} 批次`,
    },
    {
      label: "未關閉不符合",
      value: openNc,
      color: openNc === 0 ? "#22c55e" : openNc <= 3 ? "#f59e0b" : "#ef4444",
      desc:  `合計 ${ncs.length} 項`,
    },
    {
      label: "環境合格率",
      value: envPassRate + "%",
      color: envPassRate >= 90 ? "#22c55e" : envPassRate >= 80 ? "#f59e0b" : "#ef4444",
      desc:  `粒子計數 ${envParticleTotal} 筆`,
    },
    {
      label: "供應商平均分",
      value: avgSupplierScore !== null ? avgSupplierScore : "–",
      color: avgSupplierScore === null ? "#475569" : parseFloat(avgSupplierScore) >= 85 ? "#22c55e" : parseFloat(avgSupplierScore) >= 70 ? "#f59e0b" : "#ef4444",
      desc:  `${supps.length} 家`,
    },
    {
      label: "稽核完成率",
      value: auditRate !== null ? auditRate + "%" : "–",
      color: auditRate === null ? "#475569" : auditRate >= 80 ? "#22c55e" : auditRate >= 50 ? "#f59e0b" : "#ef4444",
      desc:  `${auditDone}/${auditTotal} 場`,
    },
    {
      label: "進料合格率",
      value: qcRate !== null ? qcRate + "%" : "–",
      color: qcRate === null ? "#475569" : qcRate >= 95 ? "#22c55e" : qcRate >= 80 ? "#f59e0b" : "#ef4444",
      desc:  `${qcTotal} 批`,
    },
    {
      label: "Thickness Cpk",
      value: latestCpk && latestCpk.thickness != null ? latestCpk.thickness.toFixed(2) : "–",
      color: !latestCpk || latestCpk.thickness == null ? "#475569"
        : latestCpk.thickness >= 1.33 ? "#22c55e"
        : latestCpk.thickness >= 1.00 ? "#f59e0b" : "#ef4444",
      desc: latestCpk ? latestCpk.batch : "尚無 SPC 記錄",
    },
    {
      label: "TTV Cpk",
      value: latestCpk && latestCpk.ttv != null ? latestCpk.ttv.toFixed(2) : "–",
      color: !latestCpk || latestCpk.ttv == null ? "#475569"
        : latestCpk.ttv >= 1.33 ? "#22c55e"
        : latestCpk.ttv >= 1.00 ? "#f59e0b" : "#ef4444",
      desc: latestCpk ? latestCpk.batch : "尚無 SPC 記錄",
    },
  ];

  const panel = (children, style = {}) => (
    <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:20, ...style }}>
      {children}
    </div>
  );
  const sectionTitle = t => <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>{t}</div>;

  return (
    <div>
      {/* ── 標題 ── */}
      <div style={{ marginBottom:24 }}>
        <div style={{ fontSize:20, fontWeight:800, color:"#e2e8f0" }}>生產績效儀表板</div>
        <div style={{ fontSize:13, color:"#64748b", marginTop:4 }}>
          高階主管視圖 — {new Date().toLocaleString("zh-TW", { year:"numeric", month:"long", day:"numeric", hour:"2-digit", minute:"2-digit" })}
        </div>
      </div>

      {/* ── Hero KPI 卡片 ── */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(150px, 1fr))", gap:12, marginBottom:20 }}>
        {heroCards.map(k => (
          <div key={k.label} style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${k.color}30`, borderRadius:14, padding:"18px 16px" }}>
            <div style={{ fontSize:28, fontWeight:800, color:k.color, lineHeight:1 }}>{k.value}</div>
            <div style={{ fontSize:12, color:"#94a3b8", marginTop:6 }}>{k.label}</div>
            <div style={{ fontSize:11, color:"#475569", marginTop:3 }}>{k.desc}</div>
          </div>
        ))}
      </div>

      {/* ── 環境粒子計數監控 ── */}
      <EnvParticlePanel />

      {/* ── 玻璃基板良率監控 ── */}
      <GlassYieldPanel />

      {/* ── 第一排：良品率 + NC 月度 ── */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16, marginTop:24 }}>
        {panel(<>
          {sectionTitle("批次良品率趨勢（%）")}
          <SvgLineChart data={yieldData} color="#22c55e" domainMin={90} domainMax={100} />
        </>)}
        {panel(<>
          {sectionTitle("不符合項月度件數")}
          {ncMonthData.length === 0
            ? <div style={{ color:"#475569", fontSize:12 }}>尚無不符合記錄</div>
            : <SvgBarChart data={ncMonthData} color="#f59e0b" />
          }
        </>)}
      </div>

      {/* ── 第二排：粒子計數月合格率 + Pareto ── */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:16 }}>
        {panel(<>
          {sectionTitle("粒子計數月合格率（%）")}
          <SvgBarChart data={envMonthBars} color="#38bdf8" />
          <div style={{ fontSize:11, color:"#64748b", marginTop:4 }}>{"Model 9303 · Ch1/Ch2≥500或Ch3>10超標"}</div>
        </>)}
        {panel(<>
          {sectionTitle("不良原因 Pareto（件）")}
          {paretoData.length === 0
            ? <div style={{ color:"#475569", fontSize:12 }}>尚無不良原因記錄</div>
            : <SvgBarChart data={paretoData} color="#ef4444" />
          }
        </>)}
      </div>

      {/* ── 第三排：供應商橫條 + 稽核圓環 ── */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:16 }}>
        {panel(<>
          {sectionTitle("供應商評分一覽")}
          <div style={{ display:"flex", flexDirection:"column", gap:9 }}>
            {supps.length === 0 && <div style={{ color:"#475569", fontSize:12 }}>尚無供應商記錄</div>}
            {supps.slice(0, 8).map(s => {
              const score = parseFloat(s.score) || 0;
              const barColor = score >= 85 ? "#22c55e" : score >= 70 ? "#f59e0b" : "#ef4444";
              return (
                <div key={s.id || s.name} style={{ display:"flex", alignItems:"center", gap:10 }}>
                  <div style={{ fontSize:12, color:"#94a3b8", width:72, flexShrink:0, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{s.name || "–"}</div>
                  <div style={{ flex:1, background:"rgba(255,255,255,0.05)", borderRadius:4, height:10, overflow:"hidden" }}>
                    <div style={{ width:score + "%", height:"100%", background:barColor, borderRadius:4, transition:"width 0.6s ease" }} />
                  </div>
                  <div style={{ fontSize:12, fontWeight:700, color:barColor, width:28, textAlign:"right", flexShrink:0 }}>{score}</div>
                </div>
              );
            })}
          </div>
        </>)}
        {panel(<>
          {sectionTitle("稽核計畫完成率")}
          {auditSlices.length === 0
            ? <div style={{ color:"#475569", fontSize:12 }}>尚無稽核計畫</div>
            : (
              <div style={{ display:"flex", alignItems:"center", gap:20 }}>
                <SvgDonut slices={auditSlices} size={110} />
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  {[
                    { label:"已完成", color:"#22c55e", count: auditDone },
                    { label:"進行中", color:"#3b82f6", count: audits.filter(a => a.status === "進行中").length },
                    { label:"計畫中", color:"#6366f1", count: audits.filter(a => a.status === "計畫中").length },
                    { label:"逾期",   color:"#ef4444", count: audits.filter(a => a.status === "逾期").length },
                  ].map(item => (
                    <div key={item.label} style={{ display:"flex", alignItems:"center", gap:6 }}>
                      <div style={{ width:8, height:8, borderRadius:"50%", background:item.color, flexShrink:0 }} />
                      <div style={{ fontSize:11, color:"#94a3b8" }}>{item.label}</div>
                      <div style={{ fontSize:12, fontWeight:700, color:item.color, marginLeft:"auto", paddingLeft:8 }}>{item.count}</div>
                    </div>
                  ))}
                  <div style={{ fontSize:13, fontWeight:800, color: auditRate !== null ? (auditRate >= 80 ? "#22c55e" : auditRate >= 50 ? "#f59e0b" : "#ef4444") : "#475569", marginTop:4, borderTop:"1px solid rgba(255,255,255,0.07)", paddingTop:6 }}>
                    完成率 {auditRate !== null ? auditRate + "%" : "–"}
                  </div>
                </div>
              </div>
            )
          }
        </>)}
      </div>
    </div>
  );
}
