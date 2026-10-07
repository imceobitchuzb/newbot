# SAT MASTER — 24/7 Service Supervisor Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      STARTING SAT MASTER 24/7          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Kill stale processes
Write-Host "Cleaning stale processes..." -ForegroundColor Yellow
Get-Process -Name node, python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*satmathbot*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 2. Start Backend FastAPI
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Green
$BackendProc = Start-Process -FilePath "$Root\backend\.venv\Scripts\python.exe" -ArgumentList "-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $Root -PassThru -WindowStyle Hidden

# 3. Start Frontend Next.js
Write-Host "Starting Next.js Frontend on port 3000..." -ForegroundColor Green
$FrontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run start" -WorkingDirectory "$Root\frontend" -PassThru -WindowStyle Hidden

# 4. Start Telegram Bot
Write-Host "Starting Telegram Bot 24/7 Polling..." -ForegroundColor Green
$BotProc = Start-Process -FilePath "$Root\backend\.venv\Scripts\python.exe" -ArgumentList "backend\bot.py" -WorkingDirectory $Root -PassThru -WindowStyle Hidden

Write-Host "SAT MASTER services running successfully." -ForegroundColor Cyan
