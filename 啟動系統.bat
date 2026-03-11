@echo off
chcp 65001 >nul
title 潔沛企業 ISO 9001:2015 稽核系統

echo ================================================
echo  潔沛企業 ISO 9001:2015 稽核系統 啟動中...
echo ================================================
echo.

:: 停止所有可能佔用 8888 port 的 Python 程序
echo [1/3] 清除舊程序...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8888 "') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

:: 再次確認 port 8888 已釋放
netstat -ano 2>nul | findstr ":8888" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [警告] port 8888 仍被占用，嘗試強制清除...
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM python3.exe >nul 2>&1
    taskkill /F /IM python3.13.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: 啟動 Flask 伺服器
echo [2/3] 啟動 Flask 伺服器 (port 8888)...
cd /d "%~dp0"
start "潔沛稽核系統-Server" /B python server.py

:: 等待伺服器啟動（最多等 8 秒）
echo [3/3] 等待伺服器就緒...
set /a count=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a count+=1
curl -s -o nul -w "%%{http_code}" http://localhost:8888/ 2>nul | findstr "200" >nul
if %errorlevel%==0 goto server_ready
if %count% geq 8 goto timeout_error
goto wait_loop

:server_ready
echo.
echo ================================================
echo  [成功] 系統已啟動！
echo  網址：http://localhost:8888
echo ================================================
echo.
start http://localhost:8888
goto end

:timeout_error
echo.
echo [錯誤] 伺服器啟動逾時，請確認：
echo   1. Python 已安裝
echo   2. 已執行：pip install flask openpyxl requests
echo   3. 查看錯誤訊息
pause

:end
echo 伺服器持續運行中。關閉此視窗將停止系統。
echo.
python server.py
