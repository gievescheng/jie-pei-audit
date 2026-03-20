@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo 請輸入 PostgreSQL 連線字串:
set /p PGURL=
if "%PGURL%"=="" (
  echo 未輸入連線字串，已取消。
  exit /b 1
)

py -3.13 configure_v2_postgres.py --url "%PGURL%" --policy prod --write-config
if errorlevel 1 (
  echo PostgreSQL 設定失敗。
  exit /b 1
)

echo PostgreSQL 設定完成。
echo 請重新執行 啟動系統.bat
exit /b 0
