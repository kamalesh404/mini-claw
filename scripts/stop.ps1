@echo off
title MiniClaw Shutdown

echo Stopping MiniClaw...

echo Stopping backend processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq MiniClaw Backend*" 2>nul
taskkill /f /im uvicorn.exe 2>nul

echo Stopping frontend processes...
taskkill /f /im node.exe /fi "WINDOWTITLE eq MiniClaw Frontend*" 2>nul
taskkill /f /im npm.exe /fi "WINDOWTITLE eq MiniClaw Frontend*" 2>nul

echo Stopping any remaining Python/Node processes on ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /f /pid %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /f /pid %%a 2>nul

echo MiniClaw stopped.
pause