#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add inline cell editing + batch column edit to DocumentsTab.
- Click any cell (文件編號/名稱/類別/版本/部門/日期/制定者) to edit in-place
- Batch action bar gets a "修改欄位" button → pick field + new value → 套用至選取
"""

import sys

SRC = r"C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx"

with open(SRC, encoding="utf-8") as f:
    code = f.read()

errors = []

def patch(old, new, label=""):
    global code
    if old not in code:
        errors.append(label)
        print(f"  FAIL: {label}")
        return
    code = code.replace(old, new, 1)
    print(f"  OK:   {label}")

# ─────────────────────────────────────────────────────────────────────────────
# D1 — add inlineEdit + batchEdit state  (after editTarget)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "  const [selectedIds, setSelectedIds] = useState(new Set());\n"
    "  const [editTarget, setEditTarget] = useState(null);",

    "  const [selectedIds, setSelectedIds] = useState(new Set());\n"
    "  const [editTarget, setEditTarget] = useState(null);\n"
    "  const [inlineEdit, setInlineEdit] = useState({ id: null, field: null, value: \"\" });\n"
    "  const [batchEdit,  setBatchEdit]  = useState({ show: false, field: \"author\", value: \"\" });",
    "D1: inlineEdit + batchEdit state"
)

# ─────────────────────────────────────────────────────────────────────────────
# D2 — add saveInline + applyBatchEdit  (after saveEdit)
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "  function saveEdit() {\n"
    "    if (!editTarget) return;\n"
    "    setDocuments(prev => prev.map(d => d.id === editTarget.id ? { ...editTarget, retentionYears: parseInt(editTarget.retentionYears)||16 } : d));\n"
    "    setEditTarget(null);\n"
    "  }",

    "  function saveEdit() {\n"
    "    if (!editTarget) return;\n"
    "    setDocuments(prev => prev.map(d => d.id === editTarget.id ? { ...editTarget, retentionYears: parseInt(editTarget.retentionYears)||16 } : d));\n"
    "    setEditTarget(null);\n"
    "  }\n"
    "  // Inline single-cell save\n"
    "  function saveInline() {\n"
    "    if (!inlineEdit.id || !inlineEdit.field) return;\n"
    "    setDocuments(prev => prev.map(d => d.id === inlineEdit.id ? { ...d, [inlineEdit.field]: inlineEdit.value } : d));\n"
    "    setInlineEdit({ id: null, field: null, value: \"\" });\n"
    "  }\n"
    "  // Batch column edit: set one field for all selected rows\n"
    "  function applyBatchEdit() {\n"
    "    if (!batchEdit.value && batchEdit.field !== \"createdDate\") return;\n"
    "    if (!selectedIds.size) return;\n"
    "    setDocuments(prev => prev.map(d => selectedIds.has(d.id) ? { ...d, [batchEdit.field]: batchEdit.value } : d));\n"
    "    setBatchEdit(p => ({ ...p, show: false, value: \"\" }));\n"
    "  }",
    "D2: saveInline + applyBatchEdit"
)

# ─────────────────────────────────────────────────────────────────────────────
# D3 — add ilStyle + onIlKey helpers before dropZoneStyle
# ─────────────────────────────────────────────────────────────────────────────
patch(
    "  const dropZoneStyle = over => ({",

    "  // Inline-edit input style\n"
    "  const ilStyle = { background:\"rgba(124,58,237,0.15)\", border:\"1px solid rgba(124,58,237,0.6)\", borderRadius:5,\n"
    "    color:\"#e2e8f0\", padding:\"2px 7px\", fontSize:13, width:\"100%\", minWidth:60, outline:\"none\" };\n"
    "  const stopIl = () => setInlineEdit({ id: null, field: null, value: \"\" });\n"
    "  const onIlKey = e => { if (e.key === \"Enter\") saveInline(); if (e.key === \"Escape\") stopIl(); };\n"
    "  const startIl = (id, field, val) => setInlineEdit({ id, field, value: val || \"\" });\n"
    "\n"
    "  const dropZoneStyle = over => ({",
    "D3: ilStyle helpers"
)

# ─────────────────────────────────────────────────────────────────────────────
# D4 — replace batch action bar with extended version (adds batch-edit form)
# ─────────────────────────────────────────────────────────────────────────────
BATCH_BAR_OLD = (
    "      {/* Batch action bar */}\n"
    "      {selectedIds.size > 0 && (\n"
    "        <div style={{ display:\"flex\", alignItems:\"center\", gap:12, background:\"rgba(239,68,68,0.08)\", border:\"1px solid rgba(239,68,68,0.25)\", borderRadius:10, padding:\"10px 16px\", marginBottom:12 }}>\n"
    "          <span style={{ color:\"#fca5a5\", fontWeight:700, fontSize:13 }}>已選 {selectedIds.size} 筆</span>\n"
    "          <button onClick={deleteSelected} style={{ background:\"linear-gradient(135deg,#dc2626,#ef4444)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"7px 18px\", fontSize:13, fontWeight:700 }}>🗑 刪除選取</button>\n"
    "          <button onClick={()=>setSelectedIds(new Set())} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"7px 14px\", fontSize:13 }}>取消</button>\n"
    "        </div>\n"
    "      )}"
)

BATCH_BAR_NEW = (
    "      {/* Batch action bar */}\n"
    "      {selectedIds.size > 0 && (\n"
    "        <div style={{ marginBottom:12 }}>\n"
    "          <div style={{ display:\"flex\", alignItems:\"center\", gap:12, flexWrap:\"wrap\", background:\"rgba(239,68,68,0.08)\", border:\"1px solid rgba(239,68,68,0.25)\",\n"
    "            borderRadius: batchEdit.show ? \"10px 10px 0 0\" : 10, padding:\"10px 16px\" }}>\n"
    "            <span style={{ color:\"#fca5a5\", fontWeight:700, fontSize:13 }}>已選 {selectedIds.size} 筆</span>\n"
    "            <button onClick={deleteSelected} style={{ background:\"linear-gradient(135deg,#dc2626,#ef4444)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"7px 16px\", fontSize:13, fontWeight:700 }}>🗑 刪除選取</button>\n"
    "            <button onClick={()=>setBatchEdit(p=>({...p,show:!p.show}))} style={{ background:\"rgba(96,165,250,0.12)\", border:\"1px solid rgba(96,165,250,0.3)\", borderRadius:8, color:\"#60a5fa\", cursor:\"pointer\", padding:\"7px 16px\", fontSize:13, fontWeight:700 }}>✏ 批次修改欄位</button>\n"
    "            <button onClick={()=>{ setSelectedIds(new Set()); setBatchEdit(p=>({...p,show:false})); }} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"7px 14px\", fontSize:13 }}>取消</button>\n"
    "          </div>\n"
    "          {batchEdit.show && (\n"
    "            <div style={{ display:\"flex\", alignItems:\"center\", gap:10, flexWrap:\"wrap\", background:\"rgba(96,165,250,0.06)\",\n"
    "              border:\"1px solid rgba(96,165,250,0.25)\", borderTop:\"none\", borderRadius:\"0 0 10px 10px\", padding:\"10px 16px\" }}>\n"
    "              <span style={{ color:\"#94a3b8\", fontSize:13, whiteSpace:\"nowrap\" }}>將選取的 {selectedIds.size} 筆：</span>\n"
    "              <select value={batchEdit.field} onChange={e=>setBatchEdit(p=>({...p,field:e.target.value,value:\"\"}))} style={inputStyle}>\n"
    "                <option value=\"author\">制定者</option>\n"
    "                <option value=\"department\">制定部門</option>\n"
    "                <option value=\"type\">類別</option>\n"
    "                <option value=\"version\">版本</option>\n"
    "                <option value=\"createdDate\">制定日期</option>\n"
    "              </select>\n"
    "              <span style={{ color:\"#94a3b8\", fontSize:13 }}>改為：</span>\n"
    "              {batchEdit.field === \"type\"\n"
    "                ? <select value={batchEdit.value} onChange={e=>setBatchEdit(p=>({...p,value:e.target.value}))} style={inputStyle}>\n"
    "                    <option value=\"\">請選擇</option>\n"
    "                    <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>\n"
    "                  </select>\n"
    "                : batchEdit.field === \"createdDate\"\n"
    "                ? <input type=\"date\" value={batchEdit.value} onChange={e=>setBatchEdit(p=>({...p,value:e.target.value}))} style={inputStyle} />\n"
    "                : <input type=\"text\" value={batchEdit.value} onChange={e=>setBatchEdit(p=>({...p,value:e.target.value}))} style={{...inputStyle,minWidth:160}} placeholder=\"輸入新值…\" />\n"
    "              }\n"
    "              <button onClick={applyBatchEdit} style={{ background:\"linear-gradient(135deg,#0891b2,#06b6d4)\", border:\"none\", borderRadius:8, color:\"#fff\", cursor:\"pointer\", padding:\"7px 20px\", fontSize:13, fontWeight:700, whiteSpace:\"nowrap\" }}>套用至選取</button>\n"
    "              <button onClick={()=>setBatchEdit(p=>({...p,show:false}))} style={{ background:\"rgba(255,255,255,0.06)\", border:\"1px solid rgba(255,255,255,0.1)\", borderRadius:8, color:\"#94a3b8\", cursor:\"pointer\", padding:\"7px 12px\", fontSize:13 }}>✕</button>\n"
    "            </div>\n"
    "          )}\n"
    "        </div>\n"
    "      )}"
)
patch(BATCH_BAR_OLD, BATCH_BAR_NEW, "D4: batch action bar + batch-edit form")

# ─────────────────────────────────────────────────────────────────────────────
# D5 — replace the 7 static table cells with inline-editable versions
# ─────────────────────────────────────────────────────────────────────────────
CELLS_OLD = (
    "                <td style={{ padding:\"10px 12px\", color:\"#60a5fa\", fontWeight:700, fontFamily:\"monospace\" }}>{doc.id}</td>\n"
    "                <td style={{ padding:\"10px 12px\", color:\"#e2e8f0\", fontWeight:600 }}>{doc.name}</td>\n"
    "                <td style={{ padding:\"10px 12px\" }}><Badge color={doc.type===\"管理手冊\"?\"#a78bfa\":\"#60a5fa\"}>{doc.type}</Badge></td>\n"
    "                <td style={{ padding:\"10px 12px\" }}><span style={{ background:\"rgba(34,197,94,0.1)\", color:\"#4ade80\", borderRadius:6, padding:\"2px 8px\", fontWeight:700, fontFamily:\"monospace\" }}>v{doc.version}</span></td>\n"
    "                <td style={{ padding:\"10px 12px\", color:\"#94a3b8\" }}>{doc.department}</td>\n"
    "                <td style={{ padding:\"10px 12px\", color:\"#94a3b8\", whiteSpace:\"nowrap\" }}>{formatDate(doc.createdDate)}</td>\n"
    "                <td style={{ padding:\"10px 12px\", color:\"#94a3b8\" }}>{doc.author}</td>"
)

CELLS_NEW = (
    # 文件編號
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"id\")) startIl(doc.id,\"id\",doc.id); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"id\"\n"
    "                    ? <input autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#60a5fa\",fontWeight:700,fontFamily:\"monospace\"}} />\n"
    "                    : <span style={{color:\"#60a5fa\",fontWeight:700,fontFamily:\"monospace\"}}>{doc.id}</span>}\n"
    "                </td>\n"
    # 文件名稱
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"name\")) startIl(doc.id,\"name\",doc.name); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"name\"\n"
    "                    ? <input autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#e2e8f0\",fontWeight:600}} />\n"
    "                    : <span style={{color:\"#e2e8f0\",fontWeight:600}}>{doc.name}</span>}\n"
    "                </td>\n"
    # 類別 (select)
    "                <td style={{ padding:\"8px 12px\", cursor:\"pointer\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"type\")) startIl(doc.id,\"type\",doc.type); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"type\"\n"
    "                    ? <select autoFocus value={inlineEdit.value} onChange={e=>{setInlineEdit(p=>({...p,value:e.target.value}));setTimeout(saveInline,50);}} onBlur={saveInline} onClick={e=>e.stopPropagation()} style={{...ilStyle,padding:\"2px 4px\"}}>\n"
    "                        <option>管理手冊</option><option>管理程序</option><option>作業指導書</option><option>表單</option>\n"
    "                      </select>\n"
    "                    : <Badge color={doc.type===\"管理手冊\"?\"#a78bfa\":\"#60a5fa\"}>{doc.type}</Badge>}\n"
    "                </td>\n"
    # 版本
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"version\")) startIl(doc.id,\"version\",doc.version); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"version\"\n"
    "                    ? <input autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#4ade80\",fontWeight:700,fontFamily:\"monospace\",width:70}} />\n"
    "                    : <span style={{background:\"rgba(34,197,94,0.1)\",color:\"#4ade80\",borderRadius:6,padding:\"2px 8px\",fontWeight:700,fontFamily:\"monospace\"}}>v{doc.version}</span>}\n"
    "                </td>\n"
    # 制定部門
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"department\")) startIl(doc.id,\"department\",doc.department); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"department\"\n"
    "                    ? <input autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#94a3b8\"}} />\n"
    "                    : <span style={{color:\"#94a3b8\"}}>{doc.department}</span>}\n"
    "                </td>\n"
    # 制定日期 (date input)
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"createdDate\")) startIl(doc.id,\"createdDate\",doc.createdDate); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"createdDate\"\n"
    "                    ? <input type=\"date\" autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#94a3b8\"}} />\n"
    "                    : <span style={{color:\"#94a3b8\",whiteSpace:\"nowrap\"}}>{formatDate(doc.createdDate)}</span>}\n"
    "                </td>\n"
    # 制定者
    "                <td style={{ padding:\"8px 12px\", cursor:\"text\" }} title=\"點擊直接編輯\"\n"
    "                  onClick={()=>{ if(!(inlineEdit.id===doc.id&&inlineEdit.field===\"author\")) startIl(doc.id,\"author\",doc.author); }}>\n"
    "                  {inlineEdit.id===doc.id&&inlineEdit.field===\"author\"\n"
    "                    ? <input autoFocus value={inlineEdit.value} onChange={e=>setInlineEdit(p=>({...p,value:e.target.value}))} onBlur={saveInline} onKeyDown={onIlKey} onClick={e=>e.stopPropagation()} style={{...ilStyle,color:\"#94a3b8\"}} />\n"
    "                    : <span style={{color:\"#94a3b8\"}}>{doc.author}</span>}\n"
    "                </td>"
)

patch(CELLS_OLD, CELLS_NEW, "D5: 7 inline-editable cells")

# ─────────────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"FAILED — {len(errors)} patch(es) not applied:")
    for e in errors:
        print("  x", e)
    sys.exit(1)
else:
    with open(SRC, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"All patches OK -> saved ({len(code):,} chars)")
