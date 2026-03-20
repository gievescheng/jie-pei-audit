# 跨電腦開發使用說明

這份說明是給「之後換電腦、換地點，也能繼續處理這個專案」用的。

## 1. 第一次在新電腦下載專案

先安裝這些工具：

1. Git
2. Python 3.13
3. PostgreSQL

然後在 PowerShell 執行：

```powershell
git clone https://github.com/gievescheng/jie-pei-audit.git
cd jie-pei-audit
```

## 2. 請注意：Codex 要開正確資料夾

如果你要在 Codex 裡繼續做這個專案，請開這一層：

```text
...\jie-pei-audit
```

不要開它的上層資料夾。

白話講：

1. 開到專案根目錄，Codex 才知道要跟哪個 GitHub repo 比較
2. 如果開錯層，雲端 task 很容易再出現 `failed to compute git diff to remote`

## 3. Python 套件

這個專案目前主要有兩套後端：

1. 主系統 Flask
2. V2 FastAPI

建議先在專案根目錄建立虛擬環境：

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
```

再安裝需要的套件。

如果你只有要跑主系統，最少要安裝：

```powershell
pip install flask openpyxl python-docx pypdf requests
```

如果你也要跑 V2：

```powershell
pip install -r v2_backend\requirements-v2.txt
pip install -r erp_qms_core\backend\requirements.txt
```

## 4. PostgreSQL

V2 現在是走 PostgreSQL。

如果新電腦已經有 PostgreSQL，請把連線設定好。  
舊電腦原本用的格式是：

```text
postgresql://postgres:你的密碼@127.0.0.1:5432/auto_audit
```

如果要重新設定，可用：

```powershell
py -3.13 .\configure_v2_postgres.py --url "postgresql://postgres:你的密碼@127.0.0.1:5432/auto_audit" --write-config
```

## 5. OpenRouter API

如果你要用 AI 工作台裡的問答、摘要、比對等功能，還需要 OpenRouter key。

請把 key 放進私有設定，不要直接寫進 GitHub。

這個專案目前會把私有設定放在：

```text
%APPDATA%\AutoAudit\
```

所以換電腦後，這些私有設定要重新配置。

## 6. 啟動方式

最簡單的方式：

```powershell
.\啟動系統.bat
```

它會幫你啟動：

1. Flask 主系統
2. V2 FastAPI

主頁通常是：

```text
http://127.0.0.1:8888/
```

## 7. 日常同步方式

開始工作前先拉最新：

```powershell
git pull
```

做完後：

```powershell
git add .
git commit -m "寫這次修改的重點"
git push
```

## 8. 哪些檔不要手動上傳到 GitHub

這些屬於本機資料或私密設定，不要手動硬加進 repo：

1. `.v2_runtime.json`
2. `.google_calendar_config.json`
3. `.google_calendar_tokens.json`
4. `*.db`
5. `v2_backend/data/`
6. `erp_qms_core/backend/data/`
7. Office 暫存檔 `~$*`

這些已經在 `.gitignore` 內，但還是建議你有概念。

## 9. 如果雲端 task 又失敗

請先檢查這三件事：

1. Codex 開的是不是專案根目錄
2. 這個資料夾是不是有 `.git`
3. `git status` 是否正常、`git remote -v` 是否有 GitHub repo

最常見原因其實不是功能壞掉，而是「開錯資料夾」。

## 10. 建議工作習慣

如果你會在多台電腦工作，最穩的方式是：

1. 每次開始前先 `git pull`
2. 每次告一段落就 `commit + push`
3. 不要在兩台電腦同時改同一個檔太久

這樣衝突會少很多，也比較不會丟資料。
