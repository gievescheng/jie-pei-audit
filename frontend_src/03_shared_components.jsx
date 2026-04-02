// ─── SHARED COMPONENTS ────────────────────────────────────────────────────────
const DARK_THEME = {
  isDark: true,
  panel: "linear-gradient(180deg, rgba(15,23,42,0.94) 0%, rgba(15,23,42,0.78) 100%)",
  panelSolid: "#0f172a",
  panelSoft: "rgba(255,255,255,0.035)",
  panelBorder: "rgba(148,163,184,0.16)",
  text: "#e2e8f0",
  textMuted: "#94a3b8",
  textSoft: "#64748b",
  shadow: "0 24px 60px rgba(2, 6, 23, 0.28)",
  navBg: "rgba(8,15,30,0.88)",
  rootBg: "radial-gradient(circle at top left, rgba(14,165,233,0.08), transparent 26%), linear-gradient(135deg, #08101f 0%, #0b1220 45%, #080d18 100%)",
  rootColor: "#e2e8f0",
  inputBg: "rgba(255,255,255,0.05)",
  inputBorder: "rgba(148,163,184,0.18)",
  inputColor: "#e2e8f0",
  modalBg: "#162033",
  modalBorder: "rgba(148,163,184,0.18)",
};

const LIGHT_THEME = {
  isDark: false,
  panel: "linear-gradient(180deg, rgba(255,255,255,0.97) 0%, rgba(248,250,252,0.92) 100%)",
  panelSolid: "#ffffff",
  panelSoft: "rgba(0,0,0,0.025)",
  panelBorder: "rgba(15,23,42,0.1)",
  text: "#0f172a",
  textMuted: "#475569",
  textSoft: "#94a3b8",
  shadow: "0 24px 60px rgba(15, 23, 42, 0.08)",
  navBg: "rgba(248,250,252,0.92)",
  rootBg: "radial-gradient(circle at top left, rgba(14,165,233,0.05), transparent 26%), linear-gradient(135deg, #f1f5f9 0%, #f8fafc 45%, #e8f0fe 100%)",
  rootColor: "#0f172a",
  inputBg: "rgba(15,23,42,0.04)",
  inputBorder: "rgba(15,23,42,0.14)",
  inputColor: "#0f172a",
  modalBg: "#ffffff",
  modalBorder: "rgba(15,23,42,0.12)",
};

const ThemeContext = React.createContext(DARK_THEME);

// 便利 hook：任何元件皆可取用目前主題
function useTheme() { return React.useContext(ThemeContext); }

// ── GlobalStyles：CSS 注入（hover / focus / animation / scrollbar）────────────
// 使用 CSS class 補足 inline style 無法表達的互動狀態，
// 避免每個按鈕都需要 onMouseEnter/Leave state。
function GlobalStyles({ isDark }) {
  useEffect(() => {
    const id = "qms-global-styles";
    let el = document.getElementById(id);
    if (!el) { el = document.createElement("style"); el.id = id; document.head.appendChild(el); }
    el.textContent = `
      /* ── 捲軸 ──────────────────────────────────────────── */
      ::-webkit-scrollbar { width: 6px; height: 6px; }
      ::-webkit-scrollbar-track { background: transparent; }
      ::-webkit-scrollbar-thumb {
        background: ${isDark ? "rgba(148,163,184,0.18)" : "rgba(15,23,42,0.15)"};
        border-radius: 3px;
      }
      ::-webkit-scrollbar-thumb:hover {
        background: ${isDark ? "rgba(148,163,184,0.32)" : "rgba(15,23,42,0.28)"};
      }

      /* ── 導覽列 Tab 按鈕 hover ──────────────────────────── */
      .qms-nav-btn { transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease !important; }
      .qms-nav-btn:hover:not(.qms-nav-active) {
        background: ${isDark ? "rgba(148,163,184,0.08)" : "rgba(15,23,42,0.06)"} !important;
        color: ${isDark ? "#cbd5e1" : "#334155"} !important;
        border-color: ${isDark ? "rgba(148,163,184,0.2)" : "rgba(15,23,42,0.12)"} !important;
      }
      .qms-nav-btn:active:not(.qms-nav-active) {
        background: ${isDark ? "rgba(148,163,184,0.12)" : "rgba(15,23,42,0.1)"} !important;
        transform: scale(0.98);
      }

      /* ── 右上角工具按鈕 hover ───────────────────────────── */
      .qms-tool-btn { transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease !important; }
      .qms-tool-btn:hover {
        background: ${isDark ? "rgba(255,255,255,0.09)" : "rgba(0,0,0,0.08)"} !important;
        border-color: ${isDark ? "rgba(148,163,184,0.3)" : "rgba(15,23,42,0.2)"} !important;
        color: ${isDark ? "#e2e8f0" : "#0f172a"} !important;
      }
      .qms-tool-btn:active { transform: scale(0.96); }

      /* ── 登出按鈕 hover ─────────────────────────────────── */
      .qms-logout-btn { transition: background 0.15s ease, border-color 0.15s ease !important; }
      .qms-logout-btn:hover {
        background: rgba(239,68,68,0.16) !important;
        border-color: rgba(239,68,68,0.45) !important;
        color: #fda4af !important;
      }
      .qms-logout-btn:active { transform: scale(0.96); }

      /* ── 通用 Action 按鈕 hover（使用 buttonStyle() 的按鈕）── */
      .qms-btn { transition: filter 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease !important; }
      .qms-btn:hover:not(:disabled):not([disabled]) {
        filter: brightness(1.12) saturate(1.05);
        transform: translateY(-1px);
      }
      .qms-btn:active:not(:disabled):not([disabled]) {
        filter: brightness(0.95);
        transform: translateY(0) scale(0.98);
      }

      /* ── 登入頁快捷帳號按鈕 hover ───────────────────────── */
      .qms-quick-btn { transition: background 0.15s ease, border-color 0.15s ease !important; }
      .qms-quick-btn:hover {
        background: ${isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.05)"} !important;
        border-color: ${isDark ? "rgba(255,255,255,0.15)" : "rgba(15,23,42,0.15)"} !important;
      }
      .qms-quick-btn:active { transform: scale(0.97); }

      /* ── Input / Textarea focus ring ────────────────────── */
      .qms-input:focus {
        outline: none !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.25) !important;
      }
      .qms-input { transition: border-color 0.15s ease, box-shadow 0.15s ease !important; }
      .qms-input::placeholder { color: ${isDark ? "rgba(148,163,184,0.45)" : "rgba(71,85,105,0.5)"}; }

      /* ── Tab 內容淡入動畫 ───────────────────────────────── */
      @keyframes qmsTabFadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      .qms-tab-content { animation: qmsTabFadeIn 0.18s ease-out both; }

      /* ── 減少動態偏好 ────────────────────────────────────── */
      @media (prefers-reduced-motion: reduce) {
        .qms-tab-content { animation: none !important; }
        .qms-nav-btn, .qms-tool-btn, .qms-logout-btn, .qms-btn, .qms-quick-btn, .qms-input {
          transition: none !important;
        }
        .qms-btn:hover, .qms-nav-btn:active, .qms-tool-btn:active, .qms-logout-btn:active,
        .qms-quick-btn:active { transform: none !important; }
      }

      /* ── 表格 light mode 底色修正 ────────────────────────── */
      .qms-table-shell-light {
        background: rgba(241,245,249,0.5) !important;
        border-color: rgba(15,23,42,0.1) !important;
      }
    `;
    return () => {};
  }, [isDark]);
  return null;
}

// 向下相容：若元件直接參照 uiTheme，改用此 proxy（請逐步遷移到 useTheme()）
const uiTheme = DARK_THEME; // 僅供靜態參照用，動態元件應使用 useTheme()

function buttonStyle(variant = "secondary", disabled = false, isDark = true) {
  const map = {
    primary: {
      background: "linear-gradient(135deg, #0284c7, #38bdf8)",
      color: "#fff",
      border: "none",
      boxShadow: "0 10px 24px rgba(14,165,233,0.22)",
    },
    secondary: {
      // 雙模式相容：深色用白色半透明，淺色用深色半透明
      background: isDark ? "rgba(255,255,255,0.045)" : "rgba(15,23,42,0.06)",
      color: isDark ? "#dbeafe" : "#334155",
      border: isDark ? "1px solid rgba(148,163,184,0.18)" : "1px solid rgba(15,23,42,0.15)",
      boxShadow: "none",
    },
    success: {
      background: "linear-gradient(135deg, #15803d, #22c55e)",
      color: "#fff",
      border: "none",
      boxShadow: "0 10px 24px rgba(34,197,94,0.18)",
    },
    warning: {
      background: "linear-gradient(135deg, #c2410c, #f97316)",
      color: "#fff",
      border: "none",
      boxShadow: "0 10px 24px rgba(249,115,22,0.18)",
    },
    danger: {
      background: "rgba(239,68,68,0.12)",
      color: isDark ? "#fecaca" : "#dc2626",
      border: "1px solid rgba(239,68,68,0.24)",
      boxShadow: "none",
    },
  };
  return {
    ...map[variant],
    borderRadius: 12,
    cursor: disabled ? "not-allowed" : "pointer",
    padding: "10px 16px",
    fontSize: 13,
    fontWeight: 700,
    opacity: disabled ? 0.6 : 1,
    transition: "all 0.2s ease",
  };
}

const tableShellStyle = {
  overflowX: "auto",
  background: "rgba(148, 163, 184, 0.06)",  // 雙模式相容：深色顯示為微亮面，淺色顯示為微灰面
  border: "1px solid rgba(148,163,184,0.14)",
  borderRadius: 16,
};

const tableHeadCellStyle = {
  padding: "12px 10px",
  borderBottom: "1px solid rgba(148,163,184,0.14)",
  color: "#94a3b8",
  fontSize: 12,
  fontWeight: 700,
  textAlign: "left",
  letterSpacing: 0.2,
};

const tableRowCellStyle = {
  padding: "9px 10px",
  borderBottom: "1px solid rgba(148,163,184,0.08)",
};

function PageIntro({ eyebrow, title, description, actions, children }) {
  const th = useTheme();
  return (
    <div style={{
      background: th.isDark
        ? "linear-gradient(180deg, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.72) 100%)"
        : "linear-gradient(180deg, rgba(255,255,255,0.97) 0%, rgba(241,245,249,0.88) 100%)",
      border: "1px solid " + th.panelBorder,
      borderRadius: 20,
      padding: 24,
      marginBottom: 20,
      boxShadow: th.shadow,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 20, alignItems: "flex-start", flexWrap: "wrap" }}>
        <div style={{ minWidth: 280, flex: 1 }}>
          {eyebrow && <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: "uppercase", color: th.isDark ? "#7dd3fc" : "#0284c7", fontWeight: 800, marginBottom: 10 }}>{eyebrow}</div>}
          <div style={{ fontSize: 28, lineHeight: 1.1, fontWeight: 800, color: th.text }}>{title}</div>
          {description && <div style={{ marginTop: 10, fontSize: 13, lineHeight: 1.8, color: th.textMuted, maxWidth: 760 }}>{description}</div>}
        </div>
        {actions && <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>{actions}</div>}
      </div>
      {children && <div style={{ marginTop: 18 }}>{children}</div>}
    </div>
  );
}

function Panel({ title, description, actions, accent = "#60a5fa", children, style = {} }) {
  const th = useTheme();
  return (
    <div style={{
      background: th.panel,
      border: `1px solid ${accent}28`,
      borderRadius: 18,
      padding: 20,
      boxShadow: th.shadow,
      ...style,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start", flexWrap: "wrap", marginBottom: 14 }}>
        <div style={{ minWidth: 220, flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <div style={{ width: 10, height: 10, borderRadius: 999, background: accent, boxShadow: `0 0 0 6px ${accent}18` }} />
            <div style={{ fontSize: 16, fontWeight: 800, color: th.text }}>{title}</div>
          </div>
          {description && <div style={{ fontSize: 12, color: th.textMuted, lineHeight: 1.7 }}>{description}</div>}
        </div>
        {actions && <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{actions}</div>}
      </div>
      {children}
    </div>
  );
}

function Badge({ color, children }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "4px 10px",
      borderRadius: 99,
      background: color + "18",
      color,
      fontSize: 12,
      fontWeight: 700,
      border: `1px solid ${color}38`,
      letterSpacing: 0.3,
    }}>{children}</span>
  );
}

class PageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("PageErrorBoundary", this.props.pageName || "page", error, info);
  }

  resetPageState = () => {
    try {
      const keys = Array.isArray(this.props.storageKeys) ? this.props.storageKeys : [];
      keys.forEach((key) => window.localStorage.removeItem(key));
    } catch (err) {
      console.warn("Failed to clear page storage", err);
    }
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ background:"rgba(127,29,29,0.18)", border:"1px solid rgba(248,113,113,0.35)", borderRadius:18, padding:24, color:"#fee2e2" }}>
        <div style={{ fontSize:24, fontWeight:800, marginBottom:10 }}>???????????</div>
        <div style={{ fontSize:14, lineHeight:1.8, color:"#fecaca", marginBottom:14 }}>
          {this.props.pageName || "????"} ???????????????????????????????????
        </div>
        <div style={{ fontSize:13, color:"#fde68a", marginBottom:16 }}>
          ?????{String(this.state.error && this.state.error.message || this.state.error || "????")}
        </div>
        <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
          <button onClick={this.resetPageState} style={{ background:"linear-gradient(135deg,#dc2626,#ef4444)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700 }}>
            ???????????
          </button>
          <button onClick={() => window.location.href='/?tab=home'} style={{ background:"rgba(255,255,255,0.08)", border:"1px solid rgba(255,255,255,0.15)", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700 }}>
            ?????
          </button>
        </div>
      </div>
    );
  }
}

function StatCard({ label, value, color, sub }) {
  const th = useTheme();
  return (
    <div style={{
      background: th.panel,
      border: "1px solid " + th.panelBorder,
      borderRadius: 18,
      padding: "22px 24px",
      flex: 1,
      minWidth: 150,
      borderTop: `3px solid ${color}`,
      boxShadow: th.shadow,
    }}>
      <div style={{ fontSize: 32, fontWeight: 800, color, fontFamily: "'DM Mono', monospace", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 13, color: th.textMuted, marginTop: 8, fontWeight: 700 }}>{label}</div>
      {sub && <div style={{ fontSize: 11, color: th.textSoft, marginTop: 6, lineHeight: 1.6 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title, count, color = "#60a5fa" }) {
  const th = useTheme();
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
      <div style={{ width: 5, height: 22, background: color, borderRadius: 3 }} />
      <h2 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: th.text }}>{title}</h2>
      {count !== undefined && (
        <span style={{ background: color + "18", color, borderRadius: 99, padding: "3px 10px", fontSize: 12, fontWeight: 700, border: `1px solid ${color}33` }}>{count}</span>
      )}
    </div>
  );
}

function Modal({ title, onClose, children }) {
  const th = useTheme();
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000,
      display: "flex", alignItems: "center", justifyContent: "center", padding: 20,
    }} onClick={onClose}>
      <div style={{
        background: th.modalBg, borderRadius: 20, padding: 32, maxWidth: 700, width: "100%",
        maxHeight: "85vh", overflow: "auto", border: "1px solid " + th.modalBorder,
        boxShadow: "0 32px 80px rgba(0,0,0,0.6)",
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h3 style={{ margin: 0, fontSize: 18, color: th.text, fontWeight: 800 }}>{title}</h3>
          <button onClick={onClose} style={{
            background: th.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)",
            border: "1px solid " + th.panelBorder, borderRadius: 10,
            color: th.textMuted, cursor: "pointer", padding: "8px 14px", fontSize: 13, fontWeight: 700,
          }}>✕ 關閉</button>
        </div>
        {children}
      </div>
    </div>
  );
}

const inputStyle = {
  background: "rgba(255,255,255,0.05)",
  border: "1px solid rgba(148,163,184,0.18)",
  borderRadius: 12,
  padding: "10px 12px",
  color: "#e2e8f0",
  fontSize: 14,
  width: "100%",
  boxSizing: "border-box",
  outline: "none",
};
