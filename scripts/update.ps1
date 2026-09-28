@echo off
title MiniClaw Update
cd /d "%~dp0..\mini-claw"

echo Updating MiniClaw...

echo [1/5] Pulling latest code...
git pull

echo [2/5] Updating Python dependencies...
cd backend
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo [3/5] Updating frontend dependencies...
cd ..\frontend
npm ci
npm run build

echo [4/5] Running database migrations...
cd ..\backend
call venv\Scripts\activate
alembic upgrade head

echo [5/5] Restarting services...
cd ..\..\scripts
call stop.ps1
timeout /t 2 /nobreak >nul
call start.ps1

echo.
echo Update complete!
echo.
pause