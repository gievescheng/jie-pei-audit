@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

title ISO 9001 Audit Dashboard
cd /d "%~dp0"

echo ================================================
echo ISO 9001 Audit Dashboard
echo ================================================
echo.

echo [1/5] Clearing ports 8888 and 8890...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8888 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8890 " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

set "PYTHON_EXE="
set "PYTHON_ARGS="
set "STORE_PY="

py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3.13"
)

if not defined PYTHON_EXE (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)

if not defined PYTHON_EXE (
    for /f "tokens=2,*" %%a in ('reg query "HKCU\Software\Python\PythonCore\3.13\InstallPath" /v ExecutablePath 2^>nul ^| find /I "ExecutablePath"') do set "STORE_PY=%%b"
    if defined STORE_PY if exist "!STORE_PY!" (
        set "PYTHON_EXE=!STORE_PY!"
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Python 3.13 was not found.
    echo Tried: py -3.13, python, and the Store Python registry path.
    pause
    exit /b 1
)

echo [2/5] Using !PYTHON_EXE! !PYTHON_ARGS!
echo [3/5] Starting Flask server...
if defined PYTHON_ARGS (
    start "audit-server" /B "!PYTHON_EXE!" !PYTHON_ARGS! server.py
) else (
    start "audit-server" /B "!PYTHON_EXE!" server.py
)

echo [4/5] Starting V2 FastAPI server...
if defined PYTHON_ARGS (
    start "audit-v2" /B "!PYTHON_EXE!" !PYTHON_ARGS! run_v2.py
) else (
    start "audit-v2" /B "!PYTHON_EXE!" run_v2.py
)

echo [5/5] Waiting for http://127.0.0.1:8888/ and http://127.0.0.1:8890/api/v2/health ...
set /a count=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a count+=1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8888/ -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8890/api/v2/health -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if !errorlevel! EQU 0 (
    powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8888/ -TimeoutSec 2; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if !errorlevel! EQU 0 goto server_ready
)
if !count! GEQ 20 goto timeout_error
goto wait_loop

:server_ready
echo.
echo ================================================
echo Services ready:
echo - Flask UI: http://127.0.0.1:8888/
echo - V2 API  : http://127.0.0.1:8890/api/v2/health
echo ================================================
start "" http://127.0.0.1:8888/
exit /b 0

:timeout_error
echo.
echo [ERROR] Services did not become ready in time.
echo Check Python dependencies: flask openpyxl requests fastapi uvicorn sqlalchemy httpx python-multipart
pause
exit /b 1
