@echo off
chcp 65001 >nul
setlocal
cd /d C:\Users\64638\OnmyojiAutoScript
set "PATH=C:\Progra~1\Netease\MuMu\nx_device\12.0\shell;%PATH%"
echo [OAS] Checking server on port 22270...
netstat -ano | findstr ":22270" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo [OAS] Server is already running: http://127.0.0.1:22270/docs
  start "" http://127.0.0.1:22270/docs
  pause
  exit /b 0
)
echo [OAS] Starting MuMu ADB...
call "%~dp0start_mumu_adb.bat"
if errorlevel 1 (
  echo [OAS] MuMu ADB setup failed.
  pause
  exit /b 1
)
echo [OAS] Starting OAS server...
echo [OAS] Keep this window open. Close it only when you want to stop OAS server.
echo [OAS] Open http://127.0.0.1:22270/docs after startup completes.
venv\Scripts\python.exe server.py --host 0.0.0.0 --port 22270
echo [OAS] Server exited.
pause
