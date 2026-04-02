// ─── DASHBOARD HOME ───────────────────────────────────────────────────────────
function DashboardHome({ instruments, documents, training, equipment, suppliers, nonConformances, auditPlans, envRecords, setActiveTab }) {
  const now = new Date(); now.setHours(0,0,0,0);
  const overdueInst = instruments.filter(i => daysUntil(i.nextCalibration) < 0).length;
  const upcomingInst = instruments.filter(i => { const d=daysUntil(i.nextCalibration); return d>=0&&d<=30; }).length;
  const overdueDoc = documents.filter(d => daysUntil(d.nextReview) < 0).length;
  const expiredTrain = training.filter(t => daysUntil(t.validUntil) < 0).length;
  const overdueEquip = equipment.filter(e => daysUntil(e.nextMaintenance) < 0).length;
  const openNc = nonConformances.filter(n => n.status !== "已關閉").length;
  const overdueNc = nonConformances.filter(n => n.status !== "已關閉" && daysUntil(n.dueDate) < 0).length;
  const upcomingAudit = auditPlans.filter(a => a.status === "計畫中" && daysUntil(a.scheduledDate) >= 0 && daysUntil(a.scheduledDate) <= 30).length;
  const envPassRate = envRecords.length > 0 ? Math.round(envRecords.filter(r => r.result === "合格").length / envRecords.length * 100) : 0;
  const poorSupplier = suppliers.filter(s => s.score < 70).length;
  const alerts = [];
  if (overdueInst > 0) alerts.push({ type: "error", msg: `有 ${overdueInst} 个小器校正遇期，請立即安排試驗` });
  if (upcomingInst > 0) alerts.push({ type: "warn", msg: `有 ${upcomingInst} 个小器將於 30 天內到期校正` });
  if (overdueDoc > 0) alerts.push({ type: "error", msg: `有 ${overdueDoc} 份文件顆開複審遇期` });
  if (expiredTrain > 0) alerts.push({ type: "error", msg: `有 ${expiredTrain} 檔員訓練認證已過期` });
  if (overdueEquip > 0) alerts.push({ type: "error", msg: `有 ${overdueEquip} 台設備保養遇期` });
  if (overdueNc > 0) alerts.push({ type: "error", msg: `有 ${overdueNc} 个不符合項目已逾期未關閉` });
  if (upcomingAudit > 0) alerts.push({ type: "warn", msg: `${upcomingAudit} 場內部稽核將於 30 天內執行` });
  if (poorSupplier > 0) alerts.push({ type: "warn", msg: `有 ${poorSupplier} 家供應商評分不足 70 分` });
  if (envPassRate < 90) alerts.push({ type: "warn", msg: `潔淨室環境合格率僅 ${envPassRate}%` });
  const kpis = [
    { label: "校正小器", value: instruments.length, sub: overdueInst > 0 ? `${overdueInst}个遇期` : "全部正常", color: overdueInst > 0 ? "#ef4444" : "#60a5fa", tab: "calibration" },
    { label: "程序文件", value: documents.length, sub: overdueDoc > 0 ? `${overdueDoc}份鸞期` : "全部有效", color: overdueDoc > 0 ? "#ef4444" : "#22c55e", tab: "documents" },
    { label: "訓練記錄", value: training.length, sub: expiredTrain > 0 ? `${expiredTrain}人過期` : "全部有效", color: expiredTrain > 0 ? "#ef4444" : "#22c55e", tab: "training" },
    { label: "設備保養", value: equipment.length, sub: overdueEquip > 0 ? `${overdueEquip}台鸞期` : "全部正常", color: overdueEquip > 0 ? "#ef4444" : "#22c55e", tab: "equipment" },
    { label: "供應商", value: suppliers.length, sub: poorSupplier > 0 ? `${poorSupplier}家評分不足` : "全部合格", color: poorSupplier > 0 ? "#eab308" : "#22c55e", tab: "supplier" },
    { label: "不符合項", value: nonConformances.length, sub: openNc > 0 ? `${openNc}個未關閉` : "全部已關閉", color: openNc > 0 ? "#ef4444" : "#22c55e", tab: "nonconformance" },
    { label: "稽核計畫", value: auditPlans.length, sub: upcomingAudit > 0 ? `${upcomingAudit}地30天內執行` : "如期進行", color: upcomingAudit > 0 ? "#f97316" : "#8b5cf6", tab: "auditplan" },
    { label: "環境監測", value: envRecords.length, sub: `合格率 ${envPassRate}%`, color: envPassRate >= 90 ? "#14b8a6" : envPassRate >= 80 ? "#eab308" : "#ef4444", tab: "environment" },
  ];
  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 22, fontWeight: 800, color: "#e2e8f0", letterSpacing: 1 }}>潔沛企業有限公司 ISO 9001:2015</div>
        <div style={{ fontSize: 14, color: "#64748b", marginTop: 4 }}>品質管理系統自動稽核主控台 — {new Date().toLocaleDateString("zh-TW", { year:"numeric", month:"long", day:"numeric" })}</div>
      </div>
      {alerts.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 13, color: "#94a3b8", fontWeight: 700, marginBottom: 10 }}>⚠ 系統警示 ({alerts.length})</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {alerts.map((a, i) => (
              <div key={i} style={{ background: a.type==="error"?"rgba(239,68,68,0.08)":"rgba(234,179,8,0.08)", border: `1px solid ${a.type==="error"?"rgba(239,68,68,0.3)":"rgba(234,179,8,0.3)"}`, borderRadius: 10, padding: "10px 16px", fontSize: 13, color: a.type==="error"?"#fca5a5":"#fde68a", display:"flex", alignItems:"center", gap:8 }}>
                <span>{a.type==="error"?"❌":"⚠️"}</span><span>{a.msg}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 14, marginBottom: 28 }}>
        {kpis.map(k => (
          <div key={k.tab} onClick={() => setActiveTab(k.tab)} style={{ background: "rgba(255,255,255,0.04)", border: `1px solid ${k.color}40`, borderRadius: 14, padding: "18px 20px", cursor: "pointer", transition: "all 0.2s" }}
            onMouseEnter={e => e.currentTarget.style.background="rgba(255,255,255,0.08)"}
            onMouseLeave={e => e.currentTarget.style.background="rgba(255,255,255,0.04)"} >
            <div style={{ fontSize: 28, fontWeight: 800, color: k.color, lineHeight: 1 }}>{k.value}</div>
            <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 6 }}>{k.label}</div>
            <div style={{ fontSize: 11, color: k.color, marginTop: 4, fontWeight: 600 }}>{k.sub}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0", marginBottom: 14 }}>最近校正到期小器</div>
          {[...instruments].sort((a,b) => daysUntil(a.nextCalibration)-daysUntil(b.nextCalibration)).slice(0,5).map(inst => (
            <div key={inst.id} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
              <div>
                <div style={{ fontSize:13, color:"#e2e8f0" }}>{inst.name}</div>
                <div style={{ fontSize:11, color:"#64748b" }}>{inst.id}</div>
              </div>
              <Badge color={urgencyColor(daysUntil(inst.nextCalibration))}>{urgencyLabel(daysUntil(inst.nextCalibration))}</Badge>
            </div>
          ))}
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: 20 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0", marginBottom: 14 }}>未關閉不符合項目</div>
          {nonConformances.filter(n => n.status !== "已關閉").slice(0,5).map(nc => (
            <div key={nc.id} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
              <div>
                <div style={{ fontSize:12, color:"#e2e8f0" }}>{nc.description.slice(0,20)}{nc.description.length>20?"...":""}</div>
                <div style={{ fontSize:11, color:"#64748b" }}>{nc.id} — {nc.dept}</div>
              </div>
              <Badge color={daysUntil(nc.dueDate)===9999?"#64748b":daysUntil(nc.dueDate)<0?"#ef4444":daysUntil(nc.dueDate)<=7?"#eab308":"#60a5fa"}>{daysUntil(nc.dueDate)===9999?"無到期日":daysUntil(nc.dueDate)<0?"逾期":"剩"+daysUntil(nc.dueDate)+"天"}</Badge>
            </div>
          ))}
          {nonConformances.filter(n=>n.status!=="已關閉").length===0 && <div style={{color:"#22c55e",fontSize:13,marginTop:8}}>✓ 目前沒有未關閉不符合項</div>}
        </div>
      </div>
    </div>
  );
}

// ─── 角色可見分頁定義 ────────────────────────────────────────────────────────
const ROLE_TABS = {
  qms:        ["home","kpi","spc","calibration","documents","library","training","equipment","supplier","nonconformance","auditplan","environment","production","notification","aiworkbench","report"],
  executive:  ["home","kpi","spc"],
  supervisor: ["home","kpi","spc","nonconformance","environment","production"],
  auditor:    ["home","calibration","documents","library","nonconformance","auditplan","report"],
};

// ─── 登入畫面 ────────────────────────────────────────────────────────────────
function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim().toLowerCase(), password }),
      });
      const data = await resp.json();
      if (!data.success) throw new Error(data.error || "登入失敗");
      localStorage.setItem("qms_token", data.token);
      localStorage.setItem("qms_user", JSON.stringify(data.user));
      onLogin(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const accounts = [
    { role:"品管人員",  user:"qms",   pw:"qms1234"   },
    { role:"高階主管",  user:"exec",  pw:"exec1234"  },
    { role:"生產主管",  user:"super", pw:"super1234" },
    { role:"外部稽核員",user:"audit", pw:"audit1234" },
  ];

  return (
    <div style={{ minHeight:"100vh", background:"radial-gradient(circle at top left, rgba(14,165,233,0.08), transparent 26%), linear-gradient(135deg, #08101f 0%, #0b1220 45%, #080d18 100%)", display:"flex", alignItems:"center", justifyContent:"center", fontFamily:"'Noto Sans TC', sans-serif" }}>
      <div style={{ width:400 }}>
        {/* Logo */}
        <div style={{ textAlign:"center", marginBottom:36 }}>
          <div style={{ fontSize:13, letterSpacing:2, textTransform:"uppercase", color:"#7dd3fc", fontWeight:800, marginBottom:6 }}>Jepei QMS</div>
          <div style={{ fontSize:22, fontWeight:800, color:"#e2e8f0" }}>潔沛企業有限公司</div>
          <div style={{ fontSize:13, color:"#64748b", marginTop:4 }}>ISO 9001:2015 品質管理系統</div>
        </div>

        {/* 登入表單 */}
        <form onSubmit={handleSubmit} style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:16, padding:32 }}>
          <div style={{ fontSize:16, fontWeight:700, color:"#e2e8f0", marginBottom:24 }}>登入系統</div>
          <div style={{ marginBottom:16 }}>
            <div style={{ fontSize:12, color:"#64748b", marginBottom:6 }}>帳號</div>
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="請輸入帳號" autoFocus
              className="qms-input"
              style={{ width:"100%", background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, padding:"9px 12px", color:"#e2e8f0", fontSize:14, outline:"none", boxSizing:"border-box" }} />
          </div>
          <div style={{ marginBottom:24 }}>
            <div style={{ fontSize:12, color:"#64748b", marginBottom:6 }}>密碼</div>
            <div style={{ position:"relative" }}>
              <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} placeholder="請輸入密碼"
                className="qms-input"
                style={{ width:"100%", background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, padding:"9px 40px 9px 12px", color:"#e2e8f0", fontSize:14, outline:"none", boxSizing:"border-box" }} />
              <button type="button" onClick={() => setShowPw(p => !p)}
                style={{ position:"absolute", right:10, top:"50%", transform:"translateY(-50%)", background:"none", border:"none", color:"#64748b", cursor:"pointer", fontSize:13, padding:2 }}>
                {showPw ? "隱藏" : "顯示"}
              </button>
            </div>
          </div>
          {error && <div style={{ marginBottom:16, padding:"8px 12px", background:"rgba(239,68,68,0.1)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:8, fontSize:13, color:"#fca5a5" }}>{error}</div>}
          <button type="submit" disabled={busy || !username || !password}
            className="qms-btn"
            style={{ width:"100%", padding:"10px 0", background: busy || !username || !password ? "rgba(255,255,255,0.05)" : "linear-gradient(90deg,#3b82f6,#6366f1)", border:"none", borderRadius:8, color: busy || !username || !password ? "#475569" : "#fff", fontSize:14, fontWeight:700, cursor: busy || !username || !password ? "not-allowed" : "pointer" }}>
            {busy ? "登入中…" : "登入"}
          </button>
        </form>

        {/* 預設帳號提示 */}
        <div style={{ marginTop:20, background:"rgba(255,255,255,0.02)", border:"1px solid rgba(255,255,255,0.06)", borderRadius:12, padding:16 }}>
          <div style={{ fontSize:11, color:"#475569", marginBottom:10, fontWeight:600 }}>預設帳號（初次使用請更改密碼）</div>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6 }}>
            {accounts.map(a => (
              <button key={a.user} type="button"
                onClick={() => { setUsername(a.user); setPassword(a.pw); }}
                className="qms-quick-btn"
                style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.07)", borderRadius:8, padding:"6px 10px", textAlign:"left", cursor:"pointer" }}>
                <div style={{ fontSize:11, color:"#94a3b8", fontWeight:600 }}>{a.role}</div>
                <div style={{ fontSize:10, color:"#475569", marginTop:2 }}>{a.user} / {a.pw}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 更改密碼 Modal ──────────────────────────────────────────────────────────
function ChangePasswordModal({ token, onClose }) {
  const [form, setForm] = useState({ old_password:"", new_password:"", confirm:"" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (form.new_password !== form.confirm) { setMsg("兩次新密碼不一致"); return; }
    if (form.new_password.length < 6) { setMsg("密碼至少 6 個字元"); return; }
    setBusy(true); setMsg("");
    try {
      const resp = await fetch("/api/auth/change-password", {
        method:"POST",
        headers: { "Content-Type":"application/json", "Authorization":"Bearer " + token },
        body: JSON.stringify({ old_password: form.old_password, new_password: form.new_password }),
      });
      const data = await resp.json();
      if (!data.success) throw new Error(data.error || "更新失敗");
      setMsg("✓ 密碼已更新");
      setTimeout(onClose, 1200);
    } catch(err) {
      setMsg("❌ " + err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ position:"fixed", inset:0, zIndex:999, background:"rgba(0,0,0,0.6)", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <form onSubmit={handleSubmit} style={{ background:"#0f1929", border:"1px solid rgba(255,255,255,0.12)", borderRadius:14, padding:28, width:340 }}>
        <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0", marginBottom:20 }}>更改密碼</div>
        {["old_password","new_password","confirm"].map(k => (
          <div key={k} style={{ marginBottom:14 }}>
            <div style={{ fontSize:11, color:"#64748b", marginBottom:4 }}>
              {k === "old_password" ? "舊密碼" : k === "new_password" ? "新密碼" : "確認新密碼"}
            </div>
            <input type="password" value={form[k]} onChange={e => setForm(p => ({...p, [k]: e.target.value}))}
              className="qms-input"
              style={{ width:"100%", background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.12)", borderRadius:8, padding:"7px 10px", color:"#e2e8f0", fontSize:13, boxSizing:"border-box", outline:"none" }} />
          </div>
        ))}
        {msg && <div style={{ marginBottom:12, fontSize:12, color: msg.startsWith("✓") ? "#22c55e" : "#fca5a5" }}>{msg}</div>}
        <div style={{ display:"flex", gap:10 }}>
          <button type="submit" disabled={busy} style={{ flex:1, padding:"8px 0", background:"linear-gradient(90deg,#3b82f6,#6366f1)", border:"none", borderRadius:8, color:"#fff", fontSize:13, fontWeight:700, cursor:"pointer" }}>
            {busy ? "更新中…" : "確認更新"}
          </button>
          <button type="button" onClick={onClose} style={{ padding:"8px 16px", background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:8, color:"#94a3b8", fontSize:13, cursor:"pointer" }}>取消</button>
        </div>
      </form>
    </div>
  );
}

// ─── MAIN APP ────────────────────────────────────────────────────────────────
export default function App() {
  // ── 主題狀態（深色/淺色）────────────────────────────────────
  const [darkMode, setDarkMode] = useState(() => {
    try { return localStorage.getItem("qms_theme") !== "light"; } catch { return true; }
  });
  function toggleTheme() {
    setDarkMode(d => {
      const next = !d;
      try { localStorage.setItem("qms_theme", next ? "dark" : "light"); } catch {}
      return next;
    });
  }
  const theme = darkMode ? DARK_THEME : LIGHT_THEME;

  // ── 身份驗證狀態 ──────────────────────────────────────────────
  const [authUser, setAuthUser] = useState(() => {
    try {
      const raw = localStorage.getItem("qms_user");
      if (!raw) return null;
      const u = JSON.parse(raw);
      // 快速驗證 token 仍有效
      const token = localStorage.getItem("qms_token");
      if (!token) return null;
      return u;
    } catch { return null; }
  });
  const [showChangePw, setShowChangePw] = useState(false);

  // 驗證 token 是否仍有效（頁面載入時）
  useEffect(() => {
    const token = localStorage.getItem("qms_token");
    if (!token) { setAuthUser(null); return; }
    fetch("/api/auth/me", { headers: { Authorization: "Bearer " + token } })
      .then(r => r.json())
      .then(d => { if (!d.success) { setAuthUser(null); localStorage.removeItem("qms_token"); localStorage.removeItem("qms_user"); } })
      .catch(() => {});
  }, []);

  function handleLogin(user) { setAuthUser(user); }
  function handleLogout() {
    localStorage.removeItem("qms_token");
    localStorage.removeItem("qms_user");
    setAuthUser(null);
  }

  // ── 主應用狀態（必須在所有提前 return 之前宣告）─────────────────
  const [activeTab, setActiveTab] = useState(() => {
    if (typeof window === "undefined") return "home";
    const params = new URLSearchParams(window.location.search);
    const t = params.get("google") ? "notification" : (params.get("tab") || "home");
    return t || "home";
  });
  const [instruments, setInstruments] = useState(initialInstruments);
  const [documents, setDocuments] = useState(initialDocuments);
  const [training, setTraining] = useState(initialTraining);
  const [equipment, setEquipment] = useState(() => loadStoredState("audit_equipment", initialEquipment));
  const [suppliers, setSuppliers] = useState(initialSuppliers);
  const [nonConformances, setNonConformances] = useState(initialNonConformances);
  const [highlightNcId, setHighlightNcId] = useState(null);
  const [expandNcId, setExpandNcId] = useState(null);
  const [auditPlans, setAuditPlans] = useState(initialAuditPlans);
  const [envRecords, setEnvRecords] = useState(initialEnvRecords);
  const [prodRecords, setProdRecords] = useState(() => loadStoredState("audit_prodrecords", initialProdRecords));
  const [qualityRecords, setQualityRecords] = useState(() => loadStoredState("audit_qualityrecords", initialQualityRecords));
  const [manuals] = useState(initialManuals);

  useEffect(() => saveStoredState("audit_prodrecords", prodRecords), [prodRecords]);
  useEffect(() => saveStoredState("audit_qualityrecords", qualityRecords), [qualityRecords]);
  useEffect(() => saveStoredState("audit_equipment", equipment), [equipment]);

  useEffect(() => {
    if (!authUser) return;
    let cancelled = false;
    async function loadOpsData() {
      try {
        const [ncPayload, auditPayload, envPayload] = await Promise.all([
          apiJson("/api/nonconformances"),
          apiJson("/api/audit-plans"),
          apiJson("/api/environment-records"),
        ]);
        if (cancelled) return;
        setNonConformances(ncPayload.items || []);
        setAuditPlans(auditPayload.items || []);
        setEnvRecords(envPayload.items || []);
      } catch (err) {
        console.warn("Failed to load operation data", err);
      }
    }
    loadOpsData();
    return () => { cancelled = true; };
  }, [authUser]);

  // ── 未登入 → 顯示登入畫面 ────────────────────────────────────
  if (!authUser) return (
    <ThemeContext.Provider value={theme}>
      <GlobalStyles isDark={darkMode} />
      <LoginScreen onLogin={handleLogin} />
    </ThemeContext.Provider>
  );

  const userRole = authUser.role || "qms";
  const allowedTabs = ROLE_TABS[userRole] || ROLE_TABS.qms;

  const allTabs = [
    { id: "home",           label: "主控台",     icon: "⌂" },
    { id: "kpi",            label: "績效儀表板",  icon: "▦" },
    { id: "spc",            label: "SPC 管制圖",  icon: "∿" },
    { id: "calibration",    label: "校正管理",   icon: "◎" },
    { id: "documents",      label: "文件管理",   icon: "≡" },
    { id: "library",        label: "文件庫",     icon: "📂" },
    { id: "training",       label: "訓練管理",   icon: "□" },
    { id: "equipment",      label: "設備保養",   icon: "⚙" },
    { id: "supplier",       label: "供應商管理",  icon: "◈" },
    { id: "nonconformance", label: "不符合管理",  icon: "⚠" },
    { id: "auditplan",      label: "稽核計畫",   icon: "✓" },
    { id: "environment",    label: "環境監測",   icon: "◉" },
    { id: "production",     label: "記錄匯出",   icon: "R" },
    { id: "notification",   label: "通知提醒",   icon: "✉" },
    { id: "aiworkbench",    label: "AI 工作台",  icon: "AI" },
    { id: "report",         label: "稽核報告",   icon: "☰" },
  ];
  const tabs = allTabs.filter(t => allowedTabs.includes(t.id));

  function setTabSafe(id) { if (allowedTabs.includes(id)) setActiveTab(id); }

  function renderTab() {
    switch(activeTab) {
      case "home":           return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setTabSafe} />;
      case "kpi":            return <KpiDashboard instruments={instruments} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} prodRecords={prodRecords} qualityRecords={qualityRecords} />;
      case "spc":            return <SpcTab prodRecords={prodRecords} />;
      case "calibration":    return <CalibrationTab instruments={instruments} setInstruments={setInstruments} />;
      case "documents":      return <DocumentsManagerTab documents={documents} setDocuments={setDocuments} manuals={manuals} />;
      case "library":        return <LibraryHierarchyTab documents={documents} manuals={manuals} />;
      case "training":       return <TrainingTab training={training} setTraining={setTraining} />;
      case "equipment":      return <EquipmentTab equipment={equipment} setEquipment={setEquipment} />;
      case "supplier":       return <SupplierTab suppliers={suppliers} setSuppliers={setSuppliers} />;
      case "nonconformance": return <NonConformanceTab nonConformances={nonConformances} setNonConformances={setNonConformances} highlightNcId={highlightNcId} onHighlightDone={() => setHighlightNcId(null)} expandNcId={expandNcId} onExpandDone={() => setExpandNcId(null)} />;
      case "auditplan":      return <AuditPlanTab auditPlans={auditPlans} setAuditPlans={setAuditPlans} />;
      case "environment":    return <EnvironmentTab envRecords={envRecords} setEnvRecords={setEnvRecords} />;
      case "production":     return <PageErrorBoundary pageName="記錄匯出" storageKeys={["audit_prodrecords", "audit_qualityrecords"]}><ProductionTab envRecords={envRecords} prodRecords={prodRecords} setProdRecords={setProdRecords} qualityRecords={qualityRecords} setQualityRecords={setQualityRecords} nonConformances={nonConformances} auditPlans={auditPlans} setActiveTab={setTabSafe} setHighlightNcId={setHighlightNcId} setExpandNcId={setExpandNcId} /></PageErrorBoundary>;
      case "notification":   return <NotificationTab instruments={instruments} documents={documents} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} />;
      case "aiworkbench":    return <AIWorkbenchTab documents={documents} manuals={manuals} nonConformances={nonConformances} />;
      case "report":         return <ReportTab instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} />;
      default:               return <DashboardHome instruments={instruments} documents={documents} training={training} equipment={equipment} suppliers={suppliers} nonConformances={nonConformances} auditPlans={auditPlans} envRecords={envRecords} setActiveTab={setTabSafe} />;
    }
  }

  const roleColors = { qms:"#3b82f6", executive:"#8b5cf6", supervisor:"#f59e0b", auditor:"#22c55e" };
  const roleColor = roleColors[userRole] || "#64748b";

  return (
    <ThemeContext.Provider value={theme}>
    <GlobalStyles isDark={darkMode} />
    <div style={{ minHeight:"100vh", background: theme.rootBg, color: theme.rootColor, fontFamily:"'Noto Sans TC', sans-serif", transition:"background 0.3s, color 0.3s" }}>
      {showChangePw && <ChangePasswordModal token={localStorage.getItem("qms_token")} onClose={() => setShowChangePw(false)} />}
      <div style={{ position:"sticky", top:0, zIndex:20, background: theme.navBg, borderBottom:`1px solid ${theme.panelBorder}`, backdropFilter:"blur(16px)", padding:"0 24px", boxShadow:"0 10px 30px rgba(2,6,23,0.12)" }}>
        <div style={{ display:"flex", alignItems:"center", gap:18, overflowX:"auto" }}>
          <div style={{ padding:"14px 0", minWidth:170, flexShrink:0 }}>
            <div style={{ fontSize:11, letterSpacing:1.4, textTransform:"uppercase", color: darkMode ? "#7dd3fc" : "#0284c7", fontWeight:800 }}>Jepei QMS</div>
            <div style={{ fontSize:15, color: theme.text, fontWeight:800, marginTop:4 }}>品質稽核工作台</div>
          </div>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`qms-nav-btn${activeTab === t.id ? " qms-nav-active" : ""}`}
              style={{
                background: activeTab === t.id ? (darkMode ? "rgba(56,189,248,0.14)" : "rgba(2,132,199,0.1)") : "transparent",
                border: activeTab === t.id ? (darkMode ? "1px solid rgba(56,189,248,0.28)" : "1px solid rgba(2,132,199,0.3)") : "1px solid transparent",
                cursor:"pointer", padding:"10px 14px", fontSize:12, fontWeight:700,
                color: activeTab === t.id ? (darkMode ? "#dbeafe" : "#0369a1") : theme.textMuted,
                borderRadius:12, whiteSpace:"nowrap", display:"flex", alignItems:"center", gap:8,
                margin:"10px 0",
              }}>
              <span style={{ fontSize:12, minWidth:24, height:24, display:"inline-flex", alignItems:"center", justifyContent:"center", borderRadius:999, background: activeTab === t.id ? "rgba(59,130,246,0.18)" : (darkMode ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)") }}>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
          {/* 使用者資訊 + 切換主題 + 登出 */}
          <div style={{ marginLeft:"auto", flexShrink:0, display:"flex", alignItems:"center", gap:10 }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, padding:"6px 12px", background: darkMode ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)", border:`1px solid ${roleColor}30`, borderRadius:10 }}>
              <div style={{ width:7, height:7, borderRadius:"50%", background:roleColor }} />
              <div style={{ fontSize:12, color: theme.textMuted }}>{authUser.display}</div>
            </div>
            {/* 主題切換按鈕 */}
            <button onClick={toggleTheme} title={darkMode ? "切換為淺色模式" : "切換為深色模式"}
              className="qms-tool-btn"
              style={{ background: darkMode ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)", border:`1px solid ${theme.panelBorder}`, borderRadius:8, padding:"6px 10px", fontSize:14, color: theme.textMuted, cursor:"pointer", lineHeight:1 }}>
              {darkMode ? "☀️" : "🌙"}
            </button>
            <button onClick={() => setShowChangePw(true)}
              className="qms-tool-btn"
              style={{ background: darkMode ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)", border:`1px solid ${theme.panelBorder}`, borderRadius:8, padding:"6px 10px", fontSize:11, color: theme.textMuted, cursor:"pointer" }}>
              改密碼
            </button>
            <button onClick={handleLogout}
              className="qms-logout-btn"
              style={{ background:"rgba(239,68,68,0.08)", border:"1px solid rgba(239,68,68,0.25)", borderRadius:8, padding:"6px 12px", fontSize:12, fontWeight:600, color:"#fca5a5", cursor:"pointer" }}>
              登出
            </button>
          </div>
        </div>
      </div>
      <div style={{ maxWidth:1460, margin:"0 auto", padding:"28px 24px 40px" }}>
        <div key={activeTab} className="qms-tab-content">
          {renderTab()}
        </div>
      </div>
    </div>
    </ThemeContext.Provider>
  );
}


