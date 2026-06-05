@echo off
chcp 65001 >nul
setlocal
cd /d C:\Users\64638\OnmyojiAutoScript
set "PATH=C:\Progra~1\Netease\MuMu\nx_device\12.0\shell;%PATH%"

echo [OAS] Checking server on port 22270...
netstat -ano | findstr :22270 >nul
if %errorlevel%==0 (
  echo [OAS] Server is already running: http://127.0.0.1:22270/docs
  start "" http://127.0.0.1:22270/docs
  pause
  exit /b 0
)

echo [OAS] Starting MuMu ADB...
call start_mumu_adb.bat

echo [OAS] Starting OAS server...
start "OAS Server" cmd /k "cd /d C:\Users\64638\OnmyojiAutoScript && set PATH=C:\Progra~1\Netease\MuMu\nx_device\12.0\shell;%PATH% && venv\Scripts\python.exe server.py --host 0.0.0.0 --port 22270"

timeout /t 3 /nobreak >nul
netstat -ano | findstr :22270 >nul
if %errorlevel%==0 (
  echo [OAS] Started: http://127.0.0.1:22270/docs
  start "" http://127.0.0.1:22270/docs
) else (
  echo [OAS] Failed to start. Check the OAS Server window for errors.
)
pause
