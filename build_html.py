import re

# Read the JSX file
with open(r'C:\Users\USER\Desktop\自動稽核程式\audit-dashboard.jsx', 'r', encoding='utf-8-sig') as f:
    jsx_content = f.read()

# Remove the import line (React/useState are globals in CDN mode)
jsx_content = re.sub(r'^import\s+.*?from\s+["\']react["\'];\s*\n', '', jsx_content, flags=re.MULTILINE)

# Remove "export default" from App so it stays as a plain function
jsx_content = jsx_content.replace('export default function App()', 'function App()')

html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>潔沛企業有限公司 ─ ISO 9001:2015 自動稽核系統</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;600;700;800&display=swap" rel="stylesheet" />
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <!-- SheetJS：XLSX 讀取／寫入（用於 XLSX 資料匯入） -->
  <script src="https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0a0f1e;
      color: #e2e8f0;
      font-family: 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 3px; }
    @media print {
      body { background: #fff; color: #000; }
    }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel" data-presets="react">
    const { useState, useEffect } = React;
''' + jsx_content + '''
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>'''

with open(r'C:\Users\USER\Desktop\自動稽核程式\index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('index.html built OK')
print(f'Total HTML size: {len(html)} bytes ({len(html)//1024} KB)')
