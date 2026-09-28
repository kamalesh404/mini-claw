@echo off
title MiniClaw Startup
cd /d "%~dp0..\mini-claw"

echo Starting MiniClaw...

echo [1/2] Starting Backend...
start "MiniClaw Backend" cmd /c "
cd /d \"%~dp0..\mini-claw\backend\"
call venv\Scripts\activate
python -m app.main
"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend...
start "MiniClaw Frontend" cmd /c "
cd /d \"%~dp0..\mini-claw\frontend\"
npm run preview -- --port 5173 --host
"

echo.
echo MiniClaw is starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C in the backend window to stop.
pause