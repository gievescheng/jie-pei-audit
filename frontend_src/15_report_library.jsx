// ─── REPORT TAB ───────────────────────────────────────────────────────────────
function ReportTab({ instruments, documents, training, equipment, suppliers, nonConformances: ncs, auditPlans, envRecords }) {
  const [generated, setGenerated] = useState(false);
  const calibEnriched = instruments.filter(i=>i.status!=="免校正").map(i => ({ ...i, nextDate:addDays(i.calibratedDate,i.intervalDays), days:daysUntil(addDays(i.calibratedDate,i.intervalDays)) }));
  const eqEnriched = equipment.map(eq => ({ ...eq, nextDate:addDays(eq.lastMaintenance,eq.intervalDays), days:daysUntil(addDays(eq.lastMaintenance,eq.intervalDays)) }));
  const supEnriched = suppliers.map(s => ({ ...s, nextEvalDate:addDays(s.lastEvalDate,s.evalIntervalDays), days:daysUntil(addDays(s.lastEvalDate,s.evalIntervalDays)) }));
  const overdue = calibEnriched.filter(i=>i.days<0).length;
  const soonCalib = calibEnriched.filter(i=>i.days>=0&&i.days<=14).length;
  const overdueEq = eqEnriched.filter(e=>e.days<0).length;
  const openNcs = ncs.filter(n=>n.status!=="已關閉").length;
  const totalTraining = training.reduce((s,e)=>s+e.trainings.length,0);
  const auditCompleted = auditPlans.filter(a=>a.status==="已完成").length;
  const auditTotal = auditPlans.length;
  const envPassRate = envRecords.length>0?Math.round(envRecords.filter(r=>r.result==="合格").length/envRecords.length*100):0;
  const tdStyle = { padding:"7px 12px", border:"1px solid #e2e8f0" };
  const thStyle = { padding:"8px 12px", textAlign:"left", border:"1px solid #e2e8f0", background:"#f1f5f9" };
  const secStyle = { fontSize:15, fontWeight:800, color:"#0f172a", paddingLeft:12, marginBottom:14 };
  const conStyle = { marginTop:10, padding:12, background:"#f8fafc", borderRadius:8, fontSize:13, color:"#374151" };
  return (
    <div>
      <SectionHeader title="稽核報告產生器" color="#f472b6" />
      <div style={{ background:"rgba(244,114,182,0.06)", border:"1px solid rgba(244,114,182,0.2)", borderRadius:14, padding:24, marginBottom:20 }}>
        <div style={{ fontSize:15, color:"#f9a8d4", fontWeight:600, marginBottom:8 }}>[ISO 9001] 自動產生 ISO 9001:2015 稽核摘要報告</div>
        <div style={{ fontSize:13, color:"#64748b", lineHeight:1.7 }}>系統將根據目前資料庫中的記錄，自動彙整校正狀態、設備保養、訓練記錄、文件版本、供應商評鑑、不符合記錄、內部稽核完成狀態及工作環境監測。</div>
        <div style={{ display:"flex", gap:12, marginTop:16 }}>
          <button onClick={() => setGenerated(true)} style={{ background:"linear-gradient(135deg, #be185d, #ec4899)", border:"none", borderRadius:10, color:"#fff", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>[+] 產生稽核報告</button>
          {generated && (<button onClick={() => window.print()} style={{ background:"rgba(244,114,182,0.15)", border:"1px solid rgba(244,114,182,0.3)", borderRadius:10, color:"#f9a8d4", cursor:"pointer", padding:"12px 24px", fontSize:14, fontWeight:700 }}>[P] 列印 / 存為 PDF</button>)}
        </div>
      </div>
      {generated && (
        <div id="report-content" style={{ background:"#fff", color:"#1e293b", borderRadius:14, padding:32, fontFamily:"'Microsoft JhengHei', 'PingFang TC', 'Noto Sans TC', sans-serif" }}>
          <div style={{ textAlign:"center", borderBottom:"2px solid #e2e8f0", paddingBottom:20, marginBottom:24 }}>
            <div style={{ fontSize:22, fontWeight:800, color:"#0f172a" }}>潔沛企業有限公司</div>
            <div style={{ fontSize:16, fontWeight:600, color:"#374151", marginTop:4 }}>ISO 9001:2015 品質系統稽核摘要報告</div>
            <div style={{ fontSize:13, color:"#6b7280", marginTop:8 }}>報告產生日期：{formatDate(new Date().toISOString().split("T")[0])} / 報告版本：自動產生</div>
          </div>
          {/* 一、量測資源 MP-05 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #3b82f6" }}>一、量測資源管理（MP-05）稽核摘要</div>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}><thead><tr style={{ background:"#f1f5f9" }}>{["儀器編號","名稱","類型","最後校正","下次校正","狀態"].map(h=>(<th key={h} style={thStyle}>{h}</th>))}</tr></thead><tbody>{calibEnriched.map(i=>(<tr key={i.id}><td style={tdStyle}>{i.id}</td><td style={tdStyle}>{i.name}</td><td style={tdStyle}>{i.type}</td><td style={tdStyle}>{formatDate(i.calibratedDate)}</td><td style={tdStyle}>{formatDate(i.nextDate)}</td><td style={{...tdStyle,color:i.days<0?"#ef4444":i.days<=14?"#f97316":"#16a34a",fontWeight:700}}>{urgencyLabel(i.days)}</td></tr>))}</tbody></table>
            <div style={conStyle}>稽核結論：共 {instruments.length} 台量規儀器，逾期 <b style={{color:"#ef4444"}}>{overdue}</b> 台，14天內到期 <b style={{color:"#f97316"}}>{soonCalib}</b> 台。{overdue>0&&" [警告] 請立即安排逾期儀器校正。"}</div>
          </div>
          {/* 二、設施設備 MP-04 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #f97316" }}>二、設施設備管理（MP-04）稽核摘要</div>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}><thead><tr style={{ background:"#f1f5f9" }}>{["設備編號","名稱","位置","最後保養","下次保養","狀態"].map(h=>(<th key={h} style={thStyle}>{h}</th>))}</tr></thead><tbody>{eqEnriched.map(eq=>(<tr key={eq.id}><td style={tdStyle}>{eq.id}</td><td style={tdStyle}>{eq.name}</td><td style={tdStyle}>{eq.location}</td><td style={tdStyle}>{formatDate(eq.lastMaintenance)}</td><td style={tdStyle}>{formatDate(eq.nextDate)}</td><td style={{...tdStyle,color:eq.days<0?"#ef4444":eq.days<=30?"#f97316":"#16a34a",fontWeight:700}}>{urgencyLabel(eq.days)}</td></tr>))}</tbody></table>
            <div style={conStyle}>稽核結論：共 {equipment.length} 台設備，逾期保養 <b style={{color:"#ef4444"}}>{overdueEq}</b> 台。</div>
          </div>
          {/* 三、人力資源 MP-03 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #8b5cf6" }}>三、人力資源及訓練（MP-03）稽核摘要</div>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}><thead><tr style={{ background:"#f1f5f9" }}>{["員工編號","姓名","部門","職稱","到職日","訓練筆數","外訓筆數","有證書"].map(h=>(<th key={h} style={thStyle}>{h}</th>))}</tr></thead><tbody>{training.map(emp=>(<tr key={emp.id}><td style={tdStyle}>{emp.id}</td><td style={{...tdStyle,fontWeight:600}}>{emp.name}</td><td style={tdStyle}>{emp.dept}</td><td style={tdStyle}>{emp.role}</td><td style={tdStyle}>{formatDate(emp.hireDate)}</td><td style={{...tdStyle,fontWeight:700}}>{emp.trainings.length}</td><td style={tdStyle}>{emp.trainings.filter(t=>t.type==="外訓").length}</td><td style={tdStyle}>{emp.trainings.filter(t=>t.cert==="有").length}</td></tr>))}</tbody></table>
            <div style={conStyle}>稽核結論：共 {training.length} 名員工，訓練記錄合計 <b>{totalTraining}</b> 筆。</div>
          </div>
          {/* 四、供應商 MP-10 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #06b6d4" }}>四、採購及供應商管理（MP-10）稽核摘要</div>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}><thead><tr style={{ background:"#f1f5f9" }}>{["供應商編號","名稱","類別","評鑑分數","評定結果","最後評鑑","下次評鑑"].map(h=>(<th key={h} style={thStyle}>{h}</th>))}</tr></thead><tbody>{supEnriched.map(s=>(<tr key={s.id}><td style={tdStyle}>{s.id}</td><td style={{...tdStyle,fontWeight:600}}>{s.name}</td><td style={tdStyle}>{s.category}</td><td style={{...tdStyle,fontWeight:700,color:s.evalScore>=90?"#16a34a":s.evalScore>=70?"#d97706":"#ef4444"}}>{s.evalScore}</td><td style={tdStyle}>{s.evalResult}</td><td style={tdStyle}>{formatDate(s.lastEvalDate)}</td><td style={{...tdStyle,color:s.days<0?"#ef4444":"#374151"}}>{formatDate(s.nextEvalDate)}</td></tr>))}</tbody></table>
            <div style={conStyle}>稽核結論：共 {suppliers.length} 家供應商，評鑑逾期 <b style={{color:"#ef4444"}}>{supEnriched.filter(s=>s.days<0).length}</b> 家，條件合格 <b style={{color:"#eab308"}}>{suppliers.filter(s=>s.evalResult==="條件合格").length}</b> 家。</div>
          </div>
          {/* 五、不符合 MP-15 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #ef4444" }}>五、不符合及矯正措施（MP-15）稽核摘要</div>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}><thead><tr style={{ background:"#f1f5f9" }}>{["編號","日期","部門","類型","嚴重度","簡述","資任人","到期日","狀態"].map(h=>(<th key={h} style={thStyle}>{h}</th>))}</tr></thead><tbody>{ncs.map(nc=>(<tr key={nc.id}><td style={{...tdStyle,fontFamily:"monospace",fontSize:11}}>{nc.id}</td><td style={tdStyle}>{formatDate(nc.date)}</td><td style={tdStyle}>{nc.dept}</td><td style={tdStyle}>{nc.type}</td><td style={{...tdStyle,color:nc.severity==="重大"?"#ef4444":"#d97706",fontWeight:700}}>{nc.severity}</td><td style={tdStyle}>{nc.description.substring(0,20)}{nc.description.length>20?"...":""}</td><td style={tdStyle}>{nc.responsible}</td><td style={tdStyle}>{formatDate(nc.dueDate)}</td><td style={{...tdStyle,color:nc.status==="已關閉"?"#16a34a":nc.status==="處理中"?"#d97706":"#ef4444",fontWeight:700}}>{nc.status}</td></tr>))}</tbody></table>
            <div style={conStyle}>稽核結論：共 {ncs.length} 筆不符合報告，尚未關閉 <b style={{color:"#ef4444"}}>{openNcs}</b> 筆。{openNcs>0&&" [警告] 請監控未關閉項目之矯正措施執行進度。"}</div>
          </div>
          {/* 六、內部稽核 MP-09 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #8b5cf6" }}>六、內部稽核管理（MP-09）執行摘要</div>
            <div style={conStyle}>內部稽核已完成 <b>{auditCompleted}</b> 次 / 計畫 <b>{auditTotal}</b> 次，完成率 <b>{auditTotal>0?Math.round(auditCompleted/auditTotal*100):0}%</b>。累計發現 {auditPlans.reduce((s,a)=>s+a.findings,0)} 項，不符合 {auditPlans.reduce((s,a)=>s+a.ncCount,0)} 項。</div>
          </div>
          {/* 七、環境監控 MP-06 */}
          <div style={{ marginBottom:24 }}>
            <div style={{ ...secStyle, borderLeft:"4px solid #14b8a6" }}>七、工作環境監控（MP-06）稽核摘要</div>
            <div style={conStyle}>潔淨室環境監測共 {envRecords.length} 筆，整體合格率 <b style={{color:envPassRate>=90?"#16a34a":envPassRate>=80?"#d97706":"#ef4444"}}>{envPassRate}%</b>，不合格 <b style={{color:"#ef4444"}}>{envRecords.filter(r=>r.result==="不合格").length}</b> 筆，警告 <b style={{color:"#d97706"}}>{envRecords.filter(r=>r.result==="警告").length}</b> 筆。</div>
          </div>
          <div style={{ borderTop:"1px solid #e2e8f0", paddingTop:16, marginTop:24, display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:16 }}>
            {["稽核員","審核者","核准者"].map(role => (<div key={role} style={{ textAlign:"center" }}><div style={{ height:40, borderBottom:"1px solid #374151" }} /><div style={{ fontSize:12, color:"#6b7280", marginTop:6 }}>{role}（簽名）</div></div>))}
          </div>
        </div>
      )}
    </div>
  );
}


function sortByDocumentId(items) {
  return [...items].sort((a, b) => String(a.id || "").localeCompare(String(b.id || ""), "zh-Hant", { numeric: true, sensitivity: "base" }));
}

function buildIsoDocumentMap(documents, manuals) {
  const firstLevel = [];
  const procedures = [];
  const thirdLevelMap = new Map();
  const procedureMap = new Map();
  const orphanForms = [];
  const orphanRecords = [];

  const getProcedureKey = id => {
    const match = String(id || "").match(/^MP-(\d+)/i);
    return match ? String(parseInt(match[1], 10)).padStart(2, "0") : "";
  };

  const addThirdLevel = doc => {
    if (!doc || !doc.id) return;
    if (!thirdLevelMap.has(doc.id)) thirdLevelMap.set(doc.id, doc);
  };

  documents.forEach(doc => {
    if (/^MM-/i.test(doc.id) || doc.type === "管理手冊") {
      firstLevel.push(doc);
      return;
    }
    if (/^MP-/i.test(doc.id)) {
      procedures.push(doc);
      procedureMap.set(getProcedureKey(doc.id), { procedure: doc, forms: [], records: [] });
      return;
    }
    if (/^RW-/i.test(doc.id) || doc.type === "作業指導書") {
      addThirdLevel(doc);
    }
  });

  manuals.forEach(addThirdLevel);

  documents.forEach(doc => {
    const match = String(doc.id || "").match(/^(FR|RC)-(\d+)/i);
    if (!match) return;
    const bucket = procedureMap.get(String(parseInt(match[2], 10)).padStart(2, "0"));
    if (!bucket) {
      if (match[1].toUpperCase() === "FR") orphanForms.push(doc);
      else orphanRecords.push(doc);
      return;
    }
    if (match[1].toUpperCase() === "FR") bucket.forms.push(doc);
    else bucket.records.push(doc);
  });

  const bundles = procedures
    .map(proc => {
      const key = getProcedureKey(proc.id);
      const bucket = procedureMap.get(key) || { procedure: proc, forms: [], records: [] };
      return {
        procedure: proc,
        forms: sortByDocumentId(bucket.forms),
        records: sortByDocumentId(bucket.records),
      };
    })
    .sort((a, b) => String(a.procedure.id).localeCompare(String(b.procedure.id), "zh-Hant", { numeric: true, sensitivity: "base" }));

  return {
    firstLevel: sortByDocumentId(firstLevel),
    secondLevel: sortByDocumentId(procedures),
    thirdLevel: sortByDocumentId(Array.from(thirdLevelMap.values())),
    bundles,
    orphanForms: sortByDocumentId(orphanForms),
    orphanRecords: sortByDocumentId(orphanRecords),
  };
}

function IsoDocumentCard({ doc, accent = "#60a5fa", showPaths = false }) {
  const path = doc.pdfPath || doc.docxPath || doc.fileName || "";
  return (
    <div style={{ background:"rgba(255,255,255,0.03)", border:`1px solid ${accent}33`, borderRadius:14, padding:16 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
        <div>
          <div style={{ fontSize:11, fontFamily:"monospace", color:accent, fontWeight:700 }}>{doc.id}</div>
          <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0", marginTop:6 }}>{doc.name}</div>
        </div>
        <Badge color={accent}>{doc.type}</Badge>
      </div>
      <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginTop:10, fontSize:12, color:"#94a3b8" }}>
        <span>部門: {doc.department || "未填寫"}</span>
        <span>版本: v{doc.version || "?"}</span>
        {doc.author && <span>作者: {doc.author}</span>}
      </div>
      {showPaths && path && <div style={{ marginTop:10, fontSize:11, color:"#64748b", wordBreak:"break-all" }}>{path}</div>}
    </div>
  );
}

function IsoProcedureBundle({ bundle, showPaths = false }) {
  const sections = [
    { title: "表單", items: bundle.forms, color: "#22c55e" },
    { title: "記錄", items: bundle.records, color: "#f59e0b" },
  ];

  return (
    <div style={{ background:"rgba(255,255,255,0.025)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:16, padding:18 }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12, flexWrap:"wrap" }}>
        <div>
          <div style={{ fontSize:11, fontFamily:"monospace", color:"#60a5fa", fontWeight:700 }}>{bundle.procedure.id}</div>
          <div style={{ fontSize:16, fontWeight:800, color:"#e2e8f0", marginTop:6 }}>{bundle.procedure.name}</div>
          <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginTop:8, fontSize:12, color:"#94a3b8" }}>
            <span>部門: {bundle.procedure.department || "未填寫"}</span>
            <span>版本: v{bundle.procedure.version || "?"}</span>
            <span>表單: {bundle.forms.length}</span>
            <span>記錄: {bundle.records.length}</span>
          </div>
        </div>
        <Badge color="#60a5fa">二階文件</Badge>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:14, marginTop:18 }}>
        {sections.map(section => (
          <div key={section.title} style={{ background:"rgba(15,23,42,0.35)", border:`1px solid ${section.color}22`, borderRadius:12, padding:14 }}>
            <div style={{ fontSize:13, fontWeight:700, color:section.color, marginBottom:10 }}>{section.title} ({section.items.length})</div>
            {section.items.length === 0 ? (
              <div style={{ fontSize:12, color:"#64748b" }}>目前沒有歸屬到此程序的{section.title}</div>
            ) : (
              <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                {section.items.map(item => <IsoDocumentCard key={item.id} doc={item} accent={section.color} showPaths={showPaths} />)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DocumentsManagerDetails({ documents, setDocuments }) {
  const th = useTheme();
  return (
    <details style={{ background: th.panel, border:"1px solid " + th.panelBorder, borderRadius:18, padding:18, boxShadow: th.shadow }}>
      <summary style={{ cursor:"pointer", fontSize:14, fontWeight:700, color: th.text }}>進階管理：原始文件清單、上傳與編修</summary>
      <div style={{ marginTop:18 }}>
        <DocumentsTab documents={documents} setDocuments={setDocuments} />
      </div>
    </details>
  );
}

function LibraryDetailsPanel({ documents, manuals }) {
  const th = useTheme();
  return (
    <details style={{ background: th.panel, border:"1px solid " + th.panelBorder, borderRadius:18, padding:18, boxShadow: th.shadow }}>
      <summary style={{ cursor:"pointer", fontSize:14, fontWeight:700, color: th.text }}>原始文件庫視圖</summary>
      <div style={{ marginTop:18 }}>
        <LibraryTab documents={documents} manuals={manuals} />
      </div>
    </details>
  );
}

function DocumentsManagerTab({ documents, setDocuments, manuals }) {
  const iso = buildIsoDocumentMap(documents, manuals);

  return (
    <div>
      <PageIntro
        eyebrow="ISO Document Center"
        title="文件管理（ISO 架構）"
        description="這裡是 QMS 文件中心。系統會依 ISO 邏輯把一階、二階、三階文件，以及表單與記錄對應到正確程序底下，方便管理與查核。"
      >
        <div style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
          <StatCard label="一階文件" value={iso.firstLevel.length} color="#a78bfa" sub="品質手冊 / 管理手冊" />
          <StatCard label="二階文件" value={iso.secondLevel.length} color="#60a5fa" sub="管理程序" />
          <StatCard label="三階文件" value={iso.thirdLevel.length} color="#14b8a6" sub="作業指導書" />
          <StatCard label="表單" value={documents.filter(doc => /^FR-/i.test(doc.id)).length} color="#22c55e" />
          <StatCard label="記錄" value={documents.filter(doc => /^RC-/i.test(doc.id)).length} color="#f59e0b" />
        </div>
      </PageIntro>

      <div style={{ display:"flex", flexDirection:"column", gap:18 }}>
        <Panel title="第一層：品質手冊與管理手冊" description="這一層放制度總綱與管理原則，是整套 QMS 的最高層文件。" accent="#a78bfa">
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:12 }}>
            {iso.firstLevel.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#a78bfa" showPaths />)}
          </div>
        </Panel>

        <Panel title="第二層：管理程序與其表單 / 記錄" description="每一份程序文件下面都會帶出對應表單與記錄，方便你從程序一路追到實際執行紀錄。" accent="#60a5fa">
          <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
            {iso.bundles.map(bundle => <IsoProcedureBundle key={bundle.procedure.id} bundle={bundle} showPaths />)}
          </div>
          {(iso.orphanForms.length > 0 || iso.orphanRecords.length > 0) && (
            <div style={{ marginTop:14, background:"rgba(245,158,11,0.08)", border:"1px solid rgba(245,158,11,0.2)", borderRadius:12, padding:14 }}>
              <div style={{ fontSize:13, fontWeight:700, color:"#fcd34d", marginBottom:10 }}>未歸屬程序的文件</div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(260px, 1fr))", gap:10 }}>
                {iso.orphanForms.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#22c55e" showPaths />)}
                {iso.orphanRecords.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#f59e0b" showPaths />)}
              </div>
            </div>
          )}
        </Panel>

        <Panel title="第三層：作業指導書" description="這一層是現場操作、設備使用與細部作業規則，通常最貼近實際執行。" accent="#14b8a6">
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:12 }}>
            {iso.thirdLevel.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#14b8a6" showPaths />)}
          </div>
        </Panel>

        <DocumentsManagerDetails documents={documents} setDocuments={setDocuments} />
      </div>
    </div>
  );
}

function LibraryHierarchyTab({ documents, manuals }) {
  const [search, setSearch] = useState("");
  const [levelFilter, setLevelFilter] = useState("全部");
  const iso = buildIsoDocumentMap(documents, manuals);

  const matchesSearch = doc => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return [doc.id, doc.name, doc.department, doc.docxPath, doc.pdfPath].filter(Boolean).some(value => String(value).toLowerCase().includes(q));
  };

  const filterByLevel = section => levelFilter === "全部" || levelFilter === section;
  const filteredBundles = iso.bundles.map(bundle => ({
    ...bundle,
    forms: bundle.forms.filter(matchesSearch),
    records: bundle.records.filter(matchesSearch),
    visible: matchesSearch(bundle.procedure) || bundle.forms.some(matchesSearch) || bundle.records.some(matchesSearch),
  })).filter(bundle => bundle.visible);
  const filteredFirst = iso.firstLevel.filter(matchesSearch);
  const filteredThird = iso.thirdLevel.filter(matchesSearch);

  return (
    <div>
      <PageIntro
        eyebrow="Document Library"
        title="文件庫（ISO 分層瀏覽）"
        description="文件庫偏向查詢與閱讀。你可以先依 ISO 層級切換，再用搜尋快速縮小範圍，避免清單過長時難以定位。"
      >
        <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="搜尋文件名稱、編號、部門或路徑…" style={{ ...inputStyle, flex:1, minWidth:240 }} />
          {["全部", "一階文件", "二階文件", "三階文件"].map(item => (
            <button key={item} onClick={() => setLevelFilter(item)} style={levelFilter===item ? buttonStyle("warning") : buttonStyle("secondary")}>{item}</button>
          ))}
        </div>
      </PageIntro>

      <div style={{ display:"flex", flexDirection:"column", gap:18 }}>
        {filterByLevel("一階文件") && (
          <Panel title="第一層文件" description="以制度與手冊為主，適合快速看總則與管理原則。" accent="#a78bfa">
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:12 }}>
              {filteredFirst.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#a78bfa" showPaths />)}
            </div>
          </Panel>
        )}

        {filterByLevel("二階文件") && (
          <Panel title="第二層文件與其表單 / 記錄" description="從程序直接展開其表單和記錄，最適合做稽核追查與缺漏檢查。" accent="#60a5fa">
            <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
              {filteredBundles.map(bundle => <IsoProcedureBundle key={bundle.procedure.id} bundle={bundle} showPaths />)}
            </div>
          </Panel>
        )}

        {filterByLevel("三階文件") && (
          <Panel title="第三層文件" description="主要用來查看作業指導書與現場執行依據。" accent="#14b8a6">
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:12 }}>
              {filteredThird.map(doc => <IsoDocumentCard key={doc.id} doc={doc} accent="#14b8a6" showPaths />)}
            </div>
          </Panel>
        )}

        {filteredFirst.length === 0 && filteredBundles.length === 0 && filteredThird.length === 0 && (
          <div style={{ textAlign:"center", padding:"36px 20px", color:"#64748b", fontSize:14 }}>沒有符合篩選條件的文件。</div>
        )}

        <LibraryDetailsPanel documents={documents} manuals={manuals} />
      </div>
    </div>
  );
}

// ─── LIBRARY TAB ──────────────────────────────────────────────────────────────────────────────
function LibraryTab({ documents, manuals }) {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("全部");
  const [preview, setPreview] = useState(null);

  // Merge all docs with pdfs + manuals
  const allItems = [
    ...documents.filter(d => d.pdfPath),
    ...manuals,
  ];
  const types = ["全部", "管理手冊", "管理程序", "作業指導書"];
  const filtered = allItems.filter(d => {
    const matchType = typeFilter === "全部" || d.type === typeFilter;
    const q = search.toLowerCase();
    const matchSearch = !q || d.name.toLowerCase().includes(q) || d.id.toLowerCase().includes(q) || (d.department||"").toLowerCase().includes(q);
    return matchType && matchSearch;
  });

  const typeColor = t => t==="管理手冊"?"#a78bfa":t==="管理程序"?"#60a5fa":"#34d399";

  return (
    <div>
      <SectionHeader title="文件庫（PDF 檔案）" count={allItems.length} color="#f97316" />
      <div style={{ display:"flex", gap:12, marginBottom:20, flexWrap:"wrap" }}>
        <StatCard label="管理手冊" value={allItems.filter(d=>d.type==="管理手冊").length} color="#a78bfa" />
        <StatCard label="管理程序" value={allItems.filter(d=>d.type==="管理程序").length} color="#60a5fa" />
        <StatCard label="作業指導書" value={allItems.filter(d=>d.type==="作業指導書").length} color="#34d399" />
        <StatCard label="總計" value={allItems.length} color="#f97316" />
      </div>

      {/* Search & Filter bar */}
      <div style={{ display:"flex", gap:10, marginBottom:18, flexWrap:"wrap" }}>
        <input
          type="text" value={search} onChange={e=>setSearch(e.target.value)}
          placeholder="搜尋文件名稱、編號、部門…"
          style={{ ...inputStyle, flex:1, minWidth:200, padding:"10px 14px" }}
        />
        <div style={{ display:"flex", gap:6 }}>
          {types.map(t => (
            <button key={t} onClick={()=>setTypeFilter(t)} style={{
              background: typeFilter===t ? "linear-gradient(135deg,#ea580c,#f97316)" : "rgba(255,255,255,0.05)",
              border: "1px solid " + (typeFilter===t ? "#f97316" : "rgba(255,255,255,0.1)"),
              borderRadius:8, color: typeFilter===t?"#fff":"#94a3b8",
              cursor:"pointer", padding:"8px 14px", fontSize:12, fontWeight:600
            }}>{t}</button>
          ))}
        </div>
      </div>

      {/* Document Cards Grid */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(300px, 1fr))", gap:14 }}>
        {filtered.map(doc => (
          <div key={doc.id} style={{ background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:14, padding:18, display:"flex", flexDirection:"column", gap:10 }}>
            {/* Header */}
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
              <div style={{ fontSize:11, fontFamily:"monospace", color:"#60a5fa", fontWeight:700 }}>{doc.id}</div>
              <Badge color={typeColor(doc.type)}>{doc.type}</Badge>
            </div>
            {/* Name */}
            <div style={{ fontSize:14, fontWeight:700, color:"#e2e8f0", lineHeight:1.4 }}>{doc.name}</div>
            {/* Description (for manuals) */}
            {doc.desc && <div style={{ fontSize:12, color:"#64748b", lineHeight:1.5 }}>{doc.desc}</div>}
            {/* Meta */}
            <div style={{ display:"flex", gap:12, fontSize:11, color:"#64748b", flexWrap:"wrap" }}>
              <span>版本: <b style={{color:"#4ade80"}}>v{doc.version}</b></span>
              <span>部門: {doc.department}</span>
              {doc.author && <span>作者: {doc.author}</span>}
            </div>
            {/* PDF button */}
            <div style={{ display:"flex", gap:8, marginTop:4 }}>
              <a
                href={encodeURI(doc.pdfPath)} target="_blank" rel="noopener noreferrer"
                style={{ flex:1, background:"linear-gradient(135deg,#dc2626,#ef4444)", color:"#fff",
                  padding:"10px 0", borderRadius:8, fontSize:13, fontWeight:700,
                  textDecoration:"none", textAlign:"center" }}
              >
                &#128196; 開啟 PDF
              </a>
              <button onClick={()=>setPreview(doc.pdfPath)} style={{
                background:"rgba(255,255,255,0.06)", border:"1px solid rgba(255,255,255,0.15)",
                borderRadius:8, color:"#94a3b8", cursor:"pointer",
                padding:"10px 14px", fontSize:12, fontWeight:600
              }}>預覽</button>
            </div>
          </div>
        ))}
      </div>
      {filtered.length === 0 && (
        <div style={{ textAlign:"center", padding:"40px 0", color:"#475569", fontSize:14 }}>未找到符合條件的文件</div>
      )}

      {/* PDF Preview Modal (iframe) */}
      {preview && (
        <div style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.85)", zIndex:1000, display:"flex", flexDirection:"column" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"12px 20px", background:"rgba(15,23,42,0.95)", borderBottom:"1px solid rgba(255,255,255,0.1)" }}>
            <div style={{ fontSize:13, color:"#94a3b8", fontFamily:"monospace" }}>{preview.split("/").pop()}</div>
            <div style={{ display:"flex", gap:10 }}>
              <a href={encodeURI(preview)} target="_blank" rel="noopener noreferrer" style={{ background:"linear-gradient(135deg,#dc2626,#ef4444)", color:"#fff", padding:"6px 14px", borderRadius:7, fontSize:12, fontWeight:700, textDecoration:"none" }}>在新標籤開啟</a>
              <button onClick={()=>setPreview(null)} style={{ background:"rgba(255,255,255,0.1)", border:"1px solid rgba(255,255,255,0.2)", borderRadius:7, color:"#e2e8f0", cursor:"pointer", padding:"6px 14px", fontSize:13, fontWeight:700 }}>✕ 關閉</button>
            </div>
          </div>
          <iframe
            src={encodeURI(preview)}
            style={{ flex:1, border:"none", background:"#fff" }}
            title="PDF Preview"
          />
        </div>
      )}
    </div>
  );
}
