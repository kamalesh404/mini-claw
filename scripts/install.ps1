<# 
.SYNOPSIS
    MiniClaw Installation Script for Windows
.DESCRIPTION
    Installs MiniClaw Personal AI Automation Agent on Windows
.NOTES
    Run as Administrator for best results
#>

param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipOllama,
    [switch]$SkipDocker,
    [switch]$DevMode,
    [string]$InstallPath = "C:\MiniClaw"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  MiniClaw Installation Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warning "Not running as Administrator. Some features may not work correctly."
}

# Helper functions
function Test-Command($command) {
    try {
        $null = & $command --version 2>$null
        return $true
    } catch {
        return $false
    }
}

function Get-Version($command) {
    try {
        return & $command --version 2>$null
    } catch {
        return "Not found"
    }
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$pythonVersion = Get-Version python
$nodeVersion = Get-Version node
$gitVersion = Get-Version git
$dockerVersion = Get-Version docker

Write-Host "  Python: $pythonVersion" -ForegroundColor Gray
Write-Host "  Node.js: $nodeVersion" -ForegroundColor Gray
Write-Host "  Git: $gitVersion" -ForegroundColor Gray
Write-Host "  Docker: $dockerVersion" -ForegroundColor Gray

# Install Python if needed
if (-not $SkipPython -and -not (Test-Command python)) {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
    refreshenv
}

# Install Node.js if needed
if (-not $SkipNode -and -not (Test-Command node)) {
    Write-Host "Installing Node.js..." -ForegroundColor Yellow
    winget install --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
    refreshenv
}

# Install Git if needed
if (-not (Test-Command git)) {
    Write-Host "Installing Git..." -ForegroundColor Yellow
    winget install --id Git.Git --silent --accept-source-agreements --accept-package-agreements
    refreshenv
}

# Install Docker if needed
if (-not $SkipDocker -and -not (Test-Command docker)) {
    Write-Host "Installing Docker Desktop..." -ForegroundColor Yellow
    winget install --id Docker.DockerDesktop --silent --accept-source-agreements --accept-package-agreements
    Write-Warning "Docker Desktop requires a restart. Please restart and re-run this script."
}

# Install Ollama if needed
if (-not $SkipOllama) {
    Write-Host "Checking Ollama..." -ForegroundColor Yellow
    if (-not (Test-Command ollama)) {
        Write-Host "Installing Ollama..." -ForegroundColor Yellow
        winget install --id Ollama.Ollama --silent --accept-source-agreements --accept-package-agreements
    }
    
    # Pull default model
    Write-Host "Pulling default model (llama3.2:3b)..." -ForegroundColor Yellow
    Start-Process ollama -ArgumentList "pull llama3.2:3b" -Wait -NoNewWindow
}

# Create installation directory
Write-Host "Creating installation directory..." -ForegroundColor Yellow
$installPath = $InstallPath
if (-not (Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
}

# Clone or update repository
Write-Host "Setting up repository..." -ForegroundColor Yellow
$repoPath = Join-Path $installPath "mini-claw"
if (Test-Path (Join-Path $repoPath ".git")) {
    Write-Host "Updating existing repository..." -ForegroundColor Yellow
    Set-Location $repoPath
    git pull
} else {
    Write-Host "Cloning repository..." -ForegroundColor Yellow
    git clone https://github.com/yourusername/mini-claw.git $repoPath
    Set-Location $repoPath
}

# Setup Python virtual environment
Write-Host "Setting up Python environment..." -ForegroundColor Yellow
$venvPath = Join-Path $repoPath "backend" "venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}
& "$venvPath\Scripts\pip.exe" install --upgrade pip
& "$venvPath\Scripts\pip.exe" install -r "$repoPath\backend\requirements.txt"

# Setup frontend
Write-Host "Setting up frontend..." -ForegroundColor Yellow
Set-Location "$repoPath\frontend"
npm ci
npm run build

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
Set-Location "$repoPath\backend"
& "$venvPath\Scripts\python.exe" -c "
import asyncio
from app.database.session import init_db
asyncio.run(init_db())
print('Database initialized')
"

# Create .env file if not exists
$envPath = Join-Path $repoPath ".env"
$envExamplePath = Join-Path $repoPath ".env.example"
if (-not (Test-Path $envPath) -and (Test-Path $envExamplePath)) {
    Copy-Item $envExamplePath $envPath
    Write-Host "Created .env from .env.example. Please edit it with your settings." -ForegroundColor Yellow
}

# Create start scripts
Write-Host "Creating start scripts..." -ForegroundColor Yellow

$startScript = @"
@echo off
title MiniClaw Backend
cd /d "$repoPath\backend"
call venv\Scripts\activate
python -m app.main
"@
$startScript | Out-File -FilePath (Join-Path $installPath "start-backend.bat") -Encoding ASCII

$startFrontend = @"
@echo off
title MiniClaw Frontend
cd /d "$repoPath\frontend"
npm run preview -- --port 5173 --host
"@
$startFrontend | Out-File -FilePath (Join-Path $installPath "start-frontend.bat") -Encoding ASCII

$startAll = @"
@echo off
title MiniClaw
cd /d "$repoPath"

echo Starting MiniClaw...
start "MiniClaw Backend" cmd /c call "$installPath\start-backend.bat"
timeout /t 3 /nobreak >nul
start "MiniClaw Frontend" cmd /c "$installPath\start-frontend.bat"

echo.
echo MiniClaw is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/api/docs
echo.
pause
"@
$startAll | Out-File -FilePath (Join-Path $installPath "start-miniclaw.bat") -Encoding ASCII

# Create desktop shortcut
if (-not $DevMode) {
    Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut([Environment]::GetFolderPath('Desktop') + "\MiniClaw.lnk")
    $shortcut.TargetPath = Join-Path $installPath "start-miniclaw.bat"
    $shortcut.WorkingDirectory = $installPath
    $shortcut.IconLocation = Join-Path $repoPath "frontend\public\icon.ico"
    $shortcut.Save()
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installation path: $installPath" -ForegroundColor Gray
Write-Host "Repository path: $repoPath" -ForegroundColor Gray
Write-Host ""
Write-Host "To start MiniClaw:" -ForegroundColor Yellow
Write-Host "  1. Run: $installPath\start-miniclaw.bat" -ForegroundColor Gray
Write-Host "  2. Or run backend and frontend separately:" -ForegroundColor Gray
Write-Host "     - Backend: $installPath\start-backend.bat" -ForegroundColor Gray
Write-Host "     - Frontend: $installPath\start-frontend.bat" -ForegroundColor Gray
Write-Host ""
Write-Host "Access points:" -ForegroundColor Yellow
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor Gray
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Edit $repoPath\.env with your settings" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Configure .env with your GitHub token, API keys, etc." -ForegroundColor Gray
Write-Host "  2. Pull additional Ollama models: ollama pull <model>" -ForegroundColor Gray
Write-Host "  3. Open http://localhost:5173 and create your account" -ForegroundColor Gray
Write-Host ""