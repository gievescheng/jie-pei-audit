# GitHub 上傳說明

這個資料夾已整理成可獨立上傳 GitHub 的專案根目錄。

## 建議做法

1. 只把 `自動稽核程式` 當成 Git repo。
2. GitHub 請建立 `Private repository`。
3. 不要把上一層 `C:\Users\USER\Documents\Codex` 當成上傳根目錄。

## 為什麼

上一層資料夾混有其他工作區、暫存檔與不相關資料，會讓：

1. Cloud task 無法正確計算 diff
2. Git 歷史很亂
3. 容易把不該上傳的資料一起推上去

## 已排除的內容

`.gitignore` 已排除下列常見不應上傳內容：

1. 本機私密設定
2. Google / OpenRouter runtime 設定
3. 本機資料庫
4. Python 快取
5. Office 暫存檔
6. 大型安裝程式 `*.exe`

## 初始化指令

在此資料夾內執行：

```powershell
git init
git branch -M main
git add .
git commit -m "Initial commit: auto audit QMS seed system"
git remote add origin https://github.com/<your-account>/<repo-name>.git
git push -u origin main
```

## Codex Cloud 注意事項

如果之後要在 Codex 中建立 cloud task：

1. 請開啟這個資料夾作為 workspace：
   `C:\Users\USER\Documents\Codex\自動稽核程式`
2. 不要開上一層 `C:\Users\USER\Documents\Codex`
3. 先完成：
   - 第一個 commit
   - 設定 remote
   - 推到 GitHub

做完後，Codex 才能正確計算「本機對遠端」的差異。
