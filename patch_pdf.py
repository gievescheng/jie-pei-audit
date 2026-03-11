with open(r'C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx', 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

print(f"Original lines: {len(lines)}")

# ── Step 1: Replace initialDocuments (lines 14-25, 0-indexed 13-24) ──────────
# Find the exact line range
start_doc = next(i for i,l in enumerate(lines) if 'const initialDocuments' in l)
end_doc   = next(i for i in range(start_doc, len(lines)) if lines[i].strip() == '];') + 1
print(f"initialDocuments: lines {start_doc+1}–{end_doc} (0-idx {start_doc}–{end_doc-1})")

new_docs = [
'const initialDocuments = [\n',
'  { id:"MM-01", name:"\u516c\u53f8\u54c1\u8cea\u624b\u518a",               type:"\u7ba1\u7406\u624b\u518a", version:"2.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"0  \u54c1\u8cea\u624b\u518a/\u516c\u53f8\u54c1\u8cea\u624b\u518a(2.0).pdf" },\n',
'  { id:"MP-01", name:"\u6587\u4ef6\u5316\u8cc7\u8a0a\u7ba1\u5236\u7a0b\u5e8f",          type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-12-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"" },\n',
'  { id:"MP-02", name:"\u7d44\u7e54\u74b0\u5883\u8207\u7e3e\u6548\u8a55\u4f30\u7ba1\u7406\u7a0b\u5e8f",   type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"2 \u7d44\u7e54\u74b0\u5883\u8207\u7e3e\u6548\u7ba1\u7406\u7a0b\u5e8f/\u7d44\u7e54\u74b0\u5883\u8207\u7e3e\u6548\u8a55\u4f30\u7ba1\u7406\u7a0b\u5e8f(2.0).pdf" },\n',
'  { id:"MP-03", name:"\u4eba\u529b\u8cc7\u6e90\u53ca\u8a13\u7df4\u7ba1\u7406\u7a0b\u5e8f",       type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-07-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"3 \u4eba\u529b\u8cc7\u6e90\u53ca\u8a13\u7df4\u7ba1\u7406\u7a0b\u5e8f/\u4eba\u529b\u8cc7\u6e90\u53ca\u8a13\u7df4\u7ba1\u7406\u7a0b\u5e8f.pdf" },\n',
'  { id:"MP-04", name:"\u8a2d\u65bd\u8a2d\u5099\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-12-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"4 \u8a2d\u65bd\u8a2d\u5099\u7ba1\u7406\u7a0b\u5e8f/\u8a2d\u65bd\u8a2d\u5099\u7ba1\u7406\u7a0b\u5e8f2.0.pdf" },\n',
'  { id:"MP-05", name:"\u91cf\u6e2c\u8cc7\u6e90\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u54c1\u7ba1\u8ab2", createdDate:"2025-12-01", author:"\u7a0b\u9f0e\u667a", retentionYears:16, pdfPath:"5 \u91cf\u6e2c\u8cc7\u6e90\u7ba1\u7406\u7a0b\u5e8f/\u91cf\u6e2c\u8cc7\u6e90\u7ba1\u7406\u7a0b\u5e8f2.0.pdf" },\n',
'  { id:"MP-06", name:"\u5de5\u4f5c\u74b0\u5883\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-07-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"6 \u5de5\u4f5c\u74b0\u5883\u7ba1\u7406\u7a0b\u5e8f/\u5de5\u4f5c\u74b0\u5883\u7ba1\u7406\u7a0b\u5e8f(\u6b63\u5f0f\u7248).pdf" },\n',
'  { id:"MP-07", name:"\u8cc7\u8a0a\u7ba1\u7406\u7a0b\u5e8f",               type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u8cc7\u8a0a\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"7 \u8cc7\u8a0a\u7ba1\u7406\u7a0b\u5e8f/\u8cc7\u8a0a\u7ba1\u7406\u7a0b\u5e8f2.0.pdf" },\n',
'  { id:"MP-08", name:"\u5ba2\u6236\u670d\u52d9\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"4.0", department:"\u696d\u52d9\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"8 \u5ba2\u6236\u670d\u52d9\u7ba1\u7406\u7a0b\u5e8f/\u5ba2\u6236\u670d\u52d9\u7ba1\u7406\u7a0b\u5e8f(4.0).pdf" },\n',
'  { id:"MP-09", name:"\u5167\u90e8\u7a3d\u6838\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u54c1\u7ba1\u8ab2", createdDate:"2025-07-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"9 \u5167\u90e8\u7a3d\u6838\u7ba1\u7406\u7a0b\u5e8f/\u5167\u90e8\u7a3d\u6838\u7ba1\u7406\u7a0b\u5e8f.pdf" },\n',
'  { id:"MP-10", name:"\u63a1\u8cfc\u53ca\u4f9b\u61c9\u5546\u7ba1\u7406\u7a0b\u5e8f",       type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u63a1\u8cfc\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"10 \u63a1\u8cfc\u53ca\u4f9b\u61c9\u5546\u7ba1\u7406\u7a0b\u5e8f/\u63a1\u8cfc\u53ca\u4f9b\u61c9\u5546\u7ba1\u7406\u7a0b\u5e8f(2.0).pdf" },\n',
'  { id:"MP-11", name:"\u751f\u7522\u4f5c\u696d\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u751f\u7522\u90e8", createdDate:"2025-10-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"11 \u751f\u7522\u4f5c\u696d\u7ba1\u7406\u7a0b\u5e8f/\u751f\u7522\u4f5c\u696d\u7ba1\u7406\u7a0b\u5e8f(2.0).pdf" },\n',
'  { id:"MP-12", name:"\u54c1\u8cea\u6aa2\u9a57\u7ba1\u7406\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"3.0", department:"\u54c1\u7ba1\u8ab2", createdDate:"2025-10-01", author:"\u7a0b\u9f0e\u667a", retentionYears:16, pdfPath:"12 \u54c1\u8cea\u6aa2\u9a57\u7ba1\u7406\u7a0b\u5e8f/\u54c1\u8cea\u6aa2\u9a57\u7ba1\u7406\u7a0b\u5e8f3.0.pdf" },\n',
'  { id:"MP-13", name:"\u4e0d\u5408\u683c\u54c1\u7ba1\u5236\u7a0b\u5e8f",           type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u54c1\u7ba1\u8ab2", createdDate:"2025-07-01", author:"\u7a0b\u9f0e\u667a", retentionYears:16, pdfPath:"13 \u4e0d\u5408\u683c\u54c1\u7ba1\u5236\u7a0b\u5e8f/\u4e0d\u5408\u683c\u54c1\u7ba1\u5236\u7a0b\u5e8f.pdf" },\n',
'  { id:"MP-14", name:"\u5009\u5132\u7ba1\u7406\u7a0b\u5e8f",               type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u5009\u5132\u90e8", createdDate:"2025-07-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"14 \u5009\u5132\u7ba1\u7406\u7a0b\u5e8f/\u5009\u5132\u7ba1\u7406\u7a0b\u5e8f.pdf" },\n',
'  { id:"MP-15", name:"\u4e0d\u7b26\u5408\u53ca\u77ef\u6b63\u63aa\u65bd\u7ba1\u7406\u7a0b\u5e8f",   type:"\u7ba1\u7406\u7a0b\u5e8f", version:"2.0", department:"\u54c1\u7ba1\u8ab2", createdDate:"2025-10-01", author:"\u7a0b\u9f0e\u667a", retentionYears:16, pdfPath:"15 \u4e0d\u7b26\u5408\u53ca\u77ef\u6b63\u63aa\u65bd\u7ba1\u7406\u7a0b\u5e8f/\u4e0d\u7b26\u5408\u53ca\u77ef\u6b63\u63aa\u65bd\u7ba1\u7406\u7a0b\u5e8f2.0.pdf" },\n',
'  { id:"MP-16", name:"\u7ba1\u7406\u5be9\u67e5\u7a0b\u5e8f",               type:"\u7ba1\u7406\u7a0b\u5e8f", version:"1.0", department:"\u7ba1\u7406\u90e8", createdDate:"2025-07-01", author:"\u8521\u6709\u70ba", retentionYears:16, pdfPath:"16 \u7ba1\u7406\u5be9\u67e5\u7a0b\u5e8f/\u7ba1\u7406\u5be9\u67e5\u7a0b\u5e8f.pdf" },\n',
'];\n',
'\n',
'// \u4e09\u968e\u6587\u4ef6\uff08\u8a2d\u5099\u624b\u518a\u53ca\u4f5c\u696d\u6307\u5c0e\u66f8\uff09\n',
'const initialManuals = [\n',
'  { id:"RW-01", name:"12\u5413 Wafer AOI \u4f7f\u7528\u624b\u518a",         type:"\u4f5c\u696d\u6307\u5c0e\u66f8", version:"1.0", department:"\u8a2d\u5099\u90e8", author:"\u9f3b\u53cb\u76ca\u96fb\u5b50", pdfPath:"\u4e09\u968e\u6587\u4ef6/RW01\u9f3b\u53cb\u76ca_12inch Wafer AOI\u4f7f\u7528\u624b\u518a_v1.0.pdf",         desc:"12\u5413 Wafer AOI\u7cfb\u7d71\u7528\u65bc\u7a81\u8d77\u76f8\u9060\u53ca\u5206\u5c42\u76f8\u9060\u76f8\u9023\u6aa2\u67e5" },\n',
'  { id:"RW-02", name:"12\u5413 Wafer Chipping AOI \u4f7f\u7528\u624b\u518a", type:"\u4f5c\u696d\u6307\u5c0e\u66f8", version:"1.0", department:"\u8a2d\u5099\u90e8", author:"\u9f3b\u53cb\u76ca\u96fb\u5b50", pdfPath:"\u4e09\u968e\u6587\u4ef6/RW02\u9f3b\u53cb\u76ca_12inch Wafer Chipping AOI\u4f7f\u7528\u624b\u518a_v1.0(\u7b5b\u9078\u6a5f).pdf", desc:"12\u5413\u7b5b\u9078\u6a5f\u7cfb\u7d71 Chipping \u7f3a\u9677\u6aa2\u67e5\u7528\u64cd\u4f5c\u624b\u518a" },\n',
'  { id:"RW-09a",name:"\u7a7a\u58d3\u6a5fAM3-37A-E30\u64cd\u4f5c\u624b\u518a",      type:"\u4f5c\u696d\u6307\u5c0e\u66f8", version:"1.0", department:"\u8a2d\u5099\u90e8", author:"\u539f\u5ee0\u5546",    pdfPath:"\u4e09\u968e\u6587\u4ef6/RW09\u7a7a\u58d3\u6a5fAM3-37A-E30_Manual.pdf",                                              desc:"\u7a7a\u58d3\u6a5f\u65e5\u5e38\u64cd\u4f5c\u3001\u4fdd\u990a\u8207\u6545\u969c\u6392\u9664\u624b\u518a" },\n',
'  { id:"RW-10", name:"\u624b\u6301\u5f0f\u5fae\u7c92\u5b50\u8a08\u6578\u5668\u64cd\u4f5c\u624b\u518a",   type:"\u4f5c\u696d\u6307\u5c0e\u66f8", version:"1.0", department:"\u54c1\u7ba1\u8ab2", author:"\u62d3\u751f\u79d1\u6280",   pdfPath:"\u4e09\u968e\u6587\u4ef6/RW10\u624b\u6301\u5f0f\u5fae\u7c92\u5b50\u8a08\u6578\u5668\u64cd\u4f5c\u624b\u518a Model9303+\u8edf\u9ad4.pdf",  desc:"TSI Model 9303 \u5fae\u7c92\u5b50\u8a08\u6578\u5668\u64cd\u4f5c\u8207\u8edf\u9ad4\u4f7f\u7528\u624b\u518a" },\n',
'  { id:"RW-11", name:"\u73bb\u7483\u6676\u5713\u5426\u5ea6\u91cf\u6e2c\u5c08\u64cd\u4f5c\u624b\u518a",  type:"\u4f5c\u696d\u6307\u5c0e\u66f8", version:"1.0", department:"\u54c1\u7ba1\u8ab2", author:"\u539f\u5ee0\u5546",    pdfPath:"\u4e09\u968e\u6587\u4ef6/RW11\u73bb\u7483\u6676\u5713\u5426\u5ea6\u91cf\u6e2c\u5c08\u64cd\u4f5c\u624b\u518a_MSCF-C-0300(001)(\u771f\u7a7a\u7522\u751f\u5668).pdf", desc:"MSCF-C-0300 TTV \u5426\u5ea6\u91cf\u6e2c\u5c08\u64cd\u4f5c\u624b\u518a" },\n',
'];\n',
]

# ── Step 2: Update DocumentsTab — open PDF button in modal (line ~383 area) ──
# We'll append the manuals data AFTER initialEnvRecords and BEFORE the helpers line

# Find where initialEnvRecords ends and helpers begin
env_end = next(i for i,l in enumerate(lines) if '// ─── HELPERS' in l)
print(f"HELPERS section at line {env_end+1}")

# Build the replacement: replace initialDocuments block, keep rest, insert initialManuals before HELPERS
part_before = lines[:start_doc]
part_docs   = new_docs
part_middle = lines[end_doc:env_end]
part_manuals_header = []  # already included in new_docs above (initialManuals defined there)
part_after  = lines[env_end:]

new_lines = part_before + part_docs + part_middle + part_after
print(f"New total lines: {len(new_lines)}")

with open(r'C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx', 'w', encoding='utf-8-sig') as f:
    f.writelines(new_lines)
print("Step1 initialDocuments + initialManuals written OK")
