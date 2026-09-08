@echo off

echo Starting AI server...
start "AI Server" cmd /k "cd /d %~dp0back\ai && py ollamacli.py"

echo Starting Backend...
start "Backend" cmd /k "cd /d %~dp0back && py -m uvicorn server:app --reload"

echo Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0front && py -m http.server 5500"

echo.
echo All servers are starting...
pause