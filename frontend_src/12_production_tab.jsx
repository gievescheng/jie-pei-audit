function ProductionTab({ envRecords, prodRecords, setProdRecords, qualityRecords, setQualityRecords, nonConformances, auditPlans, setActiveTab, setHighlightNcId, setExpandNcId }) {
  const objectRows = (value) => Array.isArray(value) ? value.filter(item => item && typeof item === "object") : [];
  const safeEnvRecords = objectRows(envRecords);
  const safeProdRecords = objectRows(prodRecords);
  const safeQualityRecords = objectRows(qualityRecords);
  const safeNonConformances = objectRows(nonConformances);
  const safeAuditPlans = objectRows(auditPlans);
  const [downloadType, setDownloadType] = useState("");
  const [message, setMessage] = useState("");
  const [shipmentOrders, setShipmentOrders] = useState([]);
  const [shipmentLoading, setShipmentLoading] = useState(true);
  const [shipmentBusy, setShipmentBusy] = useState(false);
  const [shipmentMessage, setShipmentMessage] = useState("");
  const [shipmentOrderNo, setShipmentOrderNo] = useState("");
  const [shipmentForm, setShipmentForm] = useState({ date:"", department:"", requester:"", product_name:"", spec:"", quantity:"", unit:"", remark:"", batch_display:"" });
  const [selectedLots, setSelectedLots] = useState([]);
  const [engineCatalog, setEngineCatalog] = useState([]);
  const [engineTemplateCode, setEngineTemplateCode] = useState("shipping_pack");
  const [enginePrompt, setEnginePrompt] = useState("");
  const [engineSuggestions, setEngineSuggestions] = useState([]);
  const [engineBusy, setEngineBusy] = useState(false);
  const [engineMessage, setEngineMessage] = useState("");
  const [enginePrecheck, setEnginePrecheck] = useState(null);
  const [enginePrecheckBusy, setEnginePrecheckBusy] = useState(false);
  const [selectedNcId, setSelectedNcId] = useState("");
  const [recordReadBusy, setRecordReadBusy] = useState("");
  const [prodStartDate, setProdStartDate] = useState("");
  const [prodEndDate, setProdEndDate] = useState("");
  const [prodSiteFilter, setProdSiteFilter] = useState("ALL");
  const [prodSearch, setProdSearch] = useState("");
  const [expandedProdGroups, setExpandedProdGroups] = useState({});
  const [qualitySearch, setQualitySearch] = useState("");
  const [qualityResultFilter, setQualityResultFilter] = useState("ALL");
  const [expandedQualityGroups, setExpandedQualityGroups] = useState({});
  const prodSectionRef = useRef(null);
  const qualitySectionRef = useRef(null);
  const shipmentSectionRef = useRef(null);
  const shipmentFieldRefs = {
    date: useRef(null),
    department: useRef(null),
    requester: useRef(null),
    product_name: useRef(null),
    quantity: useRef(null),
    spec: useRef(null),
    unit: useRef(null),
    batch_display: useRef(null),
  };

  useEffect(() => {
    let cancelled = false;
    async function loadCatalog() {
      setShipmentLoading(true);
      try {
        const response = await fetch("/api/shipment-draft/catalog");
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
        if (!cancelled) {
          const orders = payload.orders || [];
          setShipmentOrders(orders);
          if (orders.length > 0) setShipmentOrderNo(prev => prev || orders[0].order_no);
        }
      } catch (err) {
        if (!cancelled) setShipmentMessage("讀取出貨單資料失敗: " + err.message);
      } finally {
        if (!cancelled) setShipmentLoading(false);
      }
    }
    loadCatalog();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadRecordEngineCatalog() {
      try {
        const response = await fetch("/api/record-engine/catalog");
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
        if (!cancelled) {
          const templates = payload.templates || [];
          setEngineCatalog(templates);
          if (templates.length > 0 && !templates.some(item => item.code === engineTemplateCode)) {
            setEngineTemplateCode(templates[0].code);
          }
        }
      } catch (err) {
        if (!cancelled) setEngineMessage("載入紀錄模板失敗: " + err.message);
      }
    }
    loadRecordEngineCatalog();
    return () => { cancelled = true; };
  }, []);

  const [selectedAuditId, setSelectedAuditId] = useState("");

  useEffect(() => {
    if (!selectedNcId && safeNonConformances.length > 0) {
      setSelectedNcId(safeNonConformances[0].id);
    }
  }, [safeNonConformances, selectedNcId]);

  useEffect(() => {
    if (!selectedAuditId && safeAuditPlans.length > 0) {
      setSelectedAuditId(safeAuditPlans[0].id);
    }
  }, [safeAuditPlans, selectedAuditId]);

  const selectedOrder = shipmentOrders.find(item => item.order_no === shipmentOrderNo) || null;

  useEffect(() => {
    if (!selectedOrder) return;
    setShipmentForm({
      date: selectedOrder.ship_date_suggested || "",
      department: selectedOrder.department_suggested || "",
      requester: selectedOrder.requester_suggested || "",
      product_name: selectedOrder.product_name_suggested || selectedOrder.source_product || "",
      spec: selectedOrder.spec_suggested || "",
      quantity: selectedOrder.quantity_suggested || "",
      unit: selectedOrder.unit_suggested || "",
      remark: selectedOrder.remark_suggested || "",
      batch_display: selectedOrder.batch_display_suggested || selectedOrder.order_no,
    });
    setSelectedLots([]);
    setShipmentMessage("");
  }, [shipmentOrderNo]);

  function updateProdRecord(index, field, value) {
    setProdRecords(prev => prev.map((row, i) => {
      if (i !== index) return row;
      const next = { ...row, [field]: value };
      if (field === "input" || field === "good" || field === "defect") {
        const input = Number(field === "input" ? value : next.input) || 0;
        const good = Number(field === "good" ? value : next.good) || 0;
        next.yieldRate = input ? Number((good / input * 100).toFixed(1)) : "";
      }
      return next;
    }));
  }

  function updateQualityRecord(index, field, value) {
    setQualityRecords(prev => prev.map((row, i) => i === index ? { ...row, [field]: value } : row));
  }

  function addProdRecord() {
    setProdRecords(prev => prev.concat({ lot:"LOT-" + String(prev.length + 1).padStart(3, "0"), customer:"", product:"", input:0, good:0, defect:0, yieldRate:"", defectReasons:[], operator:"", note:"" }));
  }

  function addQualityRecord() {
    setQualityRecords(prev => prev.concat({ materialName:"", batchNo:"", quantity:"", spec:"", inspQty:"", ph:"", density:"", ri:"", rotation:"", result:"PASS", note:"" }));
  }

  async function loadExistingRecordData(kind) {
    const isProduction = kind === "production";
    const label = isProduction ? "生產日報" : "品質檢驗記錄";
    if (!window.confirm(label + " 會覆蓋目前頁面中的暫存資料，確定要讀取既有紀錄嗎？")) return;
    setRecordReadBusy(kind);
    setMessage("");
    try {
      const response = await fetch(isProduction ? "/api/production-records/read-existing" : "/api/quality-records/read-existing");
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      const records = payload.records || [];
      if (isProduction) setProdRecords(records);
      else setQualityRecords(records);
      if (records.length === 0) {
        setMessage("目前沒有讀到可匯入的" + label + "。");
      } else {
        const shortPath = payload.source_file ? payload.source_file.split("\\").slice(-3).join("\\") : "";
        setMessage("已讀取 " + records.length + " 筆" + label + (shortPath ? "，來源：" + shortPath : "。"));
      }
    } catch (err) {
      setMessage("讀取" + label + "失敗：" + err.message);
    } finally {
      setRecordReadBusy("");
    }
  }

  async function importRecordFile(kind) {
    const isProduction = kind === "production";
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".xlsx,.xls";
    input.onchange = async () => {
      const file = input.files && input.files[0];
      if (!file) return;
      setRecordReadBusy(kind);
      setMessage("");
      try {
        const formData = new FormData();
        formData.append("file", file);
        const response = await fetch(
          isProduction ? "/api/production-records/import" : "/api/quality-records/import",
          { method: "POST", body: formData }
        );
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
        const records = payload.records || [];
        const label = isProduction ? "生產日報" : "品質記錄";
        if (!records.length) {
          setMessage("這份" + label + "沒有讀到可匯入的資料。");
          return;
        }
        const confirmed = window.confirm(
          "已從「" + (payload.source_file || file.name) + "」解析出 " + records.length + " 筆資料。\n是否用這批資料覆蓋目前頁面內容？"
        );
        if (!confirmed) {
          setMessage("已完成解析，但你暫時沒有覆蓋目前頁面資料。");
          return;
        }
        if (isProduction) setProdRecords(records);
        else setQualityRecords(records);
        setMessage("已匯入 " + records.length + " 筆" + label + "資料，來源：" + (payload.source_file || file.name));
      } catch (err) {
        setMessage("匯入失敗：" + err.message);
      } finally {
        setRecordReadBusy("");
      }
    };
    input.click();
  }

  function buildEnginePayload() {
    const selectedNc = safeNonConformances.find(item => item.id === selectedNcId) || safeNonConformances[0] || null;
    return {
      template_code: engineTemplateCode,
      prompt: enginePrompt,
      env_records: safeEnvRecords,
      prod_records: safeProdRecords,
      quality_records: safeQualityRecords,
      shipment_request: {
        order_no: shipmentOrderNo,
        selected_lots: selectedLots,
        ...shipmentForm,
      },
      nonconformance: selectedNc,
      all_nonconformances: safeNonConformances,
      audit_plans: safeAuditPlans,
      selected_audit_id: selectedAuditId,
    };
  }

  async function suggestRecordTemplates() {
    setEngineBusy(true);
    setEngineMessage("");
    setEnginePrecheck(null);
    try {
      const response = await fetch("/api/record-engine/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: enginePrompt,
          context: {
            env_count: envRecords.length,
            prod_count: prodRecords.length,
            quality_count: qualityRecords.length,
            shipment_order_count: shipmentOrders.length,
            nonconformance_count: safeNonConformances.length,
          },
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      const templates = payload.templates || [];
      setEngineSuggestions(templates.slice(0, 4));
      if (templates.length > 0) {
        setEngineTemplateCode(templates[0].code);
        setEngineMessage("已依目前提示與資料，找出較適合的模板。");
      } else {
        setEngineMessage("目前沒有可推薦的模板。");
      }
    } catch (err) {
      setEngineMessage("分析建議失敗: " + err.message);
    } finally {
      setEngineBusy(false);
    }
  }

  async function precheckRecordTemplate() {
    setEnginePrecheckBusy(true);
    setEngineMessage("");
    try {
      const response = await fetch("/api/record-engine/precheck", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildEnginePayload()),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || ("HTTP " + response.status));
      const result = payload.result || null;
      setEnginePrecheck(result);
      if (result && result.ready) {
        setEngineMessage("預檢完成：目前資料可以產生草稿。");
      } else if (result) {
        setEngineMessage("預檢完成：請先補齊必填欄位。");
      } else {
        setEngineMessage("預檢完成，但沒有取得結果。");
      }
    } catch (err) {
      setEngineMessage("預檢失敗: " + err.message);
    } finally {
      setEnginePrecheckBusy(false);
    }
  }

  async function generateEngineRecord() {
    if (enginePrecheck && enginePrecheck.ready === false) {
      setEngineMessage("目前仍有必填欄位未完成，請先依預檢結果補值。");
      return;
    }
    setEngineBusy(true);
    setEngineMessage("");
    try {
      const response = await fetch("/api/record-engine/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildEnginePayload()),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || ("HTTP " + response.status));
      }
      const selectedTemplate = engineCatalog.find(item => item.code === engineTemplateCode);
      const fallbackName = selectedTemplate ? (selectedTemplate.title + (selectedTemplate.bundle ? ".zip" : ".xlsx")) : "紀錄草稿.xlsx";
      downloadBlob(await response.blob(), fallbackName);
      setEngineMessage("已產生 " + (selectedTemplate ? selectedTemplate.title : "紀錄草稿") + "。");
    } catch (err) {
      setEngineMessage("產生紀錄失敗: " + err.message);
    } finally {
      setEngineBusy(false);
    }
  }

  function jumpToMissingDetail(detail) {
    if (!detail || typeof window === "undefined") return;
    const focusField = (refObject) => {
      const el = refObject && refObject.current;
      if (!el) return false;
      el.focus();
      if (typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return true;
    };

    const scrollToRef = (refObject) => {
      const el = refObject && refObject.current;
      if (!el || typeof el.scrollIntoView !== "function") return false;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    };

    if (detail.scope === "production") {
      scrollToRef(prodSectionRef);
      setEngineMessage("已定位到生產批次區塊，請先補上生產資料。");
      return;
    }
    if (detail.scope === "quality") {
      scrollToRef(qualitySectionRef);
      setEngineMessage("已定位到進料檢驗區塊，請先補上品質資料。");
      return;
    }
    if (detail.scope === "shipment") {
      scrollToRef(shipmentSectionRef);
      const fieldRef = shipmentFieldRefs[detail.field_key];
      if (fieldRef) {
        setTimeout(() => focusField(fieldRef), 120);
      }
      setEngineMessage("已定位到出貨單草稿欄位：" + (detail.label || detail.field_key));
      return;
    }
    if (detail.scope === "nonconformance") {
      setActiveTab("nonconformance");
      const targetId = detail.item_id || selectedNcId;
      if (targetId) {
        setHighlightNcId(targetId);
        setExpandNcId?.(targetId);
      }
      setEngineMessage("已切換到不符合管理，請補齊「" + (detail.label || detail.field_key || "必要欄位") + "」。");
      return;
    }
    if (detail.scope === "environment") {
      setActiveTab("environment");
      setEngineMessage("已切換到工作環境監控，請先上傳環境監控資料。");
      return;
    }
    if (detail.scope === "audit_plans") {
      setActiveTab("auditplan");
      setEngineMessage("已切換到稽核計畫，請補齊「" + (detail.label || detail.field_key || "必要欄位") + "」。");
      return;
    }
  }

  async function downloadRecords(type, data, fallbackName) {
    setDownloadType(type);
    setMessage("");
    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, data }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || ("HTTP " + response.status));
      }
      downloadBlob(await response.blob(), fallbackName);
      setMessage("已下載 " + fallbackName);
    } catch (err) {
      setMessage("下載失敗: " + err.message);
    } finally {
      setDownloadType("");
    }
  }

  async function generateShipmentDraft() {
    if (!shipmentOrderNo) {
      setShipmentMessage("請先選擇訂單。");
      return;
    }
    setShipmentBusy(true);
    setShipmentMessage("");
    try {
      const response = await fetch("/api/shipment-draft/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_no: shipmentOrderNo, selected_lots: selectedLots, ...shipmentForm }),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || ("HTTP " + response.status));
      }
      downloadBlob(await response.blob(), shipmentOrderNo + "_出貨單草稿.xlsx");
      setShipmentMessage("已產生出貨單草稿。");
    } catch (err) {
      setShipmentMessage("出貨單草稿產生失敗: " + err.message);
    } finally {
      setShipmentBusy(false);
    }
  }

  const prodLowYield = safeProdRecords.filter(row => Number(row?.yieldRate) < 95).length;
  const qualityNg = safeQualityRecords.filter(row => ["NG", "FAIL"].includes(String(row?.result || "").toUpperCase())).length;
  const envWarning = safeEnvRecords.filter(row => row.result && row.result !== "合格").length;

  const normalizeDateText = (value) => {
    const source = String(value || "").trim();
    if (!source) return "";
    const normalized = source.replace(/\//g, "-");
    const match = normalized.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (match) {
      return `${match[1]}-${match[2].padStart(2, "0")}-${match[3].padStart(2, "0")}`;
    }
    return normalized;
  };

  const extractProdSite = (row) => {
    const note = String(row?.note || "");
    const siteMatch = note.match(/site\s*:\s*([a-z0-9_-]+)/i);
    if (siteMatch) return siteMatch[1].toUpperCase();
    const lot = String(row?.lot || "");
    const lotMatch = lot.match(/([A-Z]{2,5})$/);
    if (lotMatch) return lotMatch[1].toUpperCase();
    return "未填站點";
  };

  const getProdRowIssues = (row) => {
    const issues = [];
    if (!String(row?.lot || "").trim()) issues.push("批號");
    if (!String(row?.customer || "").trim()) issues.push("客戶");
    if (!String(row?.product || "").trim()) issues.push("產品");
    if (!(Number(row?.input) > 0)) issues.push("投入數");
    if (!String(row?.operator || "").trim()) issues.push("作業員");
    return issues;
  };

  const prodRows = safeProdRecords.map((row, index) => ({
    row,
    index,
    normalizedDate: normalizeDateText(row.date || row.recordDate || row.created_at || ""),
    site: extractProdSite(row),
  }));

  const prodSiteOptions = Array.from(new Set(prodRows.map(item => item.site))).sort((a, b) => a.localeCompare(b, "zh-Hant"));
  const prodDateOptions = Array.from(new Set(prodRows.map(item => item.normalizedDate).filter(Boolean))).sort();
  const prodSearchKeyword = prodSearch.trim().toLowerCase();
  const filteredProdRows = prodRows.filter(({ row, normalizedDate, site }) => {
    if ((prodStartDate || prodEndDate) && !normalizedDate) return false;
    if (prodStartDate && normalizedDate < prodStartDate) return false;
    if (prodEndDate && normalizedDate > prodEndDate) return false;
    if (prodSiteFilter !== "ALL" && site !== prodSiteFilter) return false;
    if (!prodSearchKeyword) return true;
    const haystack = [
      row.lot,
      row.customer,
      row.product,
      row.operator,
      row.note,
      site,
    ].join(" ").toLowerCase();
    return haystack.includes(prodSearchKeyword);
  });

  const prodGroups = filteredProdRows.reduce((acc, item) => {
    const dateLabel = item.normalizedDate || "未填日期";
    const key = `${dateLabel}__${item.site}`;
    if (!acc[key]) {
      acc[key] = {
        key,
        date: dateLabel,
        site: item.site,
        items: [],
        totalInput: 0,
        totalGood: 0,
        totalDefect: 0,
        issueCount: 0,
      };
    }
    acc[key].items.push(item);
    acc[key].totalInput += Number(item.row.input) || 0;
    acc[key].totalGood += Number(item.row.good) || 0;
    acc[key].totalDefect += Number(item.row.defect) || 0;
    acc[key].issueCount += getProdRowIssues(item.row).length > 0 ? 1 : 0;
    return acc;
  }, {});

  const prodGroupList = Object.values(prodGroups)
    .map(group => ({
      ...group,
      avgYield: group.totalInput ? Number(((group.totalGood / group.totalInput) * 100).toFixed(1)) : 0,
    }))
    .sort((a, b) => `${b.date} ${b.site}`.localeCompare(`${a.date} ${a.site}`));

  const latestProdDate = prodDateOptions.length ? prodDateOptions[prodDateOptions.length - 1] : "";

  const setProdPresetRange = (preset) => {
    if (!prodDateOptions.length) return;
    if (preset === "all") {
      setProdStartDate("");
      setProdEndDate("");
      return;
    }
    if (preset === "latest") {
      setProdStartDate(latestProdDate);
      setProdEndDate(latestProdDate);
      return;
    }
    const days = preset === "7d" ? 7 : 30;
    const latest = new Date(`${latestProdDate}T00:00:00`);
    if (Number.isNaN(latest.getTime())) return;
    const start = new Date(latest);
    start.setDate(start.getDate() - (days - 1));
    const fmt = (value) => {
      const year = value.getFullYear();
      const month = String(value.getMonth() + 1).padStart(2, "0");
      const day = String(value.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };
    setProdStartDate(fmt(start));
    setProdEndDate(latestProdDate);
  };

  const toggleProdGroup = (key) => {
    setExpandedProdGroups(prev => ({ ...prev, [key]: !(prev[key] ?? false) }));
  };

  const toggleAllProdGroups = (expanded) => {
    const next = {};
    prodGroupList.forEach(group => {
      next[group.key] = expanded;
    });
    setExpandedProdGroups(next);
  };

  const getQualityRowIssues = (row) => {
    const issues = [];
    if (!String(row?.materialName || "").trim()) issues.push("材料名稱");
    if (!String(row?.batchNo || "").trim()) issues.push("批號");
    if (!String(row?.spec || "").trim()) issues.push("規格");
    if (!String(row?.result || "").trim()) issues.push("結果");
    return issues;
  };

  const qualityRows = safeQualityRecords.map((row, index) => ({
    row,
    index,
    materialName: String(row.materialName || "未填材料").trim() || "未填材料",
    resultLabel: String(row.result || "未判定").trim() || "未判定",
    normalizedResult: (String(row.result || "").trim() || "未判定").toUpperCase(),
  }));

  const qualitySearchKeyword = qualitySearch.trim().toLowerCase();
  const normalizedQualityFilter = String(qualityResultFilter || "ALL").toUpperCase();
  const filteredQualityRows = qualityRows.filter(({ row, materialName, resultLabel, normalizedResult }) => {
    if (normalizedQualityFilter !== "ALL" && normalizedResult !== normalizedQualityFilter) return false;
    if (!qualitySearchKeyword) return true;
    const haystack = [
      materialName,
      row.batchNo,
      row.spec,
      row.note,
      resultLabel,
    ].join(" ").toLowerCase();
    return haystack.includes(qualitySearchKeyword);
  });

  const qualityGroups = filteredQualityRows.reduce((acc, item) => {
    if (!acc[item.materialName]) {
      acc[item.materialName] = {
        key: item.materialName,
        materialName: item.materialName,
        items: [],
        ngCount: 0,
        issueCount: 0,
      };
    }
    acc[item.materialName].items.push(item);
    if (["NG", "FAIL"].includes(item.resultLabel.toUpperCase())) acc[item.materialName].ngCount += 1;
    if (getQualityRowIssues(item.row).length > 0) acc[item.materialName].issueCount += 1;
    return acc;
  }, {});

  const qualityGroupList = Object.values(qualityGroups).sort((a, b) => a.materialName.localeCompare(b.materialName, "zh-Hant"));
  const filteredQualityNg = filteredQualityRows.filter(item => ["NG", "FAIL"].includes(item.resultLabel.toUpperCase())).length;

  const toggleQualityGroup = (key) => {
    setExpandedQualityGroups(prev => ({ ...prev, [key]: !(prev[key] ?? false) }));
  };

  const toggleAllQualityGroups = (expanded) => {
    const next = {};
    qualityGroupList.forEach(group => {
      next[group.key] = expanded;
    });
    setExpandedQualityGroups(next);
  };

  const getShipmentFormIssues = () => {
    const issues = [];
    if (!String(shipmentForm.date || "").trim()) issues.push("日期");
    if (!String(shipmentForm.department || "").trim()) issues.push("部門");
    if (!String(shipmentForm.requester || "").trim()) issues.push("申請人");
    if (!String(shipmentForm.product_name || "").trim()) issues.push("產品");
    if (!String(shipmentForm.quantity || "").trim()) issues.push("數量");
    return issues;
  };

  const shipmentIssues = getShipmentFormIssues();
  const shipmentSuggestions = [];
  if (!String(shipmentForm.spec || "").trim()) shipmentSuggestions.push("規格");
  if (!String(shipmentForm.unit || "").trim()) shipmentSuggestions.push("單位");
  if (!String(shipmentForm.batch_display || "").trim()) shipmentSuggestions.push("訂單編號 / 批號顯示");
  const shipmentLots = selectedOrder && Array.isArray(selectedOrder.lots) ? selectedOrder.lots : [];
  const selectedLotCount = selectedLots.length;
  const shipmentSummaryCardStyle = {
    background: "rgba(15,23,42,0.72)",
    border: "1px solid rgba(167,139,250,0.18)",
    borderRadius: 14,
    boxShadow: "0 16px 36px rgba(15,23,42,0.16)",
    padding: 14,
  };
  const selectedEngineTemplate = engineCatalog.find(item => item.code === engineTemplateCode) || null;

  return (
    <div>
      <PageIntro
        eyebrow="QMS Record Workspace"
        title="記錄匯出"
        description="這一頁負責整理生產、品質、環境與出貨相關記錄。你可以先讀取既有正式資料，再做微調、匯出，或交給紀錄生成引擎產出下游草稿。"
        actions={
          <>
            <button onClick={() => downloadRecords("production", prodRecords, "生產記錄.xlsx")} disabled={downloadType !== ""} style={buttonStyle("primary", downloadType !== "" && downloadType !== "production")}>{downloadType === "production" ? "下載中..." : "下載生產記錄"}</button>
            <button onClick={() => downloadRecords("quality", qualityRecords, "品質檢驗記錄.xlsx")} disabled={downloadType !== ""} style={buttonStyle("success", downloadType !== "" && downloadType !== "quality")}>{downloadType === "quality" ? "下載中..." : "下載品質檢驗記錄"}</button>
            <button onClick={() => downloadRecords("env", envRecords, "環境監測記錄.xlsx")} disabled={downloadType !== ""} style={buttonStyle("secondary", downloadType !== "" && downloadType !== "env")}>{downloadType === "env" ? "下載中..." : "下載環境監測記錄"}</button>
          </>
        }
      >
        <div style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
          <StatCard label="生產記錄" value={safeProdRecords.length} color="#38bdf8" sub={prodLowYield > 0 ? prodLowYield + " 批低良率" : "良率正常"} />
          <StatCard label="進料檢驗" value={safeQualityRecords.length} color="#22c55e" sub={qualityNg > 0 ? qualityNg + " 批異常" : "全部合格"} />
          <StatCard label="環境監測" value={safeEnvRecords.length} color="#14b8a6" sub={envWarning > 0 ? envWarning + " 筆警示" : "無警示"} />
        </div>
        {message && <div style={{ marginTop:14, fontSize:12, color:"#bae6fd" }}>{message}</div>}
      </PageIntro>

      <div ref={prodSectionRef}>
      <Panel
        title="生產批次"
        description="先用日期、站點與關鍵字縮小範圍，再查看每日生產批次。你可以讀取既有生產日報、匯入新檔案，或直接編修後匯出生產記錄。"
        accent="#38bdf8"
        actions={
          <>
            <button onClick={() => loadExistingRecordData("production")} disabled={recordReadBusy !== ""} style={buttonStyle("secondary", recordReadBusy !== "" && recordReadBusy !== "production")}>{recordReadBusy === "production" ? "讀取中..." : "讀取既有生產日報"}</button>
            <button onClick={() => importRecordFile("production")} disabled={recordReadBusy !== ""} style={buttonStyle("secondary", recordReadBusy !== "" && recordReadBusy !== "production")}>{recordReadBusy === "production" ? "匯入中..." : "匯入生產日報"}</button>
            <button onClick={addProdRecord} style={buttonStyle("primary")}>新增列</button>
          </>
        }
        style={{ marginBottom: 20 }}
      >
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4, minmax(180px, 1fr))", gap:12, marginBottom:14 }}>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>開始日期</div>
            <input type="date" value={prodStartDate} onChange={e => setProdStartDate(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>結束日期</div>
            <input type="date" value={prodEndDate} onChange={e => setProdEndDate(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>站點</div>
            <select value={prodSiteFilter} onChange={e => setProdSiteFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">全部站點</option>
              {prodSiteOptions.map(site => <option key={site} value={site}>{site}</option>)}
            </select>
          </div>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>關鍵字</div>
            <input value={prodSearch} onChange={e => setProdSearch(e.target.value)} placeholder="可搜尋批號、客戶、產品、站點或作業員" style={inputStyle} />
          </div>
        </div>

        <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:14 }}>
          <button onClick={() => setProdPresetRange("latest")} style={buttonStyle("secondary")}>最新一天</button>
          <button onClick={() => setProdPresetRange("7d")} style={buttonStyle("secondary")}>最近 7 天</button>
          <button onClick={() => setProdPresetRange("30d")} style={buttonStyle("secondary")}>最近 30 天</button>
          <button onClick={() => setProdPresetRange("all")} style={buttonStyle("secondary")}>清除日期</button>
          <button onClick={() => toggleAllProdGroups(true)} style={buttonStyle("secondary")}>全部展開</button>
          <button onClick={() => toggleAllProdGroups(false)} style={buttonStyle("secondary")}>全部收合</button>
        </div>

        <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginBottom:16 }}>
          <Badge color="#38bdf8">{filteredProdRows.length} 筆可視資料</Badge>
          <Badge color="#22c55e">{prodGroupList.length} 個日期 / 站點群組</Badge>
          <Badge color={filteredProdRows.filter(item => getProdRowIssues(item.row).length > 0).length > 0 ? "#f59e0b" : "#22c55e"}>
            {filteredProdRows.filter(item => getProdRowIssues(item.row).length > 0).length} 筆待補欄位
          </Badge>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
          {prodGroupList.length === 0 && (
            <div style={{ ...tableShellStyle, padding:18, color:"#94a3b8", fontSize:13 }}>
              目前沒有符合篩選條件的生產資料。你可以先調整日期、站點或關鍵字，或先讀取既有生產日報。
            </div>
          )}

          {prodGroupList.map(group => (
            <div key={group.key} style={{ ...tableShellStyle, overflow:"hidden" }}>
              <div style={{ display:"flex", justifyContent:"space-between", gap:12, flexWrap:"wrap", alignItems:"center", padding:"14px 16px", borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
                <div>
                  <div style={{ fontSize:18, fontWeight:800, color:"#e2e8f0" }}>{group.date} / {group.site}</div>
                  <div style={{ fontSize:12, color:"#94a3b8", marginTop:4 }}>
                    {group.items.length} 筆，投入 {group.totalInput}，良品 {group.totalGood}，不良 {group.totalDefect}
                  </div>
                </div>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
                  {group.issueCount > 0 && <Badge color="#f59e0b">{group.issueCount} 筆待補欄位</Badge>}
                  <Badge color={group.avgYield < 95 ? "#f59e0b" : "#22c55e"}>平均良率 {group.avgYield}%</Badge>
                  <button onClick={() => toggleProdGroup(group.key)} style={buttonStyle("secondary")}>
                    {(expandedProdGroups[group.key] ?? true) ? "收合明細" : "展開明細"}
                  </button>
                </div>
              </div>

              {(expandedProdGroups[group.key] ?? true) && (
                <div style={{ overflowX:"auto" }}>
                  <table style={{ width:"100%", borderCollapse:"collapse", minWidth:980 }}>
                    <thead><tr>{["批號","客戶","產品","投入數","良品數","不良數","良率 %","不良原因","作業員","備註",""].map(head => <th key={head} style={tableHeadCellStyle}>{head}</th>)}</tr></thead>
                    <tbody>
                      {group.items.map(({ row, index }) => {
                        const issues = getProdRowIssues(row);
                        const issueSet = new Set(issues);
                        const flaggedStyle = (label) => issueSet.has(label)
                          ? { ...inputStyle, borderColor:"rgba(245,158,11,0.55)", background:"rgba(245,158,11,0.08)" }
                          : inputStyle;
                        return (
                          <tr key={(row.lot || "LOT") + "-" + index}>
                            <td style={tableRowCellStyle}><input value={row.lot} onChange={e => updateProdRecord(index, "lot", e.target.value)} style={flaggedStyle("批號")} /></td>
                            <td style={tableRowCellStyle}><input value={row.customer} onChange={e => updateProdRecord(index, "customer", e.target.value)} style={flaggedStyle("客戶")} /></td>
                            <td style={tableRowCellStyle}><input value={row.product} onChange={e => updateProdRecord(index, "product", e.target.value)} style={flaggedStyle("產品")} /></td>
                            <td style={tableRowCellStyle}><input type="number" value={row.input} onChange={e => updateProdRecord(index, "input", e.target.value)} style={flaggedStyle("投入數")} /></td>
                            <td style={tableRowCellStyle}><input type="number" value={row.good} onChange={e => updateProdRecord(index, "good", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input type="number" value={row.defect} onChange={e => updateProdRecord(index, "defect", e.target.value)} style={inputStyle} /></td>
                            <td style={{ ...tableRowCellStyle, color:Number(row.yieldRate) < 95 ? "#fca5a5" : "#86efac", fontWeight:700 }}>{row.yieldRate === "" ? "--" : row.yieldRate}</td>
                            <td style={tableRowCellStyle}><input value={Array.isArray(row.defectReasons) ? row.defectReasons.join(", ") : row.defectReasons} onChange={e => updateProdRecord(index, "defectReasons", e.target.value.split(/[;,]/).map(item => item.trim()).filter(Boolean))} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.operator} onChange={e => updateProdRecord(index, "operator", e.target.value)} style={flaggedStyle("作業員")} /></td>
                            <td style={tableRowCellStyle}><input value={row.note} onChange={e => updateProdRecord(index, "note", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}>
                              <div style={{ display:"flex", flexDirection:"column", gap:6, alignItems:"flex-start" }}>
                                <button onClick={() => setProdRecords(prev => prev.filter((_, i) => i !== index))} style={buttonStyle("danger")}>刪除</button>
                                {issues.length > 0 && <span style={{ fontSize:11, color:"#fcd34d" }}>待補：{issues.join(" / ")}</span>}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>
      </div>

      <div ref={qualitySectionRef}>
      <Panel
        title="進料檢驗"
        description="先用關鍵字與結果縮小範圍，再查看每一種材料的檢驗結果。你可以讀取既有品質記錄、匯入新檔案，或直接補值後匯出。"
        accent="#22c55e"
        actions={
          <>
            <button onClick={() => loadExistingRecordData("quality")} disabled={recordReadBusy !== ""} style={buttonStyle("secondary", recordReadBusy !== "" && recordReadBusy !== "quality")}>{recordReadBusy === "quality" ? "讀取中..." : "讀取既有品質記錄"}</button>
            <button onClick={() => importRecordFile("quality")} disabled={recordReadBusy !== ""} style={buttonStyle("secondary", recordReadBusy !== "" && recordReadBusy !== "quality")}>{recordReadBusy === "quality" ? "匯入中..." : "匯入品質記錄"}</button>
            <button onClick={addQualityRecord} style={buttonStyle("success")}>新增列</button>
          </>
        }
        style={{ marginBottom: 20 }}
      >
        <div style={{ display:"grid", gridTemplateColumns:"minmax(240px, 2fr) minmax(180px, 1fr)", gap:12, marginBottom:14 }}>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>關鍵字</div>
            <input value={qualitySearch} onChange={e => setQualitySearch(e.target.value)} placeholder="可搜尋材料名稱、批號、規格或結果" style={inputStyle} />
          </div>
          <div>
            <div style={{ fontSize:12, color:"#94a3b8", marginBottom:6 }}>結果</div>
            <select value={qualityResultFilter} onChange={e => setQualityResultFilter(e.target.value)} style={inputStyle}>
              <option value="ALL">全部結果</option>
              <option value="PASS">PASS</option>
              <option value="NG">NG</option>
              <option value="FAIL">FAIL</option>
            </select>
          </div>
        </div>

        <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:14 }}>
          <button onClick={() => setQualitySearch("")} style={buttonStyle("secondary")}>清除關鍵字</button>
          <button onClick={() => setQualityResultFilter("ALL")} style={buttonStyle("secondary")}>全部結果</button>
          <button onClick={() => toggleAllQualityGroups(true)} style={buttonStyle("secondary")}>全部展開</button>
          <button onClick={() => toggleAllQualityGroups(false)} style={buttonStyle("secondary")}>全部收合</button>
        </div>

        <div style={{ display:"flex", gap:10, flexWrap:"wrap", marginBottom:16 }}>
          <Badge color="#22c55e">{filteredQualityRows.length} 筆檢驗資料</Badge>
          <Badge color="#38bdf8">{qualityGroupList.length} 個材料群組</Badge>
          <Badge color={filteredQualityNg > 0 ? "#ef4444" : "#22c55e"}>{filteredQualityNg} 筆異常</Badge>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
          {qualityGroupList.length === 0 && (
            <div style={{ ...tableShellStyle, padding:18, color:"#94a3b8", fontSize:13 }}>
              目前沒有符合篩選條件的品質檢驗資料。你可以先調整關鍵字與結果，或先讀取既有品質記錄。
            </div>
          )}

          {qualityGroupList.map(group => (
            <div key={group.key} style={{ ...tableShellStyle, overflow:"hidden" }}>
              <div style={{ display:"flex", justifyContent:"space-between", gap:12, flexWrap:"wrap", alignItems:"center", padding:"14px 16px", borderBottom:"1px solid rgba(255,255,255,0.06)" }}>
                <div>
                  <div style={{ fontSize:18, fontWeight:800, color:"#e2e8f0" }}>{group.materialName}</div>
                  <div style={{ fontSize:12, color:"#94a3b8", marginTop:4 }}>
                    {group.items.length} 筆，其中異常 {group.ngCount} 筆
                  </div>
                </div>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
                  {group.issueCount > 0 && <Badge color="#f59e0b">{group.issueCount} 筆待補欄位</Badge>}
                  <Badge color={group.ngCount > 0 ? "#ef4444" : "#22c55e"}>{group.ngCount > 0 ? "有異常" : "目前正常"}</Badge>
                  <button onClick={() => toggleQualityGroup(group.key)} style={buttonStyle("secondary")}>
                    {(expandedQualityGroups[group.key] ?? true) ? "收合明細" : "展開明細"}
                  </button>
                </div>
              </div>

              {(expandedQualityGroups[group.key] ?? true) && (
                <div style={{ overflowX:"auto" }}>
                  <table style={{ width:"100%", borderCollapse:"collapse", minWidth:1080 }}>
                    <thead><tr>{["材料名稱","批號","數量","規格","檢驗數量","PH","比重","RI","旋光值","結果","備註",""].map(head => <th key={head} style={tableHeadCellStyle}>{head}</th>)}</tr></thead>
                    <tbody>
                      {group.items.map(({ row, index }) => {
                        const issues = getQualityRowIssues(row);
                        const issueSet = new Set(issues);
                        const flaggedStyle = (label) => issueSet.has(label)
                          ? { ...inputStyle, borderColor:"rgba(245,158,11,0.55)", background:"rgba(245,158,11,0.08)" }
                          : inputStyle;
                        return (
                          <tr key={(row.batchNo || row.materialName || "QUALITY") + "-" + index}>
                            <td style={tableRowCellStyle}><input value={row.materialName} onChange={e => updateQualityRecord(index, "materialName", e.target.value)} style={flaggedStyle("材料名稱")} /></td>
                            <td style={tableRowCellStyle}><input value={row.batchNo} onChange={e => updateQualityRecord(index, "batchNo", e.target.value)} style={flaggedStyle("批號")} /></td>
                            <td style={tableRowCellStyle}><input value={row.quantity} onChange={e => updateQualityRecord(index, "quantity", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.spec} onChange={e => updateQualityRecord(index, "spec", e.target.value)} style={flaggedStyle("規格")} /></td>
                            <td style={tableRowCellStyle}><input value={row.inspQty} onChange={e => updateQualityRecord(index, "inspQty", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.ph} onChange={e => updateQualityRecord(index, "ph", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.density} onChange={e => updateQualityRecord(index, "density", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.ri} onChange={e => updateQualityRecord(index, "ri", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.rotation} onChange={e => updateQualityRecord(index, "rotation", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}><input value={row.result} onChange={e => updateQualityRecord(index, "result", e.target.value)} style={flaggedStyle("結果")} /></td>
                            <td style={tableRowCellStyle}><input value={row.note} onChange={e => updateQualityRecord(index, "note", e.target.value)} style={inputStyle} /></td>
                            <td style={tableRowCellStyle}>
                              <div style={{ display:"flex", flexDirection:"column", gap:6, alignItems:"flex-start" }}>
                                <button onClick={() => setQualityRecords(prev => prev.filter((_, i) => i !== index))} style={buttonStyle("danger")}>刪除</button>
                                {issues.length > 0 && <span style={{ fontSize:11, color:"#fcd34d" }}>待補：{issues.join(" / ")}</span>}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>
      </div>

      <div ref={shipmentSectionRef}>
      <Panel
        title="出貨單草稿產生"
        description="依現有訂單與 LOT 資料產出 14.3 出貨單草稿。這一區適合先整理資料，再送出正式紀錄。"
        accent="#a78bfa"
        actions={<Badge color="#a78bfa">{shipmentLoading ? "載入中" : shipmentOrders.length + " 筆訂單"}</Badge>}
      >

        <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:14 }}>
          <Badge color="#a78bfa">{shipmentOrderNo ? "已選訂單" : "尚未選訂單"}</Badge>
          <Badge color="#38bdf8">{shipmentLots.length} 個可選 LOT</Badge>
          <Badge color="#14b8a6">{selectedLotCount} 個已勾選 LOT</Badge>
          <Badge color={shipmentIssues.length ? "#f97316" : "#22c55e"}>{shipmentIssues.length ? shipmentIssues.length + " 項必填待補" : "必填欄位完整"}</Badge>
        </div>

        {selectedOrder && (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(180px, 1fr))", gap:12, marginBottom:14 }}>
            <div style={shipmentSummaryCardStyle}>
              <div style={{ fontSize:11, letterSpacing:1.1, color:"#c4b5fd", marginBottom:6 }}>目前訂單</div>
              <div style={{ fontSize:16, fontWeight:700, color:"#f5f3ff" }}>{selectedOrder.order_no}</div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginTop:4 }}>{selectedOrder.product_name_suggested || selectedOrder.source_product || "未命名產品"}</div>
            </div>
            <div style={shipmentSummaryCardStyle}>
              <div style={{ fontSize:11, letterSpacing:1.1, color:"#c4b5fd", marginBottom:6 }}>建議出貨</div>
              <div style={{ fontSize:16, fontWeight:700, color:"#f5f3ff" }}>{selectedOrder.ship_date_suggested || "未提供"}</div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginTop:4 }}>數量 {selectedOrder.quantity_suggested || "未提供"} {selectedOrder.unit_suggested || ""}</div>
            </div>
            <div style={shipmentSummaryCardStyle}>
              <div style={{ fontSize:11, letterSpacing:1.1, color:"#c4b5fd", marginBottom:6 }}>欄位提醒</div>
              <div style={{ fontSize:13, color:shipmentIssues.length ? "#fdba74" : "#86efac", fontWeight:600 }}>
                {shipmentIssues.length ? "待補：" + shipmentIssues.join(" / ") : "必填欄位已完成"}
              </div>
              {shipmentSuggestions.length > 0 && (
                <div style={{ fontSize:12, color:"#cbd5e1", marginTop:6 }}>建議補上：{shipmentSuggestions.join(" / ")}</div>
              )}
            </div>
          </div>
        )}

        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(220px, 1fr))", gap:12 }}>
          <div>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>訂單</div>
            <select value={shipmentOrderNo} onChange={e => setShipmentOrderNo(e.target.value)} style={inputStyle}>
              <option value="">請選擇訂單</option>
              {shipmentOrders.map(item => <option key={item.order_no} value={item.order_no}>{item.order_no} - {item.product_name_suggested || item.source_product || "未命名"}</option>)}
            </select>
          </div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>日期</div><input ref={shipmentFieldRefs.date} type="date" value={shipmentForm.date} onChange={e => setShipmentForm(prev => ({ ...prev, date:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentIssues.includes("日期") ? "rgba(249,115,22,0.8)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>部門</div><input ref={shipmentFieldRefs.department} value={shipmentForm.department} onChange={e => setShipmentForm(prev => ({ ...prev, department:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentIssues.includes("部門") ? "rgba(249,115,22,0.8)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>申請人</div><input ref={shipmentFieldRefs.requester} value={shipmentForm.requester} onChange={e => setShipmentForm(prev => ({ ...prev, requester:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentIssues.includes("申請人") ? "rgba(249,115,22,0.8)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>產品</div><input ref={shipmentFieldRefs.product_name} value={shipmentForm.product_name} onChange={e => setShipmentForm(prev => ({ ...prev, product_name:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentIssues.includes("產品") ? "rgba(249,115,22,0.8)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>規格</div><input ref={shipmentFieldRefs.spec} value={shipmentForm.spec} onChange={e => setShipmentForm(prev => ({ ...prev, spec:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentSuggestions.includes("規格") ? "rgba(56,189,248,0.45)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>數量</div><input ref={shipmentFieldRefs.quantity} value={shipmentForm.quantity} onChange={e => setShipmentForm(prev => ({ ...prev, quantity:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentIssues.includes("數量") ? "rgba(249,115,22,0.8)" : inputStyle.borderColor }} /></div>
          <div><div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>單位</div><input ref={shipmentFieldRefs.unit} value={shipmentForm.unit} onChange={e => setShipmentForm(prev => ({ ...prev, unit:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentSuggestions.includes("單位") ? "rgba(56,189,248,0.45)" : inputStyle.borderColor }} /></div>
        </div>

        <div style={{ marginTop:12 }}>
          <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>訂單編號 / 批號顯示</div>
          <input ref={shipmentFieldRefs.batch_display} value={shipmentForm.batch_display} onChange={e => setShipmentForm(prev => ({ ...prev, batch_display:e.target.value }))} style={{ ...inputStyle, borderColor: shipmentSuggestions.includes("訂單編號 / 批號顯示") ? "rgba(56,189,248,0.45)" : inputStyle.borderColor }} />
        </div>

        {selectedOrder && selectedOrder.lots && selectedOrder.lots.length > 0 && (
          <div style={{ marginTop:14 }}>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:8 }}>批號清單</div>
            <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
              {selectedOrder.lots.map(item => {
                const checked = selectedLots.includes(item.lot);
                return (
                  <label key={item.lot} style={{ display:"flex", alignItems:"center", gap:6, background:checked?"rgba(167,139,250,0.18)":"rgba(255,255,255,0.05)", border:"1px solid " + (checked ? "rgba(167,139,250,0.45)" : "rgba(255,255,255,0.12)"), borderRadius:999, padding:"6px 12px", cursor:"pointer", fontSize:12, color:"#e9d5ff" }}>
                    <input type="checkbox" checked={checked} onChange={e => setSelectedLots(prev => e.target.checked ? [...prev, item.lot] : prev.filter(lot => lot !== item.lot))} />
                    <span>{item.lot}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ marginTop:14 }}>
          <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>備註</div>
          <textarea value={shipmentForm.remark} onChange={e => setShipmentForm(prev => ({ ...prev, remark:e.target.value }))} style={{ ...inputStyle, minHeight:84, resize:"vertical" }} />
        </div>

        <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap", marginTop:16 }}>
          <button onClick={generateShipmentDraft} disabled={shipmentBusy || shipmentLoading || !shipmentOrderNo} style={{ background:"linear-gradient(135deg,#7c3aed,#8b5cf6)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(shipmentBusy || shipmentLoading || !shipmentOrderNo) ? 0.6 : 1 }}>{shipmentBusy ? "產生中..." : "產生出貨單草稿"}</button>
          {shipmentMessage && <div style={{ fontSize:12, color:"#ddd6fe" }}>{shipmentMessage}</div>}
        </div>
      </Panel>

      <Panel
        title="紀錄生成引擎"
        description="先選模板，再用目前已有的生產、品質、環境、出貨或不符合資料產出草稿。這一版仍以規則帶值為主，不讓 AI 亂猜正式欄位。"
        accent="#fb923c"
        actions={<Badge color="#fb923c">{engineCatalog.length} 個模板</Badge>}
        style={{ marginTop: 20 }}
      >

        <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:14 }}>
          <Badge color="#f97316">1. 輸入需求</Badge>
          <Badge color="#fb923c">2. 選模板</Badge>
          <Badge color="#38bdf8">3. 先檢查缺欄</Badge>
          <Badge color="#22c55e">4. 產生草稿</Badge>
        </div>

        <div style={{ display:"grid", gridTemplateColumns:"1.3fr 1fr", gap:12, alignItems:"end" }}>
          <div>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>需求提示</div>
            <textarea value={enginePrompt} onChange={e => setEnginePrompt(e.target.value)} placeholder="例如：請用目前出貨資料產生出貨流程紀錄，或把不符合資料整理成 CIP 紀錄。" style={{ ...inputStyle, minHeight:80, resize:"vertical" }} />
          </div>
          <div>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>模板</div>
            <select value={engineTemplateCode} onChange={e => setEngineTemplateCode(e.target.value)} style={inputStyle}>
              {engineCatalog.map(item => <option key={item.code} value={item.code}>{item.title}</option>)}
            </select>
          </div>
        </div>

        {selectedEngineTemplate && (
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(180px, 1fr))", gap:12, marginTop:14 }}>
            <div style={{ ...shipmentSummaryCardStyle, borderColor:"rgba(249,115,22,0.18)" }}>
              <div style={{ fontSize:11, letterSpacing:1.1, color:"#fdba74", marginBottom:6 }}>目前模板</div>
              <div style={{ fontSize:16, fontWeight:700, color:"#fff7ed" }}>{selectedEngineTemplate.title}</div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginTop:4 }}>{selectedEngineTemplate.description}</div>
            </div>
            <div style={{ ...shipmentSummaryCardStyle, borderColor:"rgba(56,189,248,0.18)" }}>
              <div style={{ fontSize:11, letterSpacing:1.1, color:"#7dd3fc", marginBottom:6 }}>輸出型態</div>
              <div style={{ fontSize:16, fontWeight:700, color:"#e0f2fe" }}>{selectedEngineTemplate.bundle ? "流程包 / ZIP" : "單一表單 / XLSX"}</div>
              <div style={{ fontSize:12, color:"#cbd5e1", marginTop:4 }}>{selectedEngineTemplate.bundle ? "會一次產出多份下游紀錄" : "只產生目前選擇的模板"}</div>
            </div>
          </div>
        )}

        {engineSuggestions.length > 0 && (
          <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginTop:12 }}>
            {engineSuggestions.map(item => (
              <button key={item.code} onClick={() => setEngineTemplateCode(item.code)} style={{ background:item.code === engineTemplateCode ? "rgba(249,115,22,0.22)" : "rgba(255,255,255,0.06)", border:"1px solid rgba(249,115,22,0.24)", borderRadius:999, color:"#ffedd5", cursor:"pointer", padding:"6px 12px", fontSize:12 }}>
                {item.title}
              </button>
            ))}
          </div>
        )}

        {engineTemplateCode === "cip_152" && (
          <div style={{ marginTop:12 }}>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>不符合來源</div>
            <select value={selectedNcId} onChange={e => setSelectedNcId(e.target.value)} style={inputStyle}>
              {safeNonConformances.map(item => <option key={item.id} value={item.id}>{item.id} - {item.description}</option>)}
            </select>
          </div>
        )}

        {(engineTemplateCode === "audit_notice" || engineTemplateCode === "audit_pack") && (
          <div style={{ marginTop:12 }}>
            <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>選擇稽核計畫</div>
            {safeAuditPlans.length === 0
              ? <div style={{ fontSize:12, color:"#ef4444" }}>⚠ 尚無稽核計畫資料，請先至「稽核計畫」頁新增。</div>
              : <select value={selectedAuditId} onChange={e => setSelectedAuditId(e.target.value)} style={inputStyle}>
                  {safeAuditPlans.map(item => (
                    <option key={item.id} value={item.id}>
                      {item.id}｜{item.year} {item.period}｜{item.dept}｜{item.auditor} → {item.auditee}
                    </option>
                  ))}
                </select>
            }
          </div>
        )}

        <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap", marginTop:16 }}>
          <button onClick={suggestRecordTemplates} disabled={engineBusy} style={{ background:"linear-gradient(135deg,#b45309,#f97316)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:engineBusy ? 0.6 : 1 }}>{engineBusy ? "分析中..." : "分析建議模板"}</button>
          <button onClick={precheckRecordTemplate} disabled={engineBusy || enginePrecheckBusy || !engineTemplateCode} style={{ background:"linear-gradient(135deg,#0369a1,#0ea5e9)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(engineBusy || enginePrecheckBusy || !engineTemplateCode) ? 0.6 : 1 }}>{enginePrecheckBusy ? "檢查中..." : "先檢查缺欄"}</button>
          <button onClick={generateEngineRecord} disabled={engineBusy || !engineTemplateCode} style={{ background:"linear-gradient(135deg,#c2410c,#ea580c)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"10px 16px", fontSize:13, fontWeight:700, opacity:(engineBusy || !engineTemplateCode) ? 0.6 : 1 }}>{engineBusy ? "產生中..." : "產生紀錄草稿"}</button>
          {engineMessage && <div style={{ fontSize:12, color:"#ffedd5" }}>{engineMessage}</div>}
        </div>

        {enginePrecheck && (
          <div style={{ marginTop:16, padding:16, borderRadius:14, background:"rgba(15,23,42,0.72)", border:"1px solid rgba(249,115,22,0.16)" }}>
            <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center", marginBottom:12 }}>
              <Badge color={enginePrecheck.ready ? "#22c55e" : "#f97316"}>{enginePrecheck.ready ? "可直接產生" : "需先補欄"}</Badge>
              <Badge color="#38bdf8">{(enginePrecheck.missing_items || []).length} 項必填缺口</Badge>
              <Badge color="#f59e0b">{(enginePrecheck.warnings || []).length} 項提醒</Badge>
            </div>

            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(180px, 1fr))", gap:12 }}>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>來源資料</div>
                <div style={{ fontSize:13, color:"#e2e8f0", lineHeight:1.8 }}>
                  環境：{enginePrecheck.source_counts?.env_records || 0} 筆<br />
                  生產：{enginePrecheck.source_counts?.prod_records || 0} 筆<br />
                  品質：{enginePrecheck.source_counts?.quality_records || 0} 筆<br />
                  出貨：{enginePrecheck.source_counts?.shipment || 0} 組<br />
                  不符合：{enginePrecheck.source_counts?.nonconformance || 0} 筆
                </div>
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>缺少欄位</div>
                {(enginePrecheck.missing_details || []).length ? (
                  <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                    {enginePrecheck.missing_details.map((detail, index) => (
                      <button
                        key={(detail.scope || "scope") + "-" + (detail.field_key || "field") + "-" + index}
                        onClick={() => jumpToMissingDetail(detail)}
                        style={{ background:"rgba(249,115,22,0.12)", border:"1px solid rgba(249,115,22,0.24)", borderRadius:999, color:"#ffedd5", cursor:"pointer", padding:"6px 10px", fontSize:12 }}
                      >
                        {detail.scope_label ? detail.scope_label + "：" : ""}{detail.label || detail.field_key}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize:13, color:"#86efac", lineHeight:1.8 }}>目前沒有必填缺口</div>
                )}
              </div>
              <div>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>下游模板</div>
                <div style={{ fontSize:13, color:"#e2e8f0", lineHeight:1.8 }}>
                  {enginePrecheck.bundle && (enginePrecheck.included_templates || []).length
                    ? enginePrecheck.included_templates.map(item => item.title).join(" / ")
                    : (enginePrecheck.downstream_templates || []).length
                      ? enginePrecheck.downstream_templates.map(item => item.title).join(" / ")
                      : "無額外下游模板"}
                </div>
              </div>
            </div>

            {(enginePrecheck.warnings || []).length > 0 && (
              <div style={{ marginTop:12 }}>
                <div style={{ fontSize:12, color:"#cbd5e1", marginBottom:6 }}>提醒</div>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                  {enginePrecheck.warnings.map((item, index) => (
                    <span key={index} style={{ fontSize:12, color:"#ffedd5", background:"rgba(249,115,22,0.12)", border:"1px solid rgba(249,115,22,0.18)", borderRadius:999, padding:"6px 10px" }}>
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Panel>
      </div>
    </div>
  );
}
