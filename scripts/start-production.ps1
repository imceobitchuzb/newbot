# SAT MASTER — Production Runtime Supervisor (Windows)
# Hardened startup script for FastAPI, Next.js, Telegram Bot, and Cloudflare Tunnel

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " SAT MASTER — Starting Production Runtime" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Resolve Project Root
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot
Write-Host "[1/7] Working Directory: $ProjectRoot" -ForegroundColor Green

# 2. Check Environment Configuration (.env)
$EnvPath = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvPath)) {
    Write-Warning ".env file not found at $EnvPath! Copying from .env.example..."
    Copy-Item (Join-Path $ProjectRoot ".env.example") $EnvPath
}

# 3. Virtual Environment Check
$VenvPython = Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment not found at $VenvPython. Using system python..." -ForegroundColor Yellow
    $VenvPython = "python"
}

# 4. Database Migrations & Validation
Write-Host "[2/7] Running database migrations (Alembic)..." -ForegroundColor Yellow
& $VenvPython -m alembic -c backend/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Error "Alembic migration failed! Exiting."
    exit 1
}

Write-Host "[3/7] Verifying database seeding..." -ForegroundColor Yellow
& $VenvPython -m backend.app.db.seed

# 5. Build Frontend if .next is missing
$NextBuild = Join-Path $ProjectRoot "frontend\.next"
if (-not (Test-Path $NextBuild)) {
    Write-Host "[4/7] Frontend production build missing. Building Next.js..." -ForegroundColor Yellow
    Set-Location "$ProjectRoot\frontend"
    npm run build
    Set-Location $ProjectRoot
} else {
    Write-Host "[4/7] Frontend production build present." -ForegroundColor Green
}

# 6. Verify Running Daemons
Write-Host "[5/7] Verifying backend and frontend services..." -ForegroundColor Yellow

# Backend check
try {
    $beHealth = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  -> Backend is ALIVE (status: $($beHealth.status))" -ForegroundColor Green
} catch {
    Write-Host "  -> Starting Backend service on 127.0.0.1:8000..." -ForegroundColor Cyan
    Start-Process -FilePath $VenvPython -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# Frontend check
try {
    $feHealth = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  -> Frontend is ALIVE (status: $($feHealth.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  -> Starting Frontend production server on 127.0.0.1:3000..." -ForegroundColor Cyan
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd frontend && npm run start" -WindowStyle Minimized
    Start-Sleep -Seconds 3
}

# Bot check
Write-Host "[6/7] Ensuring Telegram Bot daemon is running..." -ForegroundColor Yellow
$botProc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*bot.py*" }
if (-not $botProc) {
    Start-Process -FilePath $VenvPython -ArgumentList "backend\bot.py" -WindowStyle Minimized
    Write-Host "  -> Bot process launched." -ForegroundColor Green
} else {
    Write-Host "  -> Bot process already running (PID: $($botProc.Id))." -ForegroundColor Green
}

# 7. Cloudflare Tunnel Status
Write-Host "[7/7] Checking Cloudflare Tunnel..." -ForegroundColor Yellow
$cfProc = Get-Process cloudflared -ErrorAction SilentlyContinue
if ($cfProc) {
    Write-Host "  -> Cloudflare tunnel is running (PID: $($cfProc.Id))." -ForegroundColor Green
} else {
    Write-Host "  -> Launching cloudflared quick tunnel..." -ForegroundColor Cyan
    $cfTool = Join-Path $ProjectRoot "tools\cloudflared.exe"
    if (Test-Path $cfTool) {
        Start-Process -FilePath $cfTool -ArgumentList "tunnel --url http://localhost:3000" -WindowStyle Minimized
    } else {
        Write-Warning "cloudflared.exe not found in tools\. Please start tunnel manually."
    }
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host " SAT MASTER PRODUCTION RUNTIME READY" -ForegroundColor Green
Write-Host " Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host " Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host " Docs:     http://localhost:8000/docs" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
