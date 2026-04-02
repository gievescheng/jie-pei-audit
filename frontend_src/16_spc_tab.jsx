// ─── DASHBOARD HOME ──────────────────────────────────────────────────────────
// ─── SPC MANAGEMENT TAB ──────────────────────────────────────────────────────

function SpcImrChart({ result, label, color = "#38bdf8", spec = {} }) {
  if (!result || !result.x_values || result.x_values.length === 0)
    return <div style={{ color:"#475569", fontSize:12, textAlign:"center", padding:16 }}>尚無資料</div>;

  const xVals = result.x_values;
  const mrVals = result.mr_values || [];
  const xBar = result.x_bar, xUcl = result.x_ucl, xLcl = result.x_lcl;
  const mrBar = result.mr_bar, mrUcl = result.mr_ucl;
  const oocX = new Set(result.ooc_x || []);
  const oocMr = new Set(result.ooc_mr || []);

  const W = 520, H = 130, padL = 40, padR = 12, padT = 14, padB = 20;
  const innerW = W - padL - padR, innerH = H - padT - padB;

  function makeScaler(vals, extras = []) {
    const all = [...vals, ...extras].filter(v => v !== null && v !== undefined);
    const mn = Math.min(...all), mx = Math.max(...all);
    const pad = (mx - mn) * 0.15 || 0.5;
    return { min: mn - pad, max: mx + pad };
  }

  function toY(v, domain) {
    return padT + innerH - ((v - domain.min) / (domain.max - domain.min)) * innerH;
  }

  function polyline(vals, domain) {
    return vals.map((v, i) => {
      const x = padL + (i / Math.max(vals.length - 1, 1)) * innerW;
      return `${x.toFixed(1)},${toY(v, domain).toFixed(1)}`;
    }).join(" ");
  }

  const xDomain = makeScaler(xVals, [xUcl, xLcl, spec.usl, spec.lsl].filter(Boolean));
  const mrDomain = makeScaler(mrVals, [mrUcl]);

  function hLine(y, stroke, dash = "") {
    return <line x1={padL} y1={y} x2={padL + innerW} y2={y} stroke={stroke} strokeWidth={1} strokeDasharray={dash} />;
  }

  const uslY = spec.usl != null ? toY(spec.usl, xDomain) : null;
  const lslY = spec.lsl != null ? toY(spec.lsl, xDomain) : null;

  return (
    <div>
      <div style={{ fontSize:12, color:"#94a3b8", marginBottom:4, fontWeight:600 }}>{label} — X 管制圖</div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display:"block", overflow:"visible" }}>
        {/* gridlines */}
        {hLine(toY(xUcl, xDomain), "rgba(239,68,68,0.5)", "4 2")}
        {hLine(toY(xBar, xDomain), "rgba(255,255,255,0.25)")}
        {hLine(toY(xLcl, xDomain), "rgba(239,68,68,0.5)", "4 2")}
        {uslY && hLine(uslY, "rgba(251,191,36,0.6)", "2 3")}
        {lslY && hLine(lslY, "rgba(251,191,36,0.6)", "2 3")}
        {/* area */}
        <polyline points={polyline(xVals, xDomain)} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
        {/* points */}
        {xVals.map((v, i) => {
          const cx = padL + (i / Math.max(xVals.length - 1, 1)) * innerW;
          const cy = toY(v, xDomain);
          const isOoc = oocX.has(i);
          return <circle key={i} cx={cx} cy={cy} r={isOoc ? 4 : 2.5} fill={isOoc ? "#ef4444" : color} />;
        })}
        {/* Y labels */}
        <text x={padL - 4} y={toY(xUcl, xDomain) + 4} textAnchor="end" fill="#ef4444" fontSize={8}>UCL</text>
        <text x={padL - 4} y={toY(xBar, xDomain) + 4} textAnchor="end" fill="#94a3b8" fontSize={8}>X̄</text>
        <text x={padL - 4} y={toY(xLcl, xDomain) + 4} textAnchor="end" fill="#ef4444" fontSize={8}>LCL</text>
        {/* X axis ticks */}
        {xVals.map((_, i) => i % Math.ceil(xVals.length / 8) === 0 ? (
          <text key={i} x={padL + (i / Math.max(xVals.length - 1, 1)) * innerW} y={H - 4} textAnchor="middle" fill="#475569" fontSize={7}>{i + 1}</text>
        ) : null)}
      </svg>
      {mrVals.length > 0 && (
        <>
          <div style={{ fontSize:12, color:"#94a3b8", marginBottom:4, marginTop:10, fontWeight:600 }}>{label} — MR 管制圖</div>
          <svg width="100%" viewBox={`0 0 ${W} ${Math.round(H * 0.65)}`} style={{ display:"block", overflow:"visible" }}>
            {hLine(toY(mrUcl, mrDomain), "rgba(239,68,68,0.5)", "4 2")}
            {hLine(toY(mrBar, mrDomain), "rgba(255,255,255,0.2)")}
            <polyline points={polyline(mrVals, mrDomain)} fill="none" stroke="#a78bfa" strokeWidth={1.5} />
            {mrVals.map((v, i) => {
              const cx = padL + (i / Math.max(mrVals.length - 1, 1)) * innerW;
              const cy = toY(v, mrDomain);
              return <circle key={i} cx={cx} cy={cy} r={oocMr.has(i) ? 4 : 2} fill={oocMr.has(i) ? "#ef4444" : "#a78bfa"} />;
            })}
            <text x={padL - 4} y={toY(mrUcl, mrDomain) + 4} textAnchor="end" fill="#ef4444" fontSize={8}>UCL</text>
          </svg>
        </>
      )}
    </div>
  );
}

function CpkGauge({ cpk, label }) {
  if (cpk == null) return null;
  const grade = cpk >= 1.67 ? { text:"A+", color:"#22c55e" }
    : cpk >= 1.33 ? { text:"A",  color:"#4ade80" }
    : cpk >= 1.00 ? { text:"B",  color:"#f59e0b" }
    : cpk >= 0.67 ? { text:"C",  color:"#f97316" }
    : { text:"D", color:"#ef4444" };
  const pct = Math.min(cpk / 2.0, 1.0);
  return (
    <div style={{ textAlign:"center" }}>
      <div style={{ fontSize:11, color:"#64748b", marginBottom:4 }}>{label}</div>
      <div style={{ width:72, height:72, borderRadius:"50%", border:`3px solid ${grade.color}`, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", margin:"0 auto" }}>
        <div style={{ fontSize:18, fontWeight:800, color:grade.color, lineHeight:1 }}>{cpk.toFixed(2)}</div>
        <div style={{ fontSize:11, fontWeight:700, color:grade.color }}>{grade.text}</div>
      </div>
      <div style={{ width:72, height:5, background:"rgba(255,255,255,0.07)", borderRadius:3, margin:"6px auto 0", overflow:"hidden" }}>
        <div style={{ width:(pct * 100) + "%", height:"100%", background:grade.color, borderRadius:3 }} />
      </div>
    </div>
  );
}

const NELSON_LABELS = {
  rule_1_beyond_3sigma:     "Rule 1：超出 ±3σ",
  rule_2_nine_same_side:    "Rule 2：連續 9 點同側",
  rule_3_six_monotone:      "Rule 3：連續 6 點單調",
  rule_4_fourteen_alternating: "Rule 4：連續 14 點交替",
  rule_5_two_of_three_2sigma:  "Rule 5：3 點中 2 點超 ±2σ",
  rule_6_four_of_five_1sigma:  "Rule 6：5 點中 4 點超 ±1σ",
};

function SpcTab({ prodRecords }) {
  const [csvFile, setCsvFile] = useState(null);
  const [batchId, setBatchId] = useState("");
  const [specForm, setSpecForm] = useState({ thickness_usl:"705", thickness_lsl:"695", ttv_usl:"2.0", ttv_lsl:"0.0" });
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [activeResult, setActiveResult] = useState(null);
  const fileRef = useRef(null);

  useEffect(() => {
    fetch("/api/spc/history").then(r => r.json()).then(d => setHistory(d.items || [])).catch(() => {});
  }, []);

  async function handleAnalyze() {
    if (!csvFile && !batchId) { setMsg("請選擇 CSV 檔案"); return; }
    setBusy(true); setMsg(""); setResult(null);
    try {
      let res;
      if (csvFile) {
        const fd = new FormData();
        fd.append("csv_file", csvFile);
        fd.append("batch_id", batchId || csvFile.name.replace(/\.csv$/i, ""));
        fd.append("spec", JSON.stringify({
          thickness_usl: parseFloat(specForm.thickness_usl),
          thickness_lsl: parseFloat(specForm.thickness_lsl),
          ttv_usl: parseFloat(specForm.ttv_usl),
          ttv_lsl: parseFloat(specForm.ttv_lsl),
        }));
        const resp = await fetch("/api/spc/analyze", { method:"POST", body: fd });
        res = await resp.json();
      }
      if (!res.success) throw new Error(res.error || "分析失敗");
      setResult(res);
      setActiveResult(res.result);
      // 重新載入歷史
      const hResp = await fetch("/api/spc/history");
      const hData = await hResp.json();
      setHistory(hData.items || []);
      setMsg("✓ 分析完成");
    } catch (e) {
      setMsg("❌ " + e.message);
    } finally {
      setBusy(false);
    }
  }

  const displayResult = activeResult || (result && result.result);
  const thk = displayResult && displayResult.thickness;
  const ttv = displayResult && displayResult.ttv;
  const summary = displayResult && displayResult.summary;

  const allNelson = [];
  [["Thickness", thk], ["TTV", ttv]].forEach(([name, r]) => {
    if (!r) return;
    Object.entries(r.nelson_signals || {}).forEach(([k, pts]) => {
      if (pts && pts.length) allNelson.push({ name, rule: NELSON_LABELS[k] || k, count: pts.length });
    });
  });

  const panel = (children, style={}) => (
    <div style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:20, ...style }}>
      {children}
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom:20 }}>
        <div style={{ fontSize:20, fontWeight:800, color:"#e2e8f0" }}>SPC 統計製程管制</div>
        <div style={{ fontSize:13, color:"#64748b", marginTop:4 }}>晶圓清洗製程 — Thickness / TTV / Particle 管制圖</div>
      </div>

      {/* ── 上傳區 ── */}
      {panel(<>
        <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:16 }}>上傳 CSV 量測資料</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr 1fr", gap:12, marginBottom:16 }}>
          {[
            { key:"thickness_usl", label:"Thickness USL (μm)" },
            { key:"thickness_lsl", label:"Thickness LSL (μm)" },
            { key:"ttv_usl",       label:"TTV USL (μm)" },
            { key:"ttv_lsl",       label:"TTV LSL (μm)" },
          ].map(f => (
            <div key={f.key}>
              <div style={{ fontSize:11, color:"#64748b", marginBottom:4 }}>{f.label}</div>
              <input type="number" step="0.1" value={specForm[f.key]}
                onChange={e => setSpecForm(p => ({...p, [f.key]: e.target.value}))}
                style={{ width:"100%", background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, padding:"6px 10px", color:"#e2e8f0", fontSize:13 }} />
            </div>
          ))}
        </div>
        <div style={{ display:"flex", gap:12, alignItems:"center", flexWrap:"wrap" }}>
          <input type="text" placeholder="批次 ID（選填，預設用檔名）" value={batchId}
            onChange={e => setBatchId(e.target.value)}
            style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, padding:"7px 12px", color:"#e2e8f0", fontSize:13, width:220 }} />
          <button onClick={() => fileRef.current && fileRef.current.click()}
            style={{ background:"rgba(56,189,248,0.12)", border:"1px solid rgba(56,189,248,0.3)", borderRadius:8, padding:"7px 16px", color:"#7dd3fc", fontSize:13, cursor:"pointer", fontWeight:600 }}>
            {csvFile ? `📄 ${csvFile.name}` : "選擇 CSV 檔"}
          </button>
          <input ref={fileRef} type="file" accept=".csv" style={{ display:"none" }}
            onChange={e => { setCsvFile(e.target.files[0] || null); setBatchId(prev => prev || (e.target.files[0] ? e.target.files[0].name.replace(/\.csv$/i,"") : "")); }} />
          <button onClick={handleAnalyze} disabled={busy || !csvFile}
            style={{ background: busy || !csvFile ? "rgba(255,255,255,0.04)" : "linear-gradient(90deg,#3b82f6,#6366f1)", border:"none", borderRadius:8, padding:"7px 20px", color: busy || !csvFile ? "#475569" : "#fff", fontSize:13, cursor: busy || !csvFile ? "default" : "pointer", fontWeight:700 }}>
            {busy ? "分析中…" : "開始分析"}
          </button>
          {msg && <span style={{ fontSize:13, color: msg.startsWith("✓") ? "#22c55e" : "#ef4444" }}>{msg}</span>}
        </div>
        {result && result.parse_errors && result.parse_errors.length > 0 && (
          <div style={{ marginTop:12, padding:"8px 12px", background:"rgba(234,179,8,0.08)", border:"1px solid rgba(234,179,8,0.3)", borderRadius:8 }}>
            {result.parse_errors.map((e, i) => <div key={i} style={{ fontSize:12, color:"#fde68a" }}>{e}</div>)}
          </div>
        )}
      </>, { marginBottom:16 })}

      {/* ── 分析結果 ── */}
      {displayResult && (
        <>
          {/* Summary 警示 */}
          {summary && summary.needs_attention && (
            <div style={{ marginBottom:14, padding:"10px 16px", background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:10, display:"flex", gap:10, alignItems:"center" }}>
              <span style={{ fontSize:16 }}>⚠</span>
              <div>
                <div style={{ fontSize:13, fontWeight:700, color:"#fca5a5" }}>製程異常警示</div>
                <div style={{ fontSize:12, color:"#fca5a5", marginTop:2 }}>
                  {summary.any_ooc && "偵測到超出管制界限（OOC）的點；"}
                  {summary.any_nelson && "Nelson Rules 訊號觸發，請確認製程狀態。"}
                </div>
              </div>
            </div>
          )}

          {/* Nelson Rules */}
          {allNelson.length > 0 && panel(<>
            <div style={{ fontSize:13, fontWeight:700, color:"#fbbf24", marginBottom:10 }}>⚡ Nelson Rules 失控訊號</div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
              {allNelson.map((n, i) => (
                <div key={i} style={{ background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, padding:"5px 12px", fontSize:12, color:"#fca5a5" }}>
                  <span style={{ fontWeight:700 }}>[{n.name}]</span> {n.rule}（{n.count} 處）
                </div>
              ))}
            </div>
          </>, { marginBottom:14 })}

          {/* Cpk 儀錶 + 統計摘要 */}
          {panel(<>
            <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>製程能力指數</div>
            <div style={{ display:"flex", gap:32, flexWrap:"wrap", alignItems:"flex-start" }}>
              <CpkGauge cpk={summary && summary.thickness_cpk} label="Thickness Cpk" />
              <CpkGauge cpk={summary && summary.ttv_cpk} label="TTV Cpk" />
              <div style={{ flex:1, minWidth:200 }}>
                {thk && thk.capability && (
                  <div style={{ fontSize:12, color:"#94a3b8", lineHeight:1.9 }}>
                    <div>Thickness：X̄ = <span style={{ color:"#e2e8f0" }}>{thk.x_bar.toFixed(3)} μm</span> / σ = <span style={{ color:"#e2e8f0" }}>{thk.sigma_mr.toFixed(4)}</span></div>
                    {thk.capability.cp   != null && <div>Cp = <span style={{ color:"#60a5fa" }}>{thk.capability.cp}</span></div>}
                    {thk.capability.cpk  != null && <div>Cpk = <span style={{ color:"#60a5fa" }}>{thk.capability.cpk}</span> <span style={{ color:"#475569" }}>({thk.capability.grade})</span></div>}
                  </div>
                )}
                {ttv && ttv.capability && (
                  <div style={{ fontSize:12, color:"#94a3b8", lineHeight:1.9, marginTop:8 }}>
                    <div>TTV：X̄ = <span style={{ color:"#e2e8f0" }}>{ttv.x_bar.toFixed(4)} μm</span> / σ = <span style={{ color:"#e2e8f0" }}>{ttv.sigma_mr.toFixed(5)}</span></div>
                    {ttv.capability.cpk != null && <div>Cpk = <span style={{ color:"#60a5fa" }}>{ttv.capability.cpk}</span> <span style={{ color:"#475569" }}>({ttv.capability.grade})</span></div>}
                  </div>
                )}
              </div>
            </div>
          </>, { marginBottom:14 })}

          {/* I-MR 圖 */}
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:14 }}>
            {thk && panel(<>
              <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>Thickness I-MR 管制圖</div>
              <SpcImrChart result={thk} label="Thickness" color="#38bdf8"
                spec={{ usl: parseFloat(specForm.thickness_usl), lsl: parseFloat(specForm.thickness_lsl) }} />
              {thk.ooc_x && thk.ooc_x.length > 0 && (
                <div style={{ marginTop:8, fontSize:11, color:"#fca5a5" }}>
                  OOC 點：第 {thk.ooc_x.map(i => i + 1).join("、")} 筆
                </div>
              )}
            </>)}
            {ttv && panel(<>
              <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:12 }}>TTV I-MR 管制圖</div>
              <SpcImrChart result={ttv} label="TTV" color="#a78bfa"
                spec={{ usl: parseFloat(specForm.ttv_usl), lsl: parseFloat(specForm.ttv_lsl) }} />
              {ttv.ooc_x && ttv.ooc_x.length > 0 && (
                <div style={{ marginTop:8, fontSize:11, color:"#fca5a5" }}>
                  OOC 點：第 {ttv.ooc_x.map(i => i + 1).join("、")} 筆
                </div>
              )}
            </>)}
          </div>
        </>
      )}

      {/* ── 跨批次 Cpk 趨勢圖 ── */}
      {history.length >= 2 && panel(<>
        <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>跨批次 Cpk 趨勢（近 {Math.min(history.length,20)} 批）</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
          {[
            { key:"thickness_cpk", label:"Thickness Cpk", color:"#38bdf8" },
            { key:"ttv_cpk",       label:"TTV Cpk",       color:"#a78bfa" },
          ].map(({ key, label, color }) => {
            const pts = [...history].reverse().slice(0, 20)
              .filter(h => h[key] != null)
              .map((h, i) => ({ label: String(i + 1), value: h[key] }));
            return (
              <div key={key}>
                <div style={{ fontSize:11, color:"#64748b", marginBottom:6, fontWeight:600 }}>{label}</div>
                {pts.length >= 2
                  ? <SvgLineChart data={pts} color={color} domainMin={0} domainMax={Math.max(2, ...pts.map(p => p.value)) * 1.1} />
                  : <div style={{ fontSize:11, color:"#475569" }}>需 2 筆以上</div>
                }
                {/* 目標線說明 */}
                <div style={{ display:"flex", gap:12, marginTop:4 }}>
                  {[{v:1.33,c:"#22c55e",t:"A（≥1.33）"},{v:1.00,c:"#f59e0b",t:"B（≥1.00）"}].map(g => (
                    <div key={g.v} style={{ display:"flex", alignItems:"center", gap:4 }}>
                      <div style={{ width:12, height:2, background:g.c, borderRadius:1 }} />
                      <span style={{ fontSize:9, color:"#475569" }}>{g.t}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </>, { marginBottom:16 })}

      {/* ── 歷史記錄 ── */}
      {panel(<>
        <div style={{ fontSize:13, fontWeight:700, color:"#e2e8f0", marginBottom:14 }}>近期分析記錄</div>
        {history.length === 0 && <div style={{ color:"#475569", fontSize:12 }}>尚無分析記錄</div>}
        <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
          {history.slice(0, 10).map((h, i) => {
            const tCpk = h.thickness_cpk, vCpk = h.ttv_cpk;
            const tColor = tCpk == null ? "#475569" : tCpk >= 1.33 ? "#22c55e" : tCpk >= 1.00 ? "#f59e0b" : "#ef4444";
            const vColor = vCpk == null ? "#475569" : vCpk >= 1.33 ? "#22c55e" : vCpk >= 1.00 ? "#f59e0b" : "#ef4444";
            return (
              <div key={i} style={{ display:"flex", alignItems:"center", gap:12, padding:"8px 12px", background:"rgba(255,255,255,0.02)", borderRadius:8, border:"1px solid rgba(255,255,255,0.06)", cursor:"pointer" }}
                onClick={() => setActiveResult(h.result || null)}
                onMouseEnter={e => e.currentTarget.style.background="rgba(255,255,255,0.05)"}
                onMouseLeave={e => e.currentTarget.style.background="rgba(255,255,255,0.02)"}>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:12, color:"#e2e8f0", fontWeight:600 }}>{h.batch_id}</div>
                  <div style={{ fontSize:11, color:"#475569" }}>{h.analyzed_at} · {h.thickness_n || 0} 筆</div>
                </div>
                <div style={{ display:"flex", gap:16 }}>
                  <div style={{ textAlign:"center" }}>
                    <div style={{ fontSize:10, color:"#64748b" }}>Thickness Cpk</div>
                    <div style={{ fontSize:13, fontWeight:700, color:tColor }}>{tCpk != null ? tCpk.toFixed(2) : "–"}</div>
                  </div>
                  <div style={{ textAlign:"center" }}>
                    <div style={{ fontSize:10, color:"#64748b" }}>TTV Cpk</div>
                    <div style={{ fontSize:13, fontWeight:700, color:vColor }}>{vCpk != null ? vCpk.toFixed(2) : "–"}</div>
                  </div>
                  {h.needs_attention && <span style={{ fontSize:11, color:"#ef4444", alignSelf:"center" }}>⚠ 異常</span>}
                  {h.has_raw_rows && (
                    <a href={`/api/spc/fosb?batch_id=${encodeURIComponent(h.batch_id)}`}
                      download onClick={e => e.stopPropagation()}
                      style={{ fontSize:11, color:"#7dd3fc", background:"rgba(56,189,248,0.08)", border:"1px solid rgba(56,189,248,0.2)", borderRadius:6, padding:"3px 8px", textDecoration:"none", alignSelf:"center", whiteSpace:"nowrap" }}>
                      ↓ FOSB
                    </a>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </>)}
    </div>
  );
}
