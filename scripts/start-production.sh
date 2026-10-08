#!/usr/bin/env bash
# SAT MASTER — Production Runtime Supervisor (Linux / VPS)
# Hardened startup script with Docker Compose or systemd services

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=================================================="
echo " SAT MASTER — Starting Production Runtime (Linux)"
echo "=================================================="

# 1. Environment validation
if [ ! -f ".env" ]; then
    echo "[!] .env file not found. Creating from .env.example..."
    cp .env.example .env
fi

# 2. Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "[+] Docker detected. Launching via Docker Compose..."
    docker-compose -f docker-compose.yml up -d --build
    
    echo "[+] Running database migrations..."
    docker-compose exec -T backend alembic -c backend/alembic.ini upgrade head
    
    echo "[+] Verifying seed data..."
    docker-compose exec -T backend python -m backend.app.db.seed
    
    echo "[+] Checking service health..."
    sleep 5
    curl -f http://127.0.0.1:8000/health || echo "[!] Backend health check pending"
    echo "=================================================="
    echo " SAT MASTER Production Running via Docker Compose"
    echo "=================================================="
    exit 0
fi

# 3. Direct host execution fallback (systemd / supervisor)
echo "[+] Starting direct host execution..."

# Activate python virtualenv
if [ -d "backend/.venv" ]; then
    source backend/.venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "[1/4] Applying database migrations..."
python -m alembic -c backend/alembic.ini upgrade head

# Run seed
echo "[2/4] Ensuring question bank is seeded..."
python -m backend.app.db.seed

# Build Next.js if missing
if [ ! -d "frontend/.next" ]; then
    echo "[3/4] Building frontend..."
    (cd frontend && npm ci && npm run build)
fi

echo "[4/4] Starting services in background..."
# Start Backend
nohup python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start Frontend
nohup bash -c "cd frontend && npm run start -- -p 3000" > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

# Start Bot
nohup python backend/bot.py > bot.log 2>&1 &
BOT_PID=$!
echo "Bot started (PID: $BOT_PID)"

echo "=================================================="
echo " SAT MASTER Services Started Successfully!"
echo " Backend:  http://127.0.0.1:8000"
echo " Frontend: http://127.0.0.1:3000"
echo "=================================================="
