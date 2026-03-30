# OpenDataLoader PDF 整合方案（PoC）

## 1. 這份文件的目的
這份文件是給後續 AI / 工程人員使用的整合方案。
目標不是立刻全面替換目前的 PDF 解析，而是先做一個 **小型試點（PoC）**，確認 `opendataloader-pdf` 是否真的能提升這個專案的 PDF 讀取準確率。

---

## 2. 先講結論
### 值不值得試？
**值得試。**

但要用對地方。

### 最適合先拿來試的 PDF 類型
1. **電腦輸出的正式 PDF**
   - 例如 SOP、程序書、正式表單 PDF
2. **掃描但內容是印刷體的 PDF**
   - 例如列印後再掃描的稽核表、程序表
3. **表格多、版面複雜的 PDF**
   - 例如多欄、跨欄、表格排版較複雜的 PDF

### 不適合一開始就依賴的 PDF 類型
1. **手寫掃描 PDF**
   - 例如手寫環境監控表、手寫檢點表

結論：
- `opendataloader-pdf` 對「正式 PDF / 印刷體掃描 PDF」很可能有幫助。
- 對「手寫 PDF」不能當成正式可靠解法。

---

## 3. 參考來源
目標套件：
- GitHub: <https://github.com/opendataloader-project/opendataloader-pdf>

從 README 可確認的重點：
1. 可輸出 `Markdown / JSON / HTML`
2. 提供每個元素的 `bounding boxes`
3. 強調正確的閱讀順序、表格、標題層級
4. 支援掃描 PDF 與 OCR
5. 需要 `Java 11+` 與 Python 環境
6. README 提醒：每次 `convert()` 會啟 JVM，建議批次處理

---

## 4. 它對目前專案最可能有幫助的地方
目前專案內，PDF 主要用在這幾種情境：

### A. 稽核計畫 / 不符合管理 的 PDF 匯入
目前相關 API：
- `server.py`
  - `/api/nonconformances/import`
  - `/api/audit-plans/import`
  - `/api/environment-records/import`

目前實際解析入口：
- `ops_data.py`
  - `parse_nonconformance_import()`
  - `parse_auditplan_import()`
  - `parse_environment_import()`

目前 PDF 文字抽取是：
- `ops_data.py` 中的 `_flatten_pdf()`
- 使用 `pypdf.PdfReader(...).extract_text()`

這一層的限制很明顯：
1. 對複雜排版 PDF 不一定穩
2. 對掃描 PDF 幾乎沒有幫助
3. 對表格欄位定位能力很弱

所以 `opendataloader-pdf` 最值得先替換的，就是這一層「PDF 轉結構化文字 / JSON」能力。

### B. AI 工作台 / 文件知識庫 / 文件稽核
這一塊如果之後要讓 PDF 文件更容易進 RAG 或文件稽核流程，`Markdown + JSON + bounding boxes` 的輸出形式很有價值。

---

## 5. 不建議的做法
### 不要直接做的事
1. 不要直接把目前所有 PDF 解析全部換成 `opendataloader-pdf`
2. 不要一開始就拿手寫 PDF 當正式準確率標準
3. 不要把「通用 PDF parser」當成「欄位解析器」

白話講：
- 這個工具適合先把 PDF 讀得更乾淨
- 但真正把內容對應到 `dept / scope / date / responsible` 這些欄位，仍然需要你自己的規則

---

## 6. 建議的 PoC 範圍
### PoC 只做 3 條路
#### 路線 1：稽核計畫 PDF 匯入
目標：測試它對正式稽核計畫 PDF 的抽取是否比現在更準

先接到：
- `ops_data.py -> parse_auditplan_import()`

作法：
1. 如果上傳檔案是 `.pdf`
2. 先走 `opendataloader-pdf`
3. 把輸出的 Markdown / JSON 轉成純文字或欄位候選
4. 再套回現在的欄位映射邏輯

優先要抓的欄位：
1. `id`
2. `scheduledDate`
3. `dept`
4. `scope`
5. `auditor`
6. `auditee`
7. `status`

#### 路線 2：不符合管理 PDF 匯入
目標：讓正式 PDF 報告的欄位擷取比現在更穩

先接到：
- `ops_data.py -> parse_nonconformance_import()`

優先要抓的欄位：
1. `id`
2. `date`
3. `dept`
4. `type`
5. `severity`
6. `description`
7. `rootCause`
8. `correctiveAction`
9. `responsible`
10. `dueDate`
11. `status`

#### 路線 3：文件知識抽取專用試點
目標：不是匯入表單，而是拿正式 PDF 文件測看看它對 RAG / 文件稽核有沒有明顯提升

建議先測：
1. 一份 SOP PDF
2. 一份管理程序 PDF
3. 一份複雜表格 PDF

用途：
- 看 Markdown/JSON 是否比目前純抽字更適合後續文件知識庫

---

## 7. 不建議先碰的部分
### 環境監控手寫 PDF
例如這份：
- `C:\Users\USER\Desktop\NAS\公用\ISO文件建立\潔沛修訂版\電子掃描紀錄\6 工作環境管理程序\潔沛環境監控記錄表202511.pdf`

這一類文件目前不建議作為 PoC 主目標。

原因：
1. 掃描影像 PDF
2. 內容還是手寫
3. 就算 OCR 能抽一些文字，也不代表欄位能穩定對上
4. 這種資料若要進正式系統，仍然建議：
   - 手寫完成後
   - 轉成電子模板
   - 再上傳

---

## 8. 建議的技術整合方式
### 8.1 新增獨立 adapter，不要直接把邏輯塞進舊函式
建議新增檔案：
- `C:\Users\USER\Documents\Codex\自動稽核程式\pdf_structured_parser.py`

用途：
1. 封裝 `opendataloader-pdf` 呼叫
2. 對外只提供簡單介面

例如：
- `extract_pdf_markdown(path)`
- `extract_pdf_json(path)`
- `extract_pdf_text_for_form(path)`

這樣可以避免 `ops_data.py` 越來越大。

### 8.2 在現有匯入流程中加「PDF 專用分支」
在：
- `parse_nonconformance_import()`
- `parse_auditplan_import()`

中加規則：
1. 如果檔案是 `.docx` / `.xlsx`
   - 維持現有方式
2. 如果檔案是 `.pdf`
   - 優先走 `opendataloader-pdf`
   - 若失敗，再 fallback 到目前 `_flatten_pdf()`

這樣風險最低。

### 8.3 不要讓這個工具直接決定欄位
流程應該是：
1. `opendataloader-pdf` 負責把 PDF 轉成比較乾淨的內容
2. 你的程式仍然負責：
   - label matching
   - date parsing
   - 欄位映射
   - 缺欄提示

也就是：
- 它是「抽取器」
- 不是「最終欄位判官」

---

## 9. PoC 成功標準
這次 PoC 不要抽象說「感覺比較好」，要有明確比較。

### 準備 3 組測試檔
1. 稽核計畫 PDF（正式電腦輸出）
2. 不符合報告 PDF（正式電腦輸出）
3. 掃描印刷體 PDF（非手寫）

### 每組比 2 種結果
1. 現有方法
   - `_flatten_pdf()` + 既有欄位映射
2. 新方法
   - `opendataloader-pdf` + 既有欄位映射

### 比較指標
1. 是否讀到正確欄位數
2. 讀錯欄位數
3. 缺欄數
4. 是否改善表格 / 多欄閱讀順序
5. 是否能更穩定抓出 `dept / scope / date / id`

### PoC 判定標準
如果同一批測試 PDF 中：
1. 正確欄位數明顯增加
2. 錯誤欄位數下降
3. 不影響 `.docx / .xlsx` 現有流程

那就值得進一步整合。

---

## 10. 安裝與環境前提
### 前提
1. Java 11+
2. Python 可正常執行
3. 可在本機安裝 `opendataloader-pdf`

### 建議安裝方式
先在獨立環境測：
1. `java -version`
2. `pip install -U opendataloader-pdf`

### 注意
README 提醒：
- 每次 `convert()` 會起 JVM
- 所以實作時要避免一筆一筆 PDF 反覆起 process
- PoC 階段可以先接受，但正式整合時最好做批次或快取

---

## 11. 建議給其他 AI / 工程人員的實作順序
### Phase 1：最小 adapter
1. 建 `pdf_structured_parser.py`
2. 做最小呼叫封裝
3. 輸出 markdown / text
4. 先能在本機測一份 PDF 成功

### Phase 2：接稽核計畫 PDF
1. 只接 `parse_auditplan_import()` 的 PDF 分支
2. 做 fallback
3. 加測試

### Phase 3：接不符合管理 PDF
1. 只接 `parse_nonconformance_import()` 的 PDF 分支
2. 做 fallback
3. 加測試

### Phase 4：文件知識抽取 PoC
1. 把正式 PDF 文件轉 Markdown / JSON
2. 跟目前 V2 文件稽核 / 知識問答流程比較品質

---

## 12. 目前對這個專案的最終建議
### 建議採用方式
**建議採用，但只做 PoC 整合，不要直接全面替換。**

最好的策略是：
1. 把它當成「PDF 專用抽取器」
2. 先接 `稽核計畫` 與 `不符合管理`
3. 讓現有欄位映射邏輯繼續負責最後判定
4. 先不碰手寫 PDF

### 一句話結論
它很可能能讓你專案在「正式 PDF / 掃描印刷 PDF」的讀取上更準，
但不應該被當成手寫 PDF 的萬能解法，也不建議一次全面替換目前所有 PDF 解析流程。
