import re

with open(r'C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find the entire DocumentsTab function to replace
old = r"""function DocumentsTab({ documents, setDocuments }) {
  const [modal, setModal] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newDoc, setNewDoc] = useState({ id: "", name: "", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "", createdDate: "", author: "", retentionYears: 16 });
  const enriched = documents.map(d => {
    const expiryDate = new Date(d.createdDate);
    expiryDate.setFullYear(expiryDate.getFullYear() + d.retentionYears);
    const expiryStr = expiryDate.toISOString().split("T")[0];
    const daysToExpiry = daysUntil(expiryStr);
    return { ...d, expiryStr, daysToExpiry };
  });
  function handleAdd() {
    setDocuments(prev => [...prev, { ...newDoc, retentionYears: parseInt(newDoc.retentionYears) }]);
    setShowAdd(false);
    setNewDoc({ id: "", name: "", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "", createdDate: "", author: "", retentionYears: 16 });
  }"""

# Build the replacement — use triple-quoted string carefully
new = (
    'function DocumentsTab({ documents, setDocuments }) {\n'
    '  const [modal, setModal] = useState(null);\n'
    '  const [showAdd, setShowAdd] = useState(false);\n'
    '  const [err, setErr] = useState("");\n'
    '  const emptyDoc = { id: "", name: "", type: "\u7ba1\u7406\u7a0b\u5e8f", version: "1.0", department: "", createdDate: "", author: "", retentionYears: 16, fileName: "", fileSize: "", fileType: "", fileData: "" };\n'
    '  const [newDoc, setNewDoc] = useState({ ...emptyDoc });\n'
    '  const enriched = documents.map(d => {\n'
    '    const expiryDate = new Date(d.createdDate);\n'
    '    expiryDate.setFullYear(expiryDate.getFullYear() + (d.retentionYears || 16));\n'
    '    const expiryStr = expiryDate.toISOString().split("T")[0];\n'
    '    const daysToExpiry = daysUntil(expiryStr);\n'
    '    return { ...d, expiryStr, daysToExpiry };\n'
    '  });\n'
    '  // Parse docx core properties XML\n'
    '  function parseDocxMeta(arrayBuffer) {\n'
    '    const JSZipFallback = window.JSZip;\n'
    '    try {\n'
    '      const uint8 = new Uint8Array(arrayBuffer);\n'
    '      // Naive ZIP central dir: read core.xml as text by scanning for its content in the zip\n'
    '      // We locate the "core.xml" local file entry and grab the compressed stream\n'
    '      // For our purpose: look for dc:title, dc:creator, cp:revision between tags\n'
    '      const decoder = new TextDecoder("utf-8", { fatal: false });\n'
    '      const raw = decoder.decode(uint8);\n'
    '      const title = (raw.match(/<dc:title[^>]*>([^<]*)<\\/dc:title>/) || [])[1] || "";\n'
    '      const creator = (raw.match(/<dc:creator[^>]*>([^<]*)<\\/dc:creator>/) || [])[1] || "";\n'
    '      const lastModBy = (raw.match(/<cp:lastModifiedBy[^>]*>([^<]*)<\\/cp:lastModifiedBy>/) || [])[1] || "";\n'
    '      const revision = (raw.match(/<cp:revision[^>]*>([^<]*)<\\/cp:revision>/) || [])[1] || "";\n'
    '      const created = (raw.match(/<dcterms:created[^>]*>([^<]*)<\\/dcterms:created>/) || [])[1] || "";\n'
    '      const modified = (raw.match(/<dcterms:modified[^>]*>([^<]*)<\\/dcterms:modified>/) || [])[1] || "";\n'
    '      return { title, creator: creator || lastModBy, revision, created, modified };\n'
    '    } catch(e) { return {}; }\n'
    '  }\n'
    '  function handleFileUpload(e) {\n'
    '    const file = e.target.files[0];\n'
    '    if (!file) return;\n'
    '    const ext = file.name.split(".").pop().toLowerCase();\n'
    '    const sizeKB = (file.size / 1024).toFixed(1);\n'
    '    setNewDoc(prev => ({ ...prev, fileName: file.name, fileSize: sizeKB + " KB", fileType: ext.toUpperCase(), name: prev.name || file.name.replace(/\\.[^.]+$/, "") }));\n'
    '    const reader = new FileReader();\n'
    '    reader.onload = ev => {\n'
    '      const ab = ev.target.result;\n'
    '      // Store base64 for later download\n'
    '      const b64reader = new FileReader();\n'
    '      b64reader.onload = e2 => setNewDoc(prev => ({ ...prev, fileData: e2.target.result }));\n'
    '      b64reader.readAsDataURL(file);\n'
    '      // Try docx metadata extraction\n'
    '      if (ext === "docx" || ext === "xlsx" || ext === "pptx") {\n'
    '        const meta = parseDocxMeta(ab);\n'
    '        setNewDoc(prev => ({\n'
    '          ...prev,\n'
    '          name: meta.title || prev.name || file.name.replace(/\\.[^.]+$/, ""),\n'
    '          author: meta.creator || prev.author,\n'
    '          version: meta.revision ? `1.${parseInt(meta.revision)-1 >= 0 ? parseInt(meta.revision)-1 : 0}` : prev.version,\n'
    '          createdDate: meta.created ? meta.created.substring(0, 10) : (meta.modified ? meta.modified.substring(0, 10) : prev.createdDate),\n'
    '        }));\n'
    '      } else if (ext === "pdf") {\n'
    '        // For PDF: try to find /Author /CreationDate /Title in raw bytes\n'
    '        const decoder = new TextDecoder("latin1", { fatal: false });\n'
    '        const raw = decoder.decode(ab);\n'
    '        const pdfTitle = (raw.match(/\\/Title\\s*\\(([^)]+)\\)/) || [])[1] || "";\n'
    '        const pdfAuthor = (raw.match(/\\/Author\\s*\\(([^)]+)\\)/) || [])[1] || "";\n'
    '        const pdfDate = (raw.match(/\\/CreationDate\\s*\\(D:(\\d{8})/) || [])[1] || "";\n'
    '        const fmtDate = pdfDate.length === 8 ? `${pdfDate.slice(0,4)}-${pdfDate.slice(4,6)}-${pdfDate.slice(6,8)}` : "";\n'
    '        setNewDoc(prev => ({\n'
    '          ...prev,\n'
    '          name: pdfTitle || prev.name,\n'
    '          author: pdfAuthor || prev.author,\n'
    '          createdDate: fmtDate || prev.createdDate,\n'
    '        }));\n'
    '      }\n'
    '    };\n'
    '    reader.readAsArrayBuffer(file);\n'
    '  }\n'
    '  function handleAdd() {\n'
    '    if (!newDoc.id.trim() || !newDoc.name.trim() || !newDoc.department.trim() || !newDoc.createdDate) {\n'
    '      setErr("\u8acb\u586b\u5beb\u6240\u6709\u5fc5\u586b\u6b04\u4f4d\uff08\u7de8\u865f\u3001\u540d\u7a31\u3001\u90e8\u9580\u3001\u5236\u5b9a\u65e5\u671f\uff09"); return;\n'
    '    }\n'
    '    setErr("");\n'
    '    setDocuments(prev => [...prev, { ...newDoc, retentionYears: parseInt(newDoc.retentionYears) || 16 }]);\n'
    '    setShowAdd(false);\n'
    '    setNewDoc({ ...emptyDoc });\n'
    '  }'
)

if old in content:
    content = content.replace(old, new, 1)
    print("DocumentsTab header replaced OK")
else:
    print("ERROR: old string not found, trying manual slice approach")
    # Debug: show what's at that location
    idx = content.find("function DocumentsTab")
    print(f"DocumentsTab starts at char {idx}")
    print(repr(content[idx:idx+200]))

with open(r'C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx', 'w', encoding='utf-8-sig') as f:
    f.write(content)
print("File written OK")
