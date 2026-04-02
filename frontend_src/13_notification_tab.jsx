function NotificationTab({ instruments, documents, equipment, suppliers, nonConformances, auditPlans }) {
  const items = collectNotificationItems({ instruments, documents, equipment, suppliers, nonConformances, auditPlans });
  const [googleStatus, setGoogleStatus] = useState({ configured: false, connected: false, email: "", redirect_uri: "" });
  const [googleForm, setGoogleForm] = useState({ client_id: "", client_secret: "" });
  const [googleBusy, setGoogleBusy] = useState("");
  const [googleMessage, setGoogleMessage] = useState("");
  const [notionForm, setNotionForm] = useState({ token: "", db_id: "" });
  const [notionBusyKey, setNotionBusyKey] = useState("");
  const [notionMessage, setNotionMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function loadStatus() {
      try {
        const response = await fetch("/api/google-calendar/status");
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
        if (!cancelled) setGoogleStatus(payload);
      } catch (err) {
        if (!cancelled) setGoogleMessage("讀取 Google 行事曆狀態失敗: " + err.message);
      }
    }
    loadStatus();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const googleState = params.get("google");
    if (!googleState) return;
    const reason = params.get("reason");
    setGoogleMessage(googleState === "connected" ? "Google 行事曆已完成授權。" : "Google 授權失敗: " + (reason || "unknown"));
    params.delete("google");
    params.delete("reason");
    params.set("tab", "notification");
    const next = window.location.pathname + "?" + params.toString();
    window.history.replaceState({}, "", next);
  }, []);

  async function refreshGoogleStatus() {
    const response = await fetch("/api/google-calendar/status");
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
    setGoogleStatus(payload);
  }

  async function saveGoogleConfig() {
    setGoogleBusy("config");
    setGoogleMessage("");
    try {
      const response = await fetch("/api/google-calendar/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(googleForm),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      setGoogleStatus(payload);
      setGoogleMessage("Google Calendar 設定已儲存。");
      setGoogleForm(prev => ({ ...prev, client_secret: "" }));
    } catch (err) {
      setGoogleMessage("Google Calendar 設定失敗: " + err.message);
    } finally {
      setGoogleBusy("");
    }
  }

  async function startGoogleAuth() {
    setGoogleBusy("auth");
    setGoogleMessage("");
    try {
      const response = await fetch("/api/google-calendar/auth/start");
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      window.location.href = payload.auth_url;
    } catch (err) {
      setGoogleMessage("啟動 Google 授權失敗: " + err.message);
      setGoogleBusy("");
    }
  }

  async function logoutGoogle() {
    setGoogleBusy("logout");
    setGoogleMessage("");
    try {
      const response = await fetch("/api/google-calendar/logout", { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      setGoogleStatus(payload);
      setGoogleMessage("Google 行事曆已中斷連線。");
    } catch (err) {
      setGoogleMessage("中斷 Google 行事曆失敗: " + err.message);
    } finally {
      setGoogleBusy("");
    }
  }

  async function createGoogleEvents(batchItems, mode) {
    if (!batchItems.length) {
      setGoogleMessage("目前沒有可建立的提醒項目。");
      return;
    }
    setGoogleBusy(mode);
    setGoogleMessage("");
    try {
      const response = await fetch("/api/google-calendar/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items: batchItems }),
      });
      const payload = await response.json();
      if (!response.ok && response.status !== 207) throw new Error(payload.error || ("HTTP " + response.status));
      const detail = (payload.results || []).filter(result => !result.success).map(result => result.title + ": " + result.error).join("；");
      setGoogleMessage(`Google 行事曆建立完成，成功 ${payload.success_count || 0} 筆，失敗 ${payload.failed_count || 0} 筆。${detail ? " 失敗明細：" + detail : ""}`);
      await refreshGoogleStatus();
    } catch (err) {
      setGoogleMessage("建立 Google 行事曆事件失敗: " + err.message);
    } finally {
      setGoogleBusy("");
    }
  }

  async function sendToNotion(item) {
    if (!notionForm.token || !notionForm.db_id) {
      setNotionMessage("請先輸入 Notion Token 與 Database ID。");
      return;
    }
    setNotionBusyKey(item.key);
    setNotionMessage("");
    try {
      const response = await fetch("/api/notion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: notionForm.token,
          db_id: notionForm.db_id,
          properties: {
            Name: { title: [{ text: { content: item.title } }] },
            Module: { rich_text: [{ text: { content: item.module } }] },
            Date: { date: { start: item.date } },
            Owner: { rich_text: [{ text: { content: item.owner || "" } }] },
            Summary: { rich_text: [{ text: { content: item.summary || "" } }] },
          },
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || payload.message || JSON.stringify(payload));
      setNotionMessage("已送出至 Notion: " + item.title);
    } catch (err) {
      setNotionMessage("Notion 建立失敗: " + err.message);
    } finally {
      setNotionBusyKey("");
    }
  }

  function openMailDraft(item) {
    const subject = encodeURIComponent(item.title);
    const body = encodeURIComponent([
      "日期: " + formatDate(item.date),
      "模組: " + item.module,
      "摘要: " + item.summary,
      "負責人: " + (item.owner || "未指定"),
    ].join("\n"));
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  }

  const overdueCount = items.filter(item => item.days < 0).length;
  const thisWeekCount = items.filter(item => item.days >= 0 && item.days <= 7).length;
  const moduleCounts = items.reduce((acc, item) => {
    acc[item.module] = (acc[item.module] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      <SectionHeader title="通知提醒" count={items.length} color="#f59e0b" />
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <StatCard label="提醒總數" value={items.length} color="#f59e0b" sub="30 天內需處理" />
        <StatCard label="已逾期" value={overdueCount} color="#ef4444" sub="優先處理" />
        <StatCard label="7 天內" value={thisWeekCount} color="#f97316" sub="近期排程" />
        <StatCard label="Google 狀態" value={googleStatus.connected ? "已連線" : googleStatus.configured ? "待授權" : "未設定"} color={googleStatus.connected ? "#22c55e" : googleStatus.configured ? "#eab308" : "#64748b"} sub={googleStatus.email || "primary calendar"} />
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"minmax(320px, 1.1fr) minmax(320px, 0.9fr)", gap:16, marginBottom:20 }}>
        <div style={{ background:"rgba(245,158,11,0.08)", border:"1px solid rgba(245,158,11,0.2)", borderRadius:14, padding:18 }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", gap:12, flexWrap:"wrap", marginBottom:12 }}>
            <div>
              <div style={{ fontSize:15, fontWeight:700, color:"#fef3c7" }}>Google 行事曆</div>
              <div style={{ fontSize:12, color:"#fcd34d", marginTop:4 }}>支援單筆或批次寫入 primary calendar。</div>
            </div>
            <Badge color={googleStatus.connected ? "#22c55e" : googleStatus.configured ? "#eab308" : "#94a3b8"}>{googleStatus.connected ? "已授權" : googleStatus.configured ? "待授權" : "未設定"}</Badge>
          </div>

          <div style={{ display:"grid", gridTemplateColumns:"1fr", gap:12 }}>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>Google Client ID</div>
              <input value={googleForm.client_id} onChange={e => setGoogleForm(prev => ({ ...prev, client_id: e.target.value }))} placeholder="貼上 Google OAuth Client ID" style={inputStyle} />
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>Google Client Secret</div>
              <input type="password" value={googleForm.client_secret} onChange={e => setGoogleForm(prev => ({ ...prev, client_secret: e.target.value }))} placeholder="貼上 Google OAuth Client Secret" style={inputStyle} />
            </div>
            <div style={{ fontSize:11, color:"#94a3b8", lineHeight:1.6 }}>
              Redirect URI: <span style={{ color:"#e2e8f0", fontFamily:"monospace" }}>{googleStatus.redirect_uri || "讀取中"}</span>
            </div>
          </div>

          <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginTop:14 }}>
            <button onClick={saveGoogleConfig} disabled={googleBusy !== ""} style={{ background:"linear-gradient(135deg,#b45309,#f59e0b)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: googleBusy ? 0.6 : 1 }}>{googleBusy === "config" ? "儲存中..." : "儲存設定"}</button>
            <button onClick={startGoogleAuth} disabled={googleBusy !== "" || !googleStatus.configured} style={{ background:"linear-gradient(135deg,#1d4ed8,#3b82f6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: (googleBusy || !googleStatus.configured) ? 0.6 : 1 }}>{googleBusy === "auth" ? "連線中..." : "連線 Google"}</button>
            <button onClick={() => createGoogleEvents(items, "batch")} disabled={googleBusy !== "" || !items.length} style={{ background:"linear-gradient(135deg,#0369a1,#0ea5e9)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: (googleBusy || !items.length) ? 0.6 : 1 }}>{googleBusy === "batch" ? "建立中..." : "全部建立 Google 事件"}</button>
            <button onClick={logoutGoogle} disabled={googleBusy !== "" || !googleStatus.connected} style={{ background:"rgba(239,68,68,0.14)", border:"1px solid rgba(239,68,68,0.3)", borderRadius:10, color:"#fca5a5", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity: (googleBusy || !googleStatus.connected) ? 0.6 : 1 }}>{googleBusy === "logout" ? "處理中..." : "中斷連線"}</button>
          </div>
          {googleMessage && <div style={{ marginTop:12, fontSize:12, color:"#fde68a", lineHeight:1.6 }}>{googleMessage}</div>}
        </div>

        <div style={{ background:"rgba(99,102,241,0.08)", border:"1px solid rgba(99,102,241,0.2)", borderRadius:14, padding:18 }}>
          <div style={{ marginBottom:12 }}>
            <div style={{ fontSize:15, fontWeight:700, color:"#e0e7ff" }}>Notion 與其他提醒方式</div>
            <div style={{ fontSize:12, color:"#c7d2fe", marginTop:4 }}>可逐筆送到 Notion，或退回用 Email / Google 建立頁。</div>
          </div>

          <div style={{ display:"grid", gap:12 }}>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>Notion Token</div>
              <input type="password" value={notionForm.token} onChange={e => setNotionForm(prev => ({ ...prev, token: e.target.value }))} placeholder="secret_xxx" style={inputStyle} />
            </div>
            <div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>Notion Database ID</div>
              <input value={notionForm.db_id} onChange={e => setNotionForm(prev => ({ ...prev, db_id: e.target.value }))} placeholder="貼上 Notion Database ID" style={inputStyle} />
            </div>
          </div>
          <div style={{ marginTop:14, fontSize:12, color:"#a5b4fc", lineHeight:1.7 }}>
            預設會寫入 `Name / Module / Date / Owner / Summary` 五個欄位。若你的資料庫欄位名稱不同，Notion 會直接回傳錯誤，畫面會顯示原始訊息。
          </div>
          {notionMessage && <div style={{ marginTop:12, fontSize:12, color:"#c7d2fe", lineHeight:1.6 }}>{notionMessage}</div>}
          <div style={{ marginTop:16 }}>
            <div style={{ fontSize:13, color:"#e2e8f0", fontWeight:700, marginBottom:8 }}>模組分布</div>
            <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
              {Object.entries(moduleCounts).map(([module, count]) => (
                <Badge key={module} color="#818cf8">{module} x {count}</Badge>
              ))}
              {items.length === 0 && <span style={{ fontSize:12, color:"#94a3b8" }}>目前沒有需要通知的資料。</span>}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
        {items.map(item => (
          <div key={item.key} style={{ background: urgencyBg(item.days), border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:16 }}>
            <div style={{ display:"flex", justifyContent:"space-between", gap:12, flexWrap:"wrap", alignItems:"flex-start" }}>
              <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
                  <div style={{ fontSize:15, fontWeight:700, color:"#e2e8f0" }}>{item.title}</div>
                  <Badge color={urgencyColor(item.days)}>{item.statusText}</Badge>
                  <Badge color="#60a5fa">{item.module}</Badge>
                </div>
                <div style={{ fontSize:13, color:"#cbd5e1", lineHeight:1.6 }}>{item.summary}</div>
                <div style={{ fontSize:12, color:"#94a3b8" }}>
                  日期 {formatDate(item.date)} {item.owner ? " / 負責人 " + item.owner : ""}
                </div>
              </div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap", justifyContent:"flex-end" }}>
                <button onClick={() => createGoogleEvents([item], "single:" + item.key)} disabled={googleBusy !== ""} style={{ background:"linear-gradient(135deg,#0369a1,#0ea5e9)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"9px 14px", fontSize:12, fontWeight:700, opacity: googleBusy ? 0.6 : 1 }}>{googleBusy === "single:" + item.key ? "建立中..." : "建立 Google 事件"}</button>
                <button onClick={() => window.open(buildCalendarLink(item), "_blank", "noopener,noreferrer")} style={{ background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.16)", borderRadius:10, color:"#e2e8f0", cursor:"pointer", padding:"9px 14px", fontSize:12, fontWeight:700 }}>開啟建立頁</button>
                <button onClick={() => sendToNotion(item)} disabled={notionBusyKey !== ""} style={{ background:"rgba(99,102,241,0.16)", border:"1px solid rgba(99,102,241,0.32)", borderRadius:10, color:"#c7d2fe", cursor:"pointer", padding:"9px 14px", fontSize:12, fontWeight:700, opacity: notionBusyKey ? 0.6 : 1 }}>{notionBusyKey === item.key ? "送出中..." : "送到 Notion"}</button>
                <button onClick={() => openMailDraft(item)} style={{ background:"rgba(245,158,11,0.14)", border:"1px solid rgba(245,158,11,0.3)", borderRadius:10, color:"#fde68a", cursor:"pointer", padding:"9px 14px", fontSize:12, fontWeight:700 }}>Email 草稿</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
