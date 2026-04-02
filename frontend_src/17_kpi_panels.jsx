// ─── ENV PARTICLE COUNTER PANEL ──────────────────────────────────────────────

function EnvParticlePanel() {
  const MONTHS = ["2025-11","2025-12","2026-01","2026-02","2026-03"];
  const MONTH_LABEL = { "2025-11":"25/11月","2025-12":"25/12月","2026-01":"26/01月","2026-02":"26/02月","2026-03":"26/03月" };

  // Monthly aggregation
  const mStats = {};
  MONTHS.forEach(m => { mStats[m] = { runs:0, passes:0, ch1sum:0, ch1n:0, ch1maxAll:0, ch3sum:0 }; });
  ENV_PARTICLE_DATA.forEach(r => {
    const m = r.date.substring(0, 7);
    if (!mStats[m]) return;
    const ok = ENV_PARTICLE_OK(r);
    mStats[m].runs++;
    if (ok) { mStats[m].passes++; mStats[m].ch1sum += r.ch1avg; mStats[m].ch1n++; mStats[m].ch3sum += r.ch3avg; }
    if (r.ch1max > mStats[m].ch1maxAll) mStats[m].ch1maxAll = r.ch1max;
  });

  const totalRuns   = ENV_PARTICLE_DATA.length;
  const totalPasses = ENV_PARTICLE_DATA.filter(ENV_PARTICLE_OK).length;
  const passRate    = Math.round(totalPasses / totalRuns * 100);
  const highEvents  = ENV_PARTICLE_DATA.filter(r => !ENV_PARTICLE_OK(r));
  const latestRun   = ENV_PARTICLE_DATA[ENV_PARTICLE_DATA.length - 1];

  const pctCol = v => v >= 95 ? "#22c55e" : v >= 85 ? "#f59e0b" : "#ef4444";

  const panel = (children, style = {}) => (
    <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:20, ...style }}>
      {children}
    </div>
  );
  const secTitle = t => <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>{t}</div>;

  // Monthly pass rate bar chart (inline SVG)
  const MonthPassBars = () => {
    const W=400, H=130, pL=8, pR=8, pT=16, pB=28;
    const iW=W-pL-pR, iH=H-pT-pB;
    const data = MONTHS.map(m => ({ label: MONTH_LABEL[m], pct: mStats[m].runs > 0 ? Math.round(mStats[m].passes/mStats[m].runs*100) : 0, runs: mStats[m].runs }));
    const slotW = iW / data.length;
    const barW  = Math.max(slotW - 10, 8);
    return (
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow:"visible", display:"block" }}>
        {[80,90,100].map(v => {
          const y = pT + iH - (v/100)*iH;
          return <g key={v}><line x1={pL} y1={y} x2={pL+iW} y2={y} stroke="rgba(255,255,255,0.05)" /><text x={pL-3} y={y+4} textAnchor="end" fill="#475569" fontSize={8}>{v}</text></g>;
        })}
        {data.map((d, i) => {
          const barH = Math.round(d.pct / 100 * iH);
          const x = pL + i * slotW + (slotW - barW) / 2;
          const y = pT + iH - barH;
          const col = pctCol(d.pct);
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={barH} rx={3} fill={col} opacity={0.85} />
              <text x={x+barW/2} y={y-3} textAnchor="middle" fill="#cbd5e1" fontSize={9}>{d.pct}%</text>
              <text x={x+barW/2} y={H-4} textAnchor="middle" fill="#475569" fontSize={8}>{d.label}</text>
            </g>
          );
        })}
      </svg>
    );
  };

  // Ch1 monthly average of normal runs (line chart)
  const Ch1AvgLine = () => {
    const pts = MONTHS.map(m => ({ label: MONTH_LABEL[m], v: mStats[m].ch1n > 0 ? Math.round(mStats[m].ch1sum / mStats[m].ch1n * 10) / 10 : 0 }));
    const maxV = Math.max(...pts.map(p => p.v), 1);
    const W=340, H=110, pL=32, pR=8, pT=14, pB=24;
    const iW=W-pL-pR, iH=H-pT-pB;
    const xStep = iW / (pts.length - 1);
    const pArr = pts.map((p, i) => ({ x: pL + i * xStep, y: pT + iH - (p.v / maxV) * iH, ...p }));
    const path = pArr.map((p, i) => `${i===0?"M":"L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    return (
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow:"visible", display:"block" }}>
        {[0,0.5,1].map(f => {
          const y = pT+iH-f*iH; const v = (f*maxV).toFixed(0);
          return <g key={f}><line x1={pL} y1={y} x2={pL+iW} y2={y} stroke="rgba(255,255,255,0.05)" /><text x={pL-4} y={y+4} textAnchor="end" fill="#475569" fontSize={8}>{v}</text></g>;
        })}
        <path d={path} fill="none" stroke="#38bdf8" strokeWidth={2} strokeLinejoin="round" />
        {pArr.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r={3} fill="#38bdf8" />
            <text x={p.x} y={p.y-6} textAnchor="middle" fill="#cbd5e1" fontSize={8}>{p.v}</text>
            <text x={p.x} y={H-4} textAnchor="middle" fill="#475569" fontSize={7.5}>{p.label}</text>
          </g>
        ))}
      </svg>
    );
  };

  return (
    <div style={{ marginTop:24 }}>
      {/* Section header */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:14 }}>
        <div>
          <div style={{ fontSize:15, fontWeight:800, color:"#e2e8f0" }}>潔淨室粒子計數監控</div>
          <div style={{ fontSize:12, color:"#64748b", marginTop:2 }}>
            Model 9303 · 0.3µm / 0.5µm / 5.0µm · 2025年11月 ～ 2026年03月 · 共 {totalRuns} 筆 Run
          </div>
        </div>
        <div style={{ fontSize:11, color:"#94a3b8", background:"rgba(56,189,248,0.08)", border:"1px solid rgba(56,189,248,0.2)", borderRadius:6, padding:"4px 10px" }}>
          超標：Ch1/Ch2 ≥ 500 或 Ch3 {">"} 10
        </div>
      </div>

      {/* KPI cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:12, marginBottom:14 }}>
        {[
          { label:"量測 Run 總數",   value: totalRuns + " 筆", color:"#38bdf8",  desc:"Model 9303 單點" },
          { label:"正常 Run 合格率", value: passRate + "%",    color: pctCol(passRate), desc:`${totalPasses} / ${totalRuns} 筆正常` },
          { label:"最新 Run Ch1均值",value: latestRun.ch1avg + " ct/m³", color: latestRun.ch1avg > 100 ? "#f59e0b" : "#22c55e", desc:`${latestRun.date} ${latestRun.session}` },
          { label:"超標事件總計",    value: highEvents.length + " 次",  color: highEvents.length === 0 ? "#22c55e" : highEvents.length <= 5 ? "#f59e0b" : "#ef4444", desc:"2025/11 ~ 2026/03" },
        ].map(k => (
          <div key={k.label} style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${k.color}28`, borderRadius:12, padding:"14px 14px" }}>
            <div style={{ fontSize:22, fontWeight:800, color:k.color, lineHeight:1 }}>{k.value}</div>
            <div style={{ fontSize:11, color:"#94a3b8", marginTop:5 }}>{k.label}</div>
            <div style={{ fontSize:10, color:"#475569", marginTop:2 }}>{k.desc}</div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:14 }}>
        {panel(<>
          {secTitle("月合格率（%）—各月正常Run佔比")}
          <MonthPassBars />
        </>)}
        {panel(<>
          {secTitle("月均 Ch1 (0.3µm) — 正常Run平均值")}
          <Ch1AvgLine />
          <div style={{ fontSize:11, color:"#64748b", marginTop:6 }}>僅計入正常Run（排除超標筆），單位：counts/m³</div>
        </>)}
      </div>

      {/* Monthly summary table */}
      {panel(<>
        {secTitle("各月統計摘要")}
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
          <thead>
            <tr style={{ background:"rgba(255,255,255,0.04)" }}>
              {["月份","Run數","正常","超標","合格率","Ch1均值(正常)","Ch1最大值","Ch3均值(正常)"].map(h => (
                <th key={h} style={{ padding:"7px 12px", textAlign: h==="月份"?"left":"right", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.07)", whiteSpace:"nowrap" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {MONTHS.map((m, i) => {
              const s = mStats[m];
              const pr = s.runs > 0 ? Math.round(s.passes/s.runs*100) : 0;
              const ch1n = s.ch1n > 0 ? (s.ch1sum/s.ch1n).toFixed(1) : "–";
              const ch3n = s.ch1n > 0 ? (s.ch3sum/s.ch1n).toFixed(2) : "–";
              const col  = pctCol(pr);
              return (
                <tr key={m} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", background: i%2===0?"transparent":"rgba(255,255,255,0.015)" }}>
                  <td style={{ padding:"6px 12px", color:"#e2e8f0", fontWeight:600 }}>{MONTH_LABEL[m]}</td>
                  <td style={{ padding:"6px 12px", color:"#94a3b8", textAlign:"right" }}>{s.runs}</td>
                  <td style={{ padding:"6px 12px", color:"#22c55e", textAlign:"right", fontWeight:600 }}>{s.passes}</td>
                  <td style={{ padding:"6px 12px", color: s.runs-s.passes>0?"#ef4444":"#64748b", textAlign:"right" }}>{s.runs-s.passes}</td>
                  <td style={{ padding:"6px 12px", textAlign:"right" }}><span style={{ fontWeight:700, color:col }}>{pr}%</span></td>
                  <td style={{ padding:"6px 12px", color:"#94a3b8", textAlign:"right" }}>{ch1n}</td>
                  <td style={{ padding:"6px 12px", color: s.ch1maxAll>=500?"#ef4444":"#64748b", textAlign:"right", fontWeight: s.ch1maxAll>=500?700:400 }}>{s.ch1maxAll.toLocaleString()}</td>
                  <td style={{ padding:"6px 12px", color:"#64748b", textAlign:"right" }}>{ch3n}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </>, { marginBottom:14 })}

      {/* High-value events */}
      {highEvents.length > 0 && panel(<>
        {secTitle(`超標事件明細（共 ${highEvents.length} 筆）`)}
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
            <thead>
              <tr style={{ background:"rgba(255,255,255,0.04)" }}>
                {["日期","Run","時段","Ch1最大","Ch2最大","Ch3最大","超標原因","備註"].map(h => (
                  <th key={h} style={{ padding:"6px 10px", textAlign: h==="日期"||h==="時段"||h==="超標原因"||h==="備註"?"left":"right", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.07)", whiteSpace:"nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {highEvents.map((r, i) => {
                const reasons = [];
                if (r.ch1max >= 500) reasons.push(`Ch1=${r.ch1max.toLocaleString()}`);
                if (r.ch2max >= 500) reasons.push(`Ch2=${r.ch2max.toLocaleString()}`);
                if (r.ch3max > 10)   reasons.push(`Ch3=${r.ch3max}`);
                return (
                  <tr key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", background: i%2===0?"transparent":"rgba(255,255,255,0.015)" }}>
                    <td style={{ padding:"5px 10px", color:"#e2e8f0" }}>{r.date}</td>
                    <td style={{ padding:"5px 10px", color:"#94a3b8", textAlign:"right" }}>{r.run}</td>
                    <td style={{ padding:"5px 10px", color:"#94a3b8" }}>{r.session}</td>
                    <td style={{ padding:"5px 10px", color: r.ch1max>=500?"#ef4444":"#94a3b8", textAlign:"right", fontWeight: r.ch1max>=500?700:400 }}>{r.ch1max.toLocaleString()}</td>
                    <td style={{ padding:"5px 10px", color: r.ch2max>=500?"#ef4444":"#94a3b8", textAlign:"right", fontWeight: r.ch2max>=500?700:400 }}>{r.ch2max.toLocaleString()}</td>
                    <td style={{ padding:"5px 10px", color: r.ch3max>10?"#f59e0b":"#94a3b8",  textAlign:"right", fontWeight: r.ch3max>10?700:400 }}>{r.ch3max}</td>
                    <td style={{ padding:"5px 10px", color:"#ef4444", fontSize:11 }}>{reasons.join(" / ")}</td>
                    <td style={{ padding:"5px 10px", color:"#6366f1", fontSize:11 }}>{r.note || ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </>)}
    </div>
  );
}

// ─── GLASS WAFER YIELD PANEL ─────────────────────────────────────────────────

function GlassYieldPanel() {
  const TANK_WARN = 5000;
  const TANK_MAX  = 10000;

  const data = GLASS_YIELD_DATA.map(r => ({
    ...r,
    fy: r.toWash > 0 ? Math.round(r.ok / r.toWash * 1000) / 10 : null,
  }));

  const withFy      = data.filter(r => r.fy !== null);
  const avgYield    = withFy.length > 0
    ? (withFy.reduce((s, r) => s + r.fy, 0) / withFy.length).toFixed(1) : null;
  const latestRow   = data[data.length - 1];
  const worstBatch  = withFy.length > 0
    ? withFy.reduce((w, r) => r.fy < w.fy ? r : w) : null;
  const totalWash   = data.reduce((s, r) => s + r.toWash, 0);
  const totalOk     = data.reduce((s, r) => s + r.ok, 0);
  const overallFy   = totalWash > 0 ? (totalOk / totalWash * 100).toFixed(1) : null;

  const fyColor = v => v === null ? "#475569" : v >= 93 ? "#22c55e" : v >= 85 ? "#f59e0b" : "#ef4444";

  const panel = (children, style = {}) => (
    <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:20, ...style }}>
      {children}
    </div>
  );
  const secTitle = t => (
    <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>{t}</div>
  );

  // Yield bar chart — SVG, custom color per bar
  const YieldBars = () => {
    const W = 560, H = 170, padL = 32, padR = 8, padT = 20, padB = 42;
    const innerW = W - padL - padR;
    const innerH = H - padT - padB;
    const domMin = 75, domMax = 100, domRange = domMax - domMin;
    const slotW  = innerW / data.length;
    const barW   = Math.max(slotW - 5, 4);
    const toY    = v => padT + innerH - Math.round(Math.max(v - domMin, 0) / domRange * innerH);
    return (
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow:"visible", display:"block" }}>
        {[75, 80, 85, 90, 95, 100].map(v => {
          const y = toY(v);
          return (
            <g key={v}>
              <line x1={padL} y1={y} x2={padL + innerW} y2={y} stroke="rgba(255,255,255,0.05)" />
              <text x={padL - 4} y={y + 4} textAnchor="end" fill="#475569" fontSize={8}>{v}</text>
            </g>
          );
        })}
        {/* 93 % threshold line */}
        {(() => { const y = toY(93); return <line x1={padL} y1={y} x2={padL+innerW} y2={y} stroke="rgba(34,197,94,0.25)" strokeDasharray="4 3" />; })()}
        {data.map((r, i) => {
          const fy = r.fy !== null ? r.fy : 0;
          const col = r.fy !== null ? fyColor(fy) : "#334155";
          const barH = Math.max(Math.round(Math.max(fy - domMin, 0) / domRange * innerH), 2);
          const x   = padL + i * slotW + (slotW - barW) / 2;
          const y   = padT + innerH - barH;
          const labelY = padT + innerH + 12;
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={barH} rx={2} fill={col} opacity={0.85} />
              {r.fy !== null && (
                <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill="#cbd5e1" fontSize={7.5}>{fy.toFixed(1)}</text>
              )}
              <text
                x={x + barW / 2} y={labelY}
                textAnchor="end"
                fill="#475569" fontSize={7.5}
                transform={`rotate(-40, ${x + barW / 2}, ${labelY})`}
              >{r.name}</text>
              {r.note && (
                <text x={x + barW / 2} y={padT + innerH + 30} textAnchor="middle" fill="#6366f1" fontSize={7}>↑</text>
              )}
            </g>
          );
        })}
      </svg>
    );
  };

  return (
    <div style={{ marginTop:24 }}>
      {/* Section header */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:14 }}>
        <div>
          <div style={{ fontSize:15, fontWeight:800, color:"#e2e8f0" }}>玻璃基板清洗良率監控</div>
          <div style={{ fontSize:12, color:"#64748b", marginTop:2 }}>
            RECYCLE GLASS NEG ABC-1（JEPE）· 2026年01月～03月 · 共 {data.length} 批
          </div>
        </div>
        <div style={{ fontSize:11, color:"#94a3b8", background:"rgba(99,102,241,0.1)", border:"1px solid rgba(99,102,241,0.25)", borderRadius:6, padding:"4px 10px" }}>
          ⓘ 僅顯示原始良率（不含重工）
        </div>
      </div>

      {/* KPI mini-cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4, 1fr)", gap:12, marginBottom:14 }}>
        {[
          {
            label:"整體原始良率", desc:`${totalOk.toLocaleString()} / ${totalWash.toLocaleString()} 片`,
            value: overallFy !== null ? overallFy + "%" : "–",
            color: fyColor(overallFy !== null ? parseFloat(overallFy) : null),
          },
          {
            label:"批次平均良率", desc:`${withFy.length} 批計算`,
            value: avgYield !== null ? avgYield + "%" : "–",
            color: fyColor(avgYield !== null ? parseFloat(avgYield) : null),
          },
          {
            label:"最新批次良率", desc:`${latestRow.name}  ${latestRow.period}`,
            value: latestRow.fy !== null ? latestRow.fy + "%" : "–",
            color: fyColor(latestRow.fy),
          },
          {
            label:"最低良率批次",
            desc: worstBatch ? `${worstBatch.name}  ${worstBatch.period}` : "–",
            value: worstBatch ? worstBatch.fy + "%" : "–",
            color: worstBatch ? fyColor(worstBatch.fy) : "#475569",
          },
        ].map(k => (
          <div key={k.label} style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${k.color}28`, borderRadius:12, padding:"14px 14px" }}>
            <div style={{ fontSize:24, fontWeight:800, color:k.color, lineHeight:1 }}>{k.value}</div>
            <div style={{ fontSize:11, color:"#94a3b8", marginTop:5 }}>{k.label}</div>
            <div style={{ fontSize:10, color:"#475569", marginTop:2 }}>{k.desc}</div>
          </div>
        ))}
      </div>

      {/* Chart row: yield bars + tank status */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:14, marginBottom:14 }}>
        {panel(<>
          {secTitle("各批次原始良率（%）")}
          <YieldBars />
          <div style={{ display:"flex", gap:16, marginTop:6, fontSize:11, color:"#64748b" }}>
            <span><span style={{ display:"inline-block", width:8, height:8, borderRadius:2, background:"#22c55e", marginRight:4 }} />≥ 93%</span>
            <span><span style={{ display:"inline-block", width:8, height:8, borderRadius:2, background:"#f59e0b", marginRight:4 }} />85 ~ 93%</span>
            <span><span style={{ display:"inline-block", width:8, height:8, borderRadius:2, background:"#ef4444", marginRight:4 }} />{"< 85%"}</span>
            <span style={{ marginLeft:"auto" }}><span style={{ color:"#6366f1" }}>↑</span> 換藥水</span>
          </div>
        </>)}

        {panel(<>
          {secTitle("藥液槽累積使用量")}
          {[
            { label:"槽 1", value: latestRow.tank1 },
            { label:"槽 2", value: latestRow.tank2 },
          ].map(tank => {
            const pct    = Math.min(tank.value / TANK_MAX * 100, 100);
            const warnPct = TANK_WARN / TANK_MAX * 100;
            const barCol = pct >= 85 ? "#ef4444" : pct >= warnPct ? "#f59e0b" : "#22c55e";
            return (
              <div key={tank.label} style={{ marginBottom:20 }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:5 }}>
                  <div style={{ fontSize:12, color:"#94a3b8", fontWeight:600 }}>{tank.label}</div>
                  <div style={{ fontSize:12, fontWeight:700, color:barCol }}>{tank.value.toLocaleString()} 片</div>
                </div>
                <div style={{ background:"rgba(255,255,255,0.05)", borderRadius:6, height:14, overflow:"hidden", position:"relative" }}>
                  <div style={{ width:pct + "%", height:"100%", background:barCol, borderRadius:6, transition:"width 0.6s ease" }} />
                  <div style={{ position:"absolute", top:0, left:warnPct + "%", height:"100%", width:2, background:"rgba(255,255,255,0.25)" }} />
                </div>
                <div style={{ fontSize:10, color:"#475569", marginTop:4 }}>
                  建議換液 {TANK_WARN.toLocaleString()} 片 · 上限 {TANK_MAX.toLocaleString()} 片
                </div>
              </div>
            );
          })}

          <div style={{ paddingTop:12, borderTop:"1px solid rgba(255,255,255,0.06)" }}>
            {secTitle("NG 件數（近 8 批）")}
            <svg width="100%" viewBox="0 0 220 110" style={{ overflow:"visible", display:"block" }}>
              {(() => {
                const recent = data.slice(-8);
                const maxNg  = Math.max(...recent.map(r => r.ng), 1);
                const W = 220, H = 85, padL = 8, padR = 8, padB = 22, padT = 10;
                const innerW = W - padL - padR, innerH = H - padT - padB;
                const slotW  = innerW / recent.length;
                const barW   = Math.max(slotW - 5, 4);
                return recent.map((r, i) => {
                  const barH = Math.max(Math.round(r.ng / maxNg * innerH), r.ng > 0 ? 2 : 0);
                  const x    = padL + i * slotW + (slotW - barW) / 2;
                  const y    = padT + innerH - barH;
                  const col  = r.ng > 80 ? "#ef4444" : r.ng > 30 ? "#f59e0b" : "#64748b";
                  return (
                    <g key={i}>
                      <rect x={x} y={y} width={barW} height={barH} rx={2} fill={col} opacity={0.85} />
                      {r.ng > 0 && <text x={x + barW/2} y={y - 2} textAnchor="middle" fill="#cbd5e1" fontSize={8}>{r.ng}</text>}
                      <text x={x + barW/2} y={H - 4} textAnchor="middle" fill="#475569" fontSize={7.5}>{r.name.slice(-3)}</text>
                    </g>
                  );
                });
              })()}
            </svg>
          </div>
        </>)}
      </div>

      {/* Batch detail table */}
      {panel(<>
        {secTitle("批次明細（原始良率）")}
        <div style={{ overflowX:"auto" }}>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
            <thead>
              <tr style={{ background:"rgba(255,255,255,0.04)" }}>
                {["批次","日期","投入","OCR 剔","入洗","良品","不良","原始良率","槽1 (片)","槽2 (片)","備註"].map(h => (
                  <th key={h} style={{ padding:"7px 10px", textAlign:"left", color:"#64748b", fontWeight:600, whiteSpace:"nowrap", borderBottom:"1px solid rgba(255,255,255,0.07)" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((r, i) => {
                const fyStr = r.fy !== null ? r.fy.toFixed(1) + "%" : "–";
                const col   = fyColor(r.fy);
                return (
                  <tr key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)" }}>
                    <td style={{ padding:"6px 10px", color:"#e2e8f0", fontWeight:600 }}>{r.name}</td>
                    <td style={{ padding:"6px 10px", color:"#94a3b8", whiteSpace:"nowrap" }}>{r.period}</td>
                    <td style={{ padding:"6px 10px", color:"#94a3b8", textAlign:"right" }}>{r.input}</td>
                    <td style={{ padding:"6px 10px", color:"#64748b", textAlign:"right" }}>{r.ocr || "–"}</td>
                    <td style={{ padding:"6px 10px", color:"#94a3b8", textAlign:"right" }}>{r.toWash}</td>
                    <td style={{ padding:"6px 10px", color:"#22c55e", textAlign:"right", fontWeight:600 }}>{r.ok}</td>
                    <td style={{ padding:"6px 10px", color: r.ng > 80 ? "#ef4444" : r.ng > 30 ? "#f59e0b" : "#94a3b8", textAlign:"right" }}>{r.ng}</td>
                    <td style={{ padding:"6px 10px", textAlign:"right" }}>
                      <span style={{ fontWeight:700, color:col }}>{fyStr}</span>
                    </td>
                    <td style={{ padding:"6px 10px", color:"#64748b", fontSize:11, textAlign:"right" }}>{r.tank1.toLocaleString()}</td>
                    <td style={{ padding:"6px 10px", color:"#64748b", fontSize:11, textAlign:"right" }}>{r.tank2.toLocaleString()}</td>
                    <td style={{ padding:"6px 10px", color:"#6366f1", fontSize:11 }}>{r.note || ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </>)}
    </div>
  );
}

// ─── SVG CHART PRIMITIVES ────────────────────────────────────────────────────

function SvgBarChart({ data, width = 420, height = 150, color = "#3b82f6" }) {
  if (!data || data.length === 0) return <div style={{ color:"#475569", fontSize:12, textAlign:"center", padding:16 }}>尚無資料</div>;
  const max = Math.max(...data.map(d => d.value), 1);
  const padL = 8, padR = 8, padB = 22, padT = 16;
  const innerW = width - padL - padR;
  const innerH = height - padT - padB;
  const slotW = innerW / data.length;
  const barW = Math.max(Math.min(slotW - 6, 36), 6);
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow:"visible", display:"block" }}>
      {[0, 0.5, 1].map(pct => {
        const y = padT + innerH - pct * innerH;
        return <line key={pct} x1={padL} y1={y} x2={padL + innerW} y2={y} stroke="rgba(255,255,255,0.05)" />;
      })}
      {data.map((d, i) => {
        const barH = Math.max(Math.round((d.value / max) * innerH), d.value > 0 ? 2 : 0);
        const x = padL + i * slotW + (slotW - barW) / 2;
        const y = padT + innerH - barH;
        return (
          <g key={i}>
            <rect x={x} y={y} width={barW} height={barH} rx={3} fill={color} opacity={0.85} />
            <text x={x + barW / 2} y={height - 4} textAnchor="middle" fill="#475569" fontSize={9}>{d.label}</text>
            {d.value > 0 && <text x={x + barW / 2} y={y - 3} textAnchor="middle" fill="#cbd5e1" fontSize={9}>{d.value}</text>}
          </g>
        );
      })}
    </svg>
  );
}

function SvgLineChart({ data, width = 420, height = 140, color = "#22c55e", domainMin, domainMax }) {
  if (!data || data.length < 2) return <div style={{ color:"#475569", fontSize:12, textAlign:"center", padding:16 }}>需 2 筆以上資料</div>;
  const vals = data.map(d => d.value);
  const rawMin = domainMin !== undefined ? domainMin : Math.min(...vals);
  const rawMax = domainMax !== undefined ? domainMax : Math.max(...vals);
  const range = rawMax - rawMin || 1;
  const padL = 36, padR = 12, padT = 16, padB = 24;
  const w = width - padL - padR;
  const h = height - padT - padB;
  const xStep = w / (data.length - 1);
  const pts = data.map((d, i) => ({
    x: padL + i * xStep,
    y: padT + h - ((d.value - rawMin) / range) * h,
    label: d.label,
    value: d.value,
  }));
  const linePath = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const areaPath = linePath + ` L ${pts[pts.length - 1].x.toFixed(1)} ${(padT + h).toFixed(1)} L ${pts[0].x.toFixed(1)} ${(padT + h).toFixed(1)} Z`;
  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} style={{ overflow:"visible", display:"block" }}>
      {[0, 0.5, 1].map(pct => {
        const y = padT + h - pct * h;
        const val = rawMin + pct * range;
        return (
          <g key={pct}>
            <line x1={padL} y1={y} x2={padL + w} y2={y} stroke="rgba(255,255,255,0.05)" />
            <text x={padL - 4} y={y + 4} textAnchor="end" fill="#475569" fontSize={8}>{val.toFixed(1)}</text>
          </g>
        );
      })}
      <path d={areaPath} fill={color} opacity={0.08} />
      <path d={linePath} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" />
      {pts.map((p, i) => (
        <g key={i}>
          <circle cx={p.x} cy={p.y} r={3} fill={color} />
          <text x={p.x} y={height - 4} textAnchor="middle" fill="#475569" fontSize={8}>{p.label}</text>
          <text x={p.x} y={p.y - 6} textAnchor="middle" fill="#cbd5e1" fontSize={8}>{p.value.toFixed(1)}</text>
        </g>
      ))}
    </svg>
  );
}

function SvgDonut({ slices, size = 110 }) {
  const total = slices.reduce((s, x) => s + x.value, 0) || 1;
  const cx = size / 2, cy = size / 2, r = size * 0.4, ir = size * 0.27;
  let angle = -Math.PI / 2;
  const paths = slices.map(sl => {
    const sweep = (sl.value / total) * 2 * Math.PI;
    const x1 = cx + r * Math.cos(angle),  y1 = cy + r * Math.sin(angle);
    angle += sweep;
    const x2 = cx + r * Math.cos(angle),  y2 = cy + r * Math.sin(angle);
    const ix1 = cx + ir * Math.cos(angle), iy1 = cy + ir * Math.sin(angle);
    const ix2 = cx + ir * Math.cos(angle - sweep), iy2 = cy + ir * Math.sin(angle - sweep);
    const lg = sweep > Math.PI ? 1 : 0;
    return (
      <path key={sl.label}
        d={`M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${lg} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} L ${ix1.toFixed(2)} ${iy1.toFixed(2)} A ${ir} ${ir} 0 ${lg} 0 ${ix2.toFixed(2)} ${iy2.toFixed(2)} Z`}
        fill={sl.color} opacity={0.9} />
    );
  });
  return <svg width={size} height={size} style={{ display:"block" }}>{paths}</svg>;
}
