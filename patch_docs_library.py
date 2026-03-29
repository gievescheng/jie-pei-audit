#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch audit-dashboard.jsx to add edit / delete / batch-select
to DocumentsTab and LibraryTab.
"""

import re, sys

SRC = r"C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx"

with open(SRC, encoding="utf-8") as f:
    code = f.read()

original = code   # keep for rollback / diff

errors = []

# ─────────────────────────────────────────────────────────────────────────────
# helper
# ─────────────────────────────────────────────────────────────────────────────
def patch(old, new, label=""):
    global code
    if old not in code:
        errors.append(f"NOT FOUND: {label!r}")
        print(f"  FAIL: {label}")
        return
    code = code.replace(old, new, 1)
    print(f"  OK: {label}")

# ═════════════════════════════════════════════════════════════════════════════
# PATCH A1 — App(): make manuals stateful + persisted
# ═════════════════════════════════════════════════════════════════════════════
patch(
    "const [manuals] = useState(initialManuals);",
    "const [manuals, setManuals] = useState(() => ls(\"audit_manuals\", initialManuals));",
    "A1: manuals state"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH A2 — App(): localStorage hook for manuals
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "useEffect(() => { try { localStorage.setItem(\"audit_prodRecords\", JSON.stringify(prodRecords)); } catch(e) {} }, [prodRecords]);",
    ("useEffect(() => { try { localStorage.setItem(\"audit_prodRecords\", JSON.stringify(prodRecords)); } catch(e) {} }, [prodRecords]);\n"
     "  useEffect(() => { try { localStorage.setItem(\"audit_manuals\",    JSON.stringify(manuals));    } catch(e) {} }, [manuals]);"),
    "A2: manuals localStorage hook"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH A3 — App(): reset list
# ─────────────────────────────────────────────────────────────────────────────
patch(
    '"audit_instruments","audit_documents","audit_training","audit_equipment","audit_suppliers","audit_ncs","audit_auditPlans","audit_envRecords","audit_prodRecords"',
    '"audit_instruments","audit_documents","audit_training","audit_equipment","audit_suppliers","audit_ncs","audit_auditPlans","audit_envRecords","audit_prodRecords","audit_manuals"',
    "A3: reset list"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH A4 — App(): pass setDocuments + setManuals to LibraryTab
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "case \"library\":        return <LibraryTab documents={documents} manuals={manuals} />;",
    "case \"library\":        return <LibraryTab documents={documents} setDocuments={setDocuments} manuals={manuals} setManuals={setManuals} />;",
    "A4: LibraryTab props"
)

# ═════════════════════════════════════════════════════════════════════════════
# PATCH B1 — DocumentsTab: add selectedIds + editTarget state
# ═════════════════════════════════════════════════════════════════════════════
patch(
    "  const [dragOver, setDragOver] = useState(false);",
    ("  const [dragOver, setDragOver] = useState(false);\n"
     "  const [selectedIds, setSelectedIds] = useState(new Set());\n"
     "  const [editTarget, setEditTarget] = useState(null);"),
    "B1: DocumentsTab state"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH B2 — DocumentsTab: CRUD helper functions (after closeModal)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "  function closeModal() { setMode(null); setNewDoc({ ...emptyDoc }); setBulkItems([]); setErr(\"\"); setBulkDone(false); }",
    (
     "  function closeModal() { setMode(null); setNewDoc({ ...emptyDoc }); setBulkItems([]); setErr(\"\"); setBulkDone(false); }\n"
     "\n"
     "  // ── Selection helpers ─────────────────────────────────────────────────────\n"
     "  function toggleSelect(id) {\n"
     "    setSelectedIds(prev => {\n"
     "      const next = new Set(prev);\n"
     "      next.has(id) ? next.delete(id) : next.add(id);\n"
     "      return next;\n"
     "    });\n"
     "  }\n"
     "  function toggleAll() {\n"
     "    if (selectedIds.size === enriched.length) setSelectedIds(new Set());\n"
     "    else setSelectedIds(new Set(enriched.map(d => d.id)));\n"
     "  }\n"
     "  function deleteSelected() {\n"
     "    if (!selectedIds.size) return;\n"
     "    if (!window.confirm(`確定刪除選取的 ${selectedIds.size} 筆文件？`)) return;\n"
     "    setDocuments(prev => prev.filter(d => !selectedIds.has(d.id)));\n"
     "    setSelectedIds(new Set());\n"
     "  }\n"
     "  function deleteSingle(id) {\n"
     "    const doc = documents.find(d => d.id === id);\n"
     "    if (!window.confirm(`確定刪除「${doc ? doc.name : id}」？`)) return;\n"
     "    setDocuments(prev => prev.filter(d => d.id !== id));\n"
     "  }\n"
     "  function saveEdit() {\n"
     "    if (!editTarget) return;\n"
     "    setDocuments(prev => prev.map(d => d.id === editTarget.id ? { ...editTarget, retentionYears: parseInt(editTarget.retentionYears)||16 } : d));\n"
     "    setEditTarget(null);\n"
     "  }\n"
    ),
    "B2: DocumentsTab CRUD helpers"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH B3 — DocumentsTab: batch action bar before table
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "      {/* Document table */}",
    (
     "      {/* Batch action bar */}\n"
     "      {selectedIds.size > 0 && (\n"
     "        <div style={{ display:\"flex\", alignItems:\"center\", gap:12, background:\"rgba(239,68,68,0.08)\", border:\"1px solid rgba(239,68,68,0.25)\", borderRadius:10, padding:\"10px 16px\", marginBottom:12 }}>\n"
     "          <span style={{ color:\"#fca5a5\", fontWeight:700, fontSize:13 }}>已選 {selectedIds.size} 筆</span>\n"
     "          <button onClick={deleteSelected} style={{ background:\"linear-gradient(135deg,#dc2626,#ef4444)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"7px 18px\", fontSize:13, fontWeight:700 }}>🗑 刪除選取</button>\n"
     "          <button onClick={()=>setSelectedIds(new Set())} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"7px 14px\", fontSize:13 }}>取消</button>\n"
     "        </div>\n"
     "      )}\n"
     "\n"
     "      {/* Document table */}"
    ),
    "B3: DocumentsTab batch bar"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH B4 — DocumentsTab: table header — add checkbox column + 操作 column
# ─────────────────────────────────────────────────────────────────────────────
patch(
    '          <thead><tr>{["文件編號","文件名稱","類別","版本","制定部門","制定日期","制定者","保存至","檔案",""].map(h=>(\n'
    '            <th key={h} style={{ textAlign:"left", padding:"10px 12px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>\n'
    '          ))}</tr></thead>',
    (
     '          <thead><tr>\n'
     '            <th style={{ padding:"10px 12px", borderBottom:"1px solid rgba(255,255,255,0.06)", width:36 }}>\n'
     '              <input type="checkbox" checked={selectedIds.size===enriched.length && enriched.length>0} onChange={toggleAll}\n'
     '                style={{ cursor:"pointer", accentColor:"#a78bfa", width:15, height:15 }} />\n'
     '            </th>\n'
     '            {["文件編號","文件名稱","類別","版本","制定部門","制定日期","制定者","保存至","檔案","操作"].map(h=>(\n'
     '              <th key={h} style={{ textAlign:"left", padding:"10px 12px", color:"#64748b", fontWeight:600, borderBottom:"1px solid rgba(255,255,255,0.06)", whiteSpace:"nowrap" }}>{h}</th>\n'
     '            ))}\n'
     '          </tr></thead>'
    ),
    "B4: DocumentsTab table header"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH B5 — DocumentsTab: each row — prepend checkbox, append edit+delete
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "              <tr key={doc.id} style={{ background: i%2===0?\"rgba(255,255,255,0.02)\":\"transparent\" }}>\n"
    "                <td style={{ padding:\"10px 12px\", color:\"#60a5fa\", fontWeight:700, fontFamily:\"monospace\" }}>{doc.id}</td>",
    (
     "              <tr key={doc.id} style={{ background: selectedIds.has(doc.id)?\"rgba(167,139,250,0.08)\":i%2===0?\"rgba(255,255,255,0.02)\":\"transparent\" }}>\n"
     "                <td style={{ padding:\"10px 12px\", width:36 }}>\n"
     "                  <input type=\"checkbox\" checked={selectedIds.has(doc.id)} onChange={()=>toggleSelect(doc.id)}\n"
     "                    style={{ cursor:\"pointer\", accentColor:\"#a78bfa\", width:15, height:15 }} />\n"
     "                </td>\n"
     "                <td style={{ padding:\"10px 12px\", color:\"#60a5fa\", fontWeight:700, fontFamily:\"monospace\" }}>{doc.id}</td>"
    ),
    "B5: DocumentsTab row checkbox"
)

patch(
    "                <td style={{ padding:\"10px 12px\" }}><button onClick={() => setModal(doc)} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:6, color:\"#94a3b8\", cursor:\"pointer\", padding:\"4px 10px\", fontSize:11 }}>詳情</button></td>",
    (
     "                <td style={{ padding:\"10px 12px\" }}><button onClick={() => setModal(doc)} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:6, color:\"#94a3b8\", cursor:\"pointer\", padding:\"4px 10px\", fontSize:11 }}>詳情</button></td>\n"
     "                <td style={{ padding:\"10px 12px\", whiteSpace:\"nowrap\" }}>\n"
     "                  <button onClick={() => setEditTarget({...doc})} style={{ background:\"rgba(96,165,250,0.12)\", border:\"1px solid rgba(96,165,250,0.3)\", borderRadius:6, color:\"#60a5fa\", cursor:\"pointer\", padding:\"4px 10px\", fontSize:11, marginRight:4 }}>✏ 編輯</button>\n"
     "                  <button onClick={() => deleteSingle(doc.id)} style={{ background:\"rgba(239,68,68,0.12)\", border:\"1px solid rgba(239,68,68,0.3)\", borderRadius:6, color:\"#f87171\", cursor:\"pointer\", padding:\"4px 10px\", fontSize:11 }}>🗑</button>\n"
     "                </td>"
    ),
    "B5b: DocumentsTab row edit/delete"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH B6 — DocumentsTab: edit modal (insert after detail modal block)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "      {/* ── SINGLE ADD MODAL ─────────────────────────────────────────────────── */}",
    (
     "      {/* ── EDIT MODAL ───────────────────────────────────────────────────────── */}\n"
     "      {editTarget && (\n"
     "        <Modal title={`編輯文件：${editTarget.id}`} onClose={() => setEditTarget(null)}>\n"
     "          <div style={{ display:\"flex\", flexDirection:\"column\", gap:14 }}>\n"
     "            <div style={{ display:\"grid\", gridTemplateColumns:\"1fr 1fr\", gap:12 }}>\n"
     "              {[[\"文件編號\",\"id\"],[\"文件名稱\",\"name\"],[\"版本\",\"version\"],[\"制定部門\",\"department\"],[\"制定者\",\"author\"]].map(([lbl,fld]) => (\n"
     "                <div key={fld}>\n"
     "                  <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>{lbl}</div>\n"
     "                  <input value={editTarget[fld]||\"\"} onChange={e=>setEditTarget(prev=>({...prev,[fld]:e.target.value}))} style={inputStyle} />\n"
     "                </div>\n"
     "              ))}\n"
     "            </div>\n"
     "            <div style={{ display:\"grid\", gridTemplateColumns:\"1fr 1fr 1fr\", gap:12 }}>\n"
     "              <div>\n"
     "                <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>類別</div>\n"
     "                <select value={editTarget.type} onChange={e=>setEditTarget(prev=>({...prev,type:e.target.value}))} style={inputStyle}>\n"
     "                  <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>\n"
     "                </select>\n"
     "              </div>\n"
     "              <div>\n"
     "                <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>制定日期</div>\n"
     "                <input type=\"date\" value={editTarget.createdDate||\"\"} onChange={e=>setEditTarget(prev=>({...prev,createdDate:e.target.value}))} style={inputStyle} />\n"
     "              </div>\n"
     "              <div>\n"
     "                <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>保存年限（年）</div>\n"
     "                <input type=\"number\" value={editTarget.retentionYears||16} onChange={e=>setEditTarget(prev=>({...prev,retentionYears:e.target.value}))} style={inputStyle} min=\"1\" max=\"99\" />\n"
     "              </div>\n"
     "            </div>\n"
     "            <div style={{ display:\"flex\", gap:10, justifyContent:\"flex-end\", paddingTop:4 }}>\n"
     "              <button onClick={()=>setEditTarget(null)} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"10px 20px\", fontWeight:600 }}>取消</button>\n"
     "              <button onClick={saveEdit} style={{ background:\"linear-gradient(135deg,#7c3aed,#4f46e5)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"10px 24px\", fontWeight:700, fontSize:14 }}>💾 儲存</button>\n"
     "            </div>\n"
     "          </div>\n"
     "        </Modal>\n"
     "      )}\n"
     "\n"
     "      {/* ── SINGLE ADD MODAL ─────────────────────────────────────────────────── */}"
    ),
    "B6: DocumentsTab edit modal"
)

# ═════════════════════════════════════════════════════════════════════════════
# PATCH C1 — LibraryTab: add setDocuments + setManuals to props
# ═════════════════════════════════════════════════════════════════════════════
patch(
    "function LibraryTab({ documents, manuals }) {",
    "function LibraryTab({ documents, setDocuments, manuals, setManuals }) {",
    "C1: LibraryTab props"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C2 — LibraryTab: tag _src + add selectedIds/editTarget state
# ─────────────────────────────────────────────────────────────────────────────
patch(
    (
     "  // Merge all docs with pdfs + manuals\n"
     "  const allItems = [\n"
     "    ...documents.filter(d => d.pdfPath),\n"
     "    ...manuals,\n"
     "  ];\n"
     "  const types = [\"全部\", \"管理手冊\", \"管理程序\", \"作業指導書\"];"
    ),
    (
     "  // Merge all docs with pdfs + manuals (tag source for CRUD routing)\n"
     "  const allItems = [\n"
     "    ...documents.filter(d => d.pdfPath).map(d => ({ ...d, _src: \"documents\" })),\n"
     "    ...manuals.map(m => ({ ...m, _src: \"manuals\" })),\n"
     "  ];\n"
     "  const types = [\"全部\", \"管理手冊\", \"管理程序\", \"作業指導書\"];\n"
     "\n"
     "  const [selectedIds, setSelectedIds] = useState(new Set());\n"
     "  const [editTarget, setEditTarget] = useState(null);"
    ),
    "C2: LibraryTab _src + state"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C3 — LibraryTab: CRUD functions (after typeColor line)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "  const typeColor = t => t===\"管理手冊\"?\"#a78bfa\":t===\"管理程序\"?\"#60a5fa\":\"#34d399\";",
    (
     "  const typeColor = t => t===\"管理手冊\"?\"#a78bfa\":t===\"管理程序\"?\"#60a5fa\":\"#34d399\";\n"
     "\n"
     "  function toggleSelect(id) {\n"
     "    setSelectedIds(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });\n"
     "  }\n"
     "  function toggleAll() {\n"
     "    if (selectedIds.size === filtered.length) setSelectedIds(new Set());\n"
     "    else setSelectedIds(new Set(filtered.map(d => d.id)));\n"
     "  }\n"
     "  function deleteItem(item) {\n"
     "    if (!window.confirm(`確定刪除「${item.name}」？`)) return;\n"
     "    if (item._src === \"documents\") setDocuments(prev => prev.filter(d => d.id !== item.id));\n"
     "    else setManuals(prev => prev.filter(m => m.id !== item.id));\n"
     "    setSelectedIds(prev => { const n = new Set(prev); n.delete(item.id); return n; });\n"
     "  }\n"
     "  function deleteSelected() {\n"
     "    const sel = filtered.filter(d => selectedIds.has(d.id));\n"
     "    if (!sel.length) return;\n"
     "    if (!window.confirm(`確定刪除選取的 ${sel.length} 筆文件？`)) return;\n"
     "    const docIds = new Set(sel.filter(d => d._src === \"documents\").map(d => d.id));\n"
     "    const manIds = new Set(sel.filter(d => d._src === \"manuals\").map(d => d.id));\n"
     "    if (docIds.size) setDocuments(prev => prev.filter(d => !docIds.has(d.id)));\n"
     "    if (manIds.size) setManuals(prev => prev.filter(m => !manIds.has(m.id)));\n"
     "    setSelectedIds(new Set());\n"
     "  }\n"
     "  function saveEdit() {\n"
     "    if (!editTarget) return;\n"
     "    if (editTarget._src === \"documents\") setDocuments(prev => prev.map(d => d.id === editTarget.id ? { ...editTarget } : d));\n"
     "    else setManuals(prev => prev.map(m => m.id === editTarget.id ? { ...editTarget } : m));\n"
     "    setEditTarget(null);\n"
     "  }\n"
    ),
    "C3: LibraryTab CRUD functions"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C4 — LibraryTab: batch action bar before cards grid
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "      {/* Document Cards Grid */}",
    (
     "      {/* Batch action bar */}\n"
     "      <div style={{ display:\"flex\", gap:10, alignItems:\"center\", marginBottom:14, flexWrap:\"wrap\" }}>\n"
     "        <label style={{ display:\"flex\", alignItems:\"center\", gap:7, cursor:\"pointer\", fontSize:13, color:\"#94a3b8\" }}>\n"
     "          <input type=\"checkbox\" checked={selectedIds.size===filtered.length && filtered.length>0} onChange={toggleAll}\n"
     "            style={{ cursor:\"pointer\", accentColor:\"#f97316\", width:15, height:15 }} />\n"
     "          全選（{filtered.length}）\n"
     "        </label>\n"
     "        {selectedIds.size > 0 && (\n"
     "          <>\n"
     "            <span style={{ color:\"#fca5a5\", fontWeight:700, fontSize:13 }}>已選 {selectedIds.size} 筆</span>\n"
     "            <button onClick={deleteSelected} style={{ background:\"linear-gradient(135deg,#dc2626,#ef4444)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"7px 18px\", fontSize:13, fontWeight:700 }}>🗑 刪除選取</button>\n"
     "            <button onClick={()=>setSelectedIds(new Set())} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"7px 14px\", fontSize:13 }}>取消</button>\n"
     "          </>\n"
     "        )}\n"
     "      </div>\n"
     "\n"
     "      {/* Document Cards Grid */}"
    ),
    "C4: LibraryTab batch bar"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C5 — LibraryTab: each card — add checkbox overlay + edit/delete buttons
# ─────────────────────────────────────────────────────────────────────────────
patch(
    (
     "          <div key={doc.id} style={{ background:\"rgba(255,255,255,0.03)\", border:\"1px solid rgba(255,255,255,0.08)\", borderRadius:14, padding:18, display:\"flex\", flexDirection:\"column\", gap:10 }}>\n"
     "            {/* Header */}\n"
     "            <div style={{ display:\"flex\", justifyContent:\"space-between\", alignItems:\"flex-start\" }}>\n"
     "              <div style={{ fontSize:11, fontFamily:\"monospace\", color:\"#60a5fa\", fontWeight:700 }}>{doc.id}</div>\n"
     "              <Badge color={typeColor(doc.type)}>{doc.type}</Badge>\n"
     "            </div>"
    ),
    (
     "          <div key={doc.id} style={{ background:selectedIds.has(doc.id)?\"rgba(249,115,22,0.08)\":\"rgba(255,255,255,0.03)\", border:\"1px solid \"+(selectedIds.has(doc.id)?\"rgba(249,115,22,0.4)\":\"rgba(255,255,255,0.08)\"), borderRadius:14, padding:18, display:\"flex\", flexDirection:\"column\", gap:10 }}>\n"
     "            {/* Header */}\n"
     "            <div style={{ display:\"flex\", justifyContent:\"space-between\", alignItems:\"flex-start\" }}>\n"
     "              <label style={{ display:\"flex\", alignItems:\"center\", gap:7, cursor:\"pointer\" }}>\n"
     "                <input type=\"checkbox\" checked={selectedIds.has(doc.id)} onChange={()=>toggleSelect(doc.id)}\n"
     "                  style={{ cursor:\"pointer\", accentColor:\"#f97316\", width:14, height:14 }} />\n"
     "                <span style={{ fontSize:11, fontFamily:\"monospace\", color:\"#60a5fa\", fontWeight:700 }}>{doc.id}</span>\n"
     "              </label>\n"
     "              <Badge color={typeColor(doc.type)}>{doc.type}</Badge>\n"
     "            </div>"
    ),
    "C5: LibraryTab card checkbox"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C6 — LibraryTab: replace card's PDF + preview buttons with PDF + edit + delete
# ─────────────────────────────────────────────────────────────────────────────
patch(
    (
     "            {/* PDF button */}\n"
     "            <div style={{ display:\"flex\", gap:8, marginTop:4 }}>\n"
     "              <a\n"
     "                href={encodeURI(doc.pdfPath)} target=\"_blank\" rel=\"noopener noreferrer\"\n"
     "                style={{ flex:1, background:\"linear-gradient(135deg,#dc2626,#ef4444)\", color:\"#fff\",\n"
     "                  padding:\"10px 0\", borderRadius:8, fontSize:13, fontWeight:700,\n"
     "                  textDecoration:\"none\", textAlign:\"center\" }}\n"
     "              >\n"
     "                &#128196; 開啟 PDF\n"
     "              </a>\n"
     "              <button onClick={()=>setPreview(doc.pdfPath)} style={{\n"
     "                background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.15)\",\n"
     "                borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\",\n"
     "                padding:\"10px 14px\", fontSize:12, fontWeight:600\n"
     "              }}>預覽</button>\n"
     "            </div>"
    ),
    (
     "            {/* PDF + action buttons */}\n"
     "            <div style={{ display:\"flex\", gap:8, marginTop:4, flexWrap:\"wrap\" }}>\n"
     "              {doc.pdfPath && (\n"
     "                <a href={encodeURI(doc.pdfPath)} target=\"_blank\" rel=\"noopener noreferrer\"\n"
     "                  style={{ flex:1, background:\"linear-gradient(135deg,#dc2626,#ef4444)\", color:\"#fff\",\n"
     "                    padding:\"9px 0\", borderRadius:8, fontSize:13, fontWeight:700,\n"
     "                    textDecoration:\"none\", textAlign:\"center\", minWidth:90 }}\n"
     "                >&#128196; PDF</a>\n"
     "              )}\n"
     "              {doc.pdfPath && (\n"
     "                <button onClick={()=>setPreview(doc.pdfPath)} style={{\n"
     "                  background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.15)\",\n"
     "                  borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\",\n"
     "                  padding:\"9px 12px\", fontSize:12, fontWeight:600\n"
     "                }}>預覽</button>\n"
     "              )}\n"
     "              <button onClick={()=>setEditTarget({...doc})} style={{ background:\"rgba(96,165,250,0.12)\", border:\"1px solid rgba(96,165,250,0.3)\", borderRadius:8, color:\"#60a5fa\", cursor:\"pointer\", padding:\"9px 12px\", fontSize:12, fontWeight:700 }}>✏</button>\n"
     "              <button onClick={()=>deleteItem(doc)} style={{ background:\"rgba(239,68,68,0.12)\", border:\"1px solid rgba(239,68,68,0.3)\", borderRadius:8, color:\"#f87171\", cursor:\"pointer\", padding:\"9px 12px\", fontSize:12, fontWeight:700 }}>🗑</button>\n"
     "            </div>"
    ),
    "C6: LibraryTab card buttons"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATCH C7 — LibraryTab: add edit modal before PDF preview modal
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "      {/* PDF Preview Modal (iframe) */}",
    (
     "      {/* ── EDIT MODAL ───────────────────────────────────────────────────────── */}\n"
     "      {editTarget && (\n"
     "        <Modal title={`編輯文件：${editTarget.id}`} onClose={() => setEditTarget(null)}>\n"
     "          <div style={{ display:\"flex\", flexDirection:\"column\", gap:14 }}>\n"
     "            <div style={{ display:\"grid\", gridTemplateColumns:\"1fr 1fr\", gap:12 }}>\n"
     "              {[[\"文件編號\",\"id\"],[\"文件名稱\",\"name\"],[\"版本\",\"version\"],[\"制定部門\",\"department\"],[\"制定者\",\"author\"]].map(([lbl,fld]) => (\n"
     "                <div key={fld}>\n"
     "                  <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>{lbl}</div>\n"
     "                  <input value={editTarget[fld]||\"\"} onChange={e=>setEditTarget(prev=>({...prev,[fld]:e.target.value}))} style={inputStyle} />\n"
     "                </div>\n"
     "              ))}\n"
     "            </div>\n"
     "            <div style={{ display:\"grid\", gridTemplateColumns:\"1fr 1fr\", gap:12 }}>\n"
     "              <div>\n"
     "                <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>類別</div>\n"
     "                <select value={editTarget.type||\"管理程序\"} onChange={e=>setEditTarget(prev=>({...prev,type:e.target.value}))} style={inputStyle}>\n"
     "                  <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>\n"
     "                </select>\n"
     "              </div>\n"
     "              <div>\n"
     "                <div style={{ fontSize:12, color:\"#64748b\", marginBottom:5 }}>說明</div>\n"
     "                <input value={editTarget.desc||\"\"} onChange={e=>setEditTarget(prev=>({...prev,desc:e.target.value}))} style={inputStyle} placeholder=\"簡短說明（選填）\" />\n"
     "              </div>\n"
     "            </div>\n"
     "            <div style={{ display:\"flex\", gap:10, justifyContent:\"flex-end\", paddingTop:4 }}>\n"
     "              <button onClick={()=>setEditTarget(null)} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"10px 20px\", fontWeight:600 }}>取消</button>\n"
     "              <button onClick={saveEdit} style={{ background:\"linear-gradient(135deg,#ea580c,#f97316)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"10px 24px\", fontWeight:700, fontSize:14 }}>💾 儲存</button>\n"
     "            </div>\n"
     "          </div>\n"
     "        </Modal>\n"
     "      )}\n"
     "\n"
     "      {/* PDF Preview Modal (iframe) */}"
    ),
    "C7: LibraryTab edit modal"
)

# ═════════════════════════════════════════════════════════════════════════════
print()
if errors:
    print(f"FAILED — {len(errors)} patch(es) not applied:")
    for e in errors:
        print("  •", e)
    sys.exit(1)
else:
    with open(SRC, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"All patches applied → saved ({len(code):,} chars)")
