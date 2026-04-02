
// ─── HELPERS ──────────────────────────────────────────────────────────────────
const today = new Date();
today.setHours(0, 0, 0, 0);

function loadStoredState(key, fallback) {
  try {
    if (typeof window === "undefined") return fallback;
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw);
    return parsed ?? fallback;
  } catch (err) {
    console.warn("Failed to load " + key, err);
    return fallback;
  }
}

function saveStoredState(key, value) {
  try {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (err) {
    console.warn("Failed to save " + key, err);
  }
}

async function apiJson(url, options = {}) {
  const token = localStorage.getItem("qms_token");
  const headers = { ...(options.headers || {}) };
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = "Bearer " + token;
  }
  const response = await fetch(url, { ...options, headers });
  let payload = {};
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    const bodyText = await response.text();
    payload = bodyText ? { message: bodyText } : {};
  }
  if (response.status === 401) {
    // Token 過期或未登入 → 清除本地憑證並強制重新登入
    localStorage.removeItem("qms_token");
    localStorage.removeItem("qms_user");
    window.location.reload();
    return; // reload 後不繼續執行
  }
  if (!response.ok) {
    throw new Error(payload.error || payload.message || `Request failed (${response.status})`);
  }
  return payload;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

// 本地時間解析（避免 "YYYY-MM-DD" 被當 UTC 午夜 → UTC+8 偏移 -1 天的 bug）
function _parseLocalDate(dateStr) {
  if (!dateStr) return null;
  const parts = dateStr.split("-");
  if (parts.length !== 3) return null;
  const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  return isNaN(d.getTime()) ? null : d;
}

function daysUntil(dateStr) {
  if (!dateStr) return 9999;
  const d = _parseLocalDate(dateStr);
  if (!d) return 9999;
  d.setHours(0, 0, 0, 0);
  return Math.round((d - today) / 86400000);
}

function addDays(dateStr, days) {
  if (!dateStr) return "";
  const parts = dateStr.split("-");
  if (parts.length !== 3) return "";
  const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]) + days);
  if (isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function formatDate(dateStr) {
  if (!dateStr) return "?";
  const d = _parseLocalDate(dateStr);
  if (!d) return "?";
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
}

const opsFieldLabels = {
  scheduledDate: "預定日期",
  dept: "部門",
  scope: "稽核範圍",
  auditor: "稽核員",
  auditee: "受稽人",
  date: "發生日",
  description: "問題描述",
  responsible: "責任人",
  location: "地點",
};

function formatMissingFields(fields) {
  return (fields || []).map(field => opsFieldLabels[field] || field).join("、");
}

function urgencyColor(days) {
  if (days < 0) return "#ef4444";
  if (days <= 14) return "#f97316";
  if (days <= 30) return "#eab308";
  return "#22c55e";
}

function urgencyLabel(days) {
  if (days === 9999) return "無到期日";
  if (days < 0) return `逾期 ${Math.abs(days)} 天`;
  if (days === 0) return "今日到期";
  return `剩 ${days} 天`;
}

function urgencyBg(days) {
  if (days < 0) return "rgba(239,68,68,0.12)";
  if (days <= 14) return "rgba(249,115,22,0.12)";
  if (days <= 30) return "rgba(234,179,8,0.12)";
  return "rgba(34,197,94,0.08)";
}

function buildCalendarLink(item) {
  const start = String(item.date || "").replaceAll("-", "");
  const end = String(addDays(item.date, 1) || "").replaceAll("-", "");
  const details = [
    item.module ? "模組: " + item.module : "",
    item.summary ? "摘要: " + item.summary : "",
    item.owner ? "負責人: " + item.owner : "",
  ].filter(Boolean).join("\n");
  const params = new URLSearchParams({
    action: "TEMPLATE",
    text: item.title || "稽核提醒",
    dates: start + "/" + end,
    details,
  });
  return "https://calendar.google.com/calendar/render?" + params.toString();
}

function collectNotificationItems({ instruments, documents, equipment, suppliers, nonConformances, auditPlans }) {
  const items = [];

  instruments.forEach(inst => {
    const date = addDays(inst.calibratedDate, inst.intervalDays);
    const days = daysUntil(date);
    if (!date || days > 30) return;
    items.push({
      key: "instrument-" + inst.id,
      sourceType: "instrument",
      priority: days < 0 ? "high" : days <= 14 ? "medium" : "low",
      title: "儀器校正提醒：" + inst.name,
      module: "MP-05 量測資源管理",
      date,
      summary: `${inst.id} 下次校正日 ${formatDate(date)}，${urgencyLabel(days)}`,
      owner: inst.keeper || inst.location || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  documents.forEach(doc => {
    const date = addDays(doc.createdDate, 365);
    const days = daysUntil(date);
    if (!date || days > 45) return;
    items.push({
      key: "document-" + doc.id,
      sourceType: "document",
      priority: days < 0 ? "high" : "low",
      title: "文件年度審查：" + doc.name,
      module: "MP-01 文件化資訊管制",
      date,
      summary: `${doc.id} 建議年度審查日 ${formatDate(date)}，來源為建立日期加一年`,
      owner: doc.author || doc.department || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  equipment.forEach(eq => {
    const date = addDays(eq.lastMaintenance, eq.intervalDays);
    const days = daysUntil(date);
    if (!date || days > 30) return;
    items.push({
      key: "equipment-" + eq.id,
      sourceType: "equipment",
      priority: days < 0 ? "high" : days <= 14 ? "medium" : "low",
      title: "設備保養提醒：" + eq.name,
      module: "MP-04 設施設備管理",
      date,
      summary: `${eq.id} 下次保養日 ${formatDate(date)}，${urgencyLabel(days)}`,
      owner: eq.location || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  suppliers.forEach(supplier => {
    const date = addDays(supplier.lastEvalDate, supplier.evalIntervalDays);
    const days = daysUntil(date);
    if (!date || days > 30) return;
    items.push({
      key: "supplier-" + supplier.id,
      sourceType: "supplier",
      priority: days < 0 ? "high" : "low",
      title: "供應商評鑑提醒：" + supplier.name,
      module: "MP-10 採購及供應商管理",
      date,
      summary: `${supplier.id} 下次評鑑日 ${formatDate(date)}，目前評等 ${supplier.evalResult}`,
      owner: supplier.contact || supplier.category || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  nonConformances.forEach(nc => {
    const days = daysUntil(nc.dueDate);
    if (!nc.dueDate || nc.status === "已關閉" || days > 30) return;
    items.push({
      key: "nc-" + nc.id,
      sourceType: "nc",
      priority: days < 0 ? "high" : "medium",
      title: "矯正措施追蹤：" + nc.id,
      module: "MP-15 不符合及矯正措施",
      date: nc.dueDate,
      summary: `${nc.dept}，${nc.description}`,
      owner: nc.responsible || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  auditPlans.forEach(plan => {
    const days = daysUntil(plan.scheduledDate);
    if (!plan.scheduledDate || plan.status === "已完成" || days > 30) return;
    items.push({
      key: "audit-" + plan.id,
      sourceType: "audit",
      priority: days < 0 ? "high" : "medium",
      title: "內部稽核提醒：" + plan.dept,
      module: "MP-09 內部稽核管理",
      date: plan.scheduledDate,
      summary: `${plan.id} 稽核對象 ${plan.auditee}，稽核員 ${plan.auditor}`,
      owner: plan.auditor || "",
      days,
      statusText: urgencyLabel(days),
    });
  });

  return items.sort((a, b) => {
    const left = new Date(a.date).getTime();
    const right = new Date(b.date).getTime();
    return left - right;
  });
}
