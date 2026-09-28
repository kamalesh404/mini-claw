@echo off
title MiniClaw Doctor
cd /d "%~dp0..\mini-claw"

echo ==========================================
echo   MiniClaw System Diagnostics
echo ==========================================
echo.

echo [1/10] Checking Python...
python --version 2>nul && echo   OK: Python found || echo   FAIL: Python not found

echo [2/10] Checking Node.js...
node --version 2>nul && echo   OK: Node.js found || echo   FAIL: Node.js not found

echo [3/10] Checking Git...
git --version 2>nul && echo   OK: Git found || echo   FAIL: Git not found

echo [4/10] Checking Docker...
docker --version 2>nul && echo   OK: Docker found || echo   WARN: Docker not found (optional)

echo [5/10] Checking Ollama...
ollama --version 2>nul && echo   OK: Ollama found || echo   FAIL: Ollama not found

echo [6/10] Checking GPU...
nvidia-smi 2>nul && echo   OK: NVIDIA GPU detected || echo   WARN: No NVIDIA GPU (CPU only mode)

echo [7/10] Checking CUDA...
nvcc --version 2>nul && echo   OK: CUDA available || echo   WARN: CUDA not available

echo [8/10] Checking Ollama models...
ollama list 2>nul | findstr /r "llama" >nul && echo   OK: Models available || echo   WARN: No models pulled (run: ollama pull llama3.2:3b)

echo [9/10] Checking database...
cd backend
python -c "
import asyncio
from app.database.session import init_db
try:
    asyncio.run(init_db())
    print('   OK: Database initialized')
except Exception as e:
    print(f'   FAIL: Database error - {e}')
" 2>nul

echo [10/10] Checking ports...
powershell -Command "
$ports = @(8000, 5173, 5432, 6379, 11434)
foreach ($p in $ports) {
    $listener = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() | Where-Object { $_.Port -eq $p }
    if ($listener) { Write-Host \"   WARN: Port $p in use\" } else { Write-Host \"   OK: Port $p available\" }
}
"

echo.
echo ==========================================
echo   Diagnostics Complete
echo ==========================================
pause