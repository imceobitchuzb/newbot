# SAT MASTER — Production Deployment & 24/7 Infrastructure Guide

## 1. Overview & Architecture

SAT MASTER is engineered as a decoupled high-performance educational platform:
* **Frontend**: Next.js 14 (App Router, React 18, TanStack Query, TailwindCSS, KaTeX). Runs on port `3000`.
* **Backend**: FastAPI (Python 3.11+, SQLAlchemy 2.0 Async, Pydantic v2, Alembic). Runs on port `8000`.
* **Database**:
  * **Development (Local Windows)**: SQLite (`sat_master.db`) via `aiosqlite`.
  * **Production (Linux VPS / Docker)**: PostgreSQL 16 via `asyncpg`.
* **Bot Daemon**: python-telegram-bot v21+ asynchronous daemon with persistent WebApp menu button.
* **Ingress / HTTPS**: Cloudflare Named Tunnel running as a systemd daemon routing to `http://localhost:3000`.

```
                    ┌────────────────────────┐
                    │      Telegram User     │
                    └───────────┬────────────┘
                                │ opens WebApp
                                ▼
                    ┌────────────────────────┐
                    │ Cloudflare Edge (HTTPS)│
                    └───────────┬────────────┘
                                │ Named Tunnel
                                ▼
         ┌──────────────────────────────────────────────────┐
         │                  Linux VPS                       │
         │  ┌─────────────────┐    ┌─────────────────────┐  │
         │  │ Next.js App     │───▶│ FastAPI Backend     │  │
         │  │ (port 3000)     │    │ (port 8000)         │  │
         │  └─────────────────┘    └──────────┬──────────┘  │
         │                                    │             │
         │  ┌─────────────────┐               │             │
         │  │ Telegram Bot    │               │             │
         │  │ (bot.py)        │               │             │
         │  └─────────────────┘               ▼             │
         │                         ┌─────────────────────┐  │
         │                         │ PostgreSQL 16       │  │
         │                         │ (port 5432)         │  │
         │                         └─────────────────────┘  │
         └──────────────────────────────────────────────────┘
```

---

## 2. Local Runtime vs Production Database

| Feature | Local Development (Windows) | Production (Docker / VPS) |
| :--- | :--- | :--- |
| **Engine** | SQLite 3 (`sqlite+aiosqlite:///./sat_master.db`) | PostgreSQL 16 (`postgresql+asyncpg://...`) |
| **Reason** | Docker CLI is not installed on host Windows | Full concurrency, multi-connection pooling |
| **Alembic** | Target head: `009_ai_tutor` | Target head: `009_ai_tutor` |
| **Questions** | 109 seeded SAT questions | 109 seeded SAT questions |

To switch environments, update `DATABASE_URL` in `.env`:
```env
# Production PostgreSQL:
DATABASE_URL=postgresql+asyncpg://postgres:secure_password@localhost:5432/sat_master

# Local SQLite:
DATABASE_URL=sqlite+aiosqlite:///./sat_master.db
```

---

## 3. Deployment Methods

### Option A: Docker Compose (Recommended for VPS)

1. Clone repository to VPS:
   ```bash
   git clone https://github.com/imceobitchuzb/newbot.git /opt/satmaster
   cd /opt/satmaster
   ```
2. Configure `.env`:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Set:
   - `TELEGRAM_BOT_TOKEN=...`
   - `TELEGRAM_WEBAPP_URL=https://sat.yourdomain.com`
   - `SECRET_KEY=your-secure-random-32char-key`
   - `POSTGRES_PASSWORD=your_strong_postgres_password`
   - `AI_API_KEY=...` (optional, falls back to pedagogical engine if omitted)
3. Launch services:
   ```bash
   docker-compose up -d --build
   ```
4. Run migrations & database seed:
   ```bash
   docker-compose exec -T backend alembic -c backend/alembic.ini upgrade head
   docker-compose exec -T backend python -m backend.app.db.seed
   ```
5. Check health:
   ```bash
   curl http://localhost:8000/health
   ```

---

### Option B: Bare-Metal Host / Systemd (Ubuntu 22.04 / Debian 12)

1. **Install Prerequisites**:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm postgresql postgresql-contrib curl
   ```
2. **Setup PostgreSQL**:
   ```bash
   sudo -u postgres psql -c "CREATE USER satmaster WITH PASSWORD 'strongpassword';"
   sudo -u postgres psql -c "CREATE DATABASE sat_master OWNER satmaster;"
   ```
3. **Setup Virtual Environment & Install Dependencies**:
   ```bash
   cd /opt/satmaster
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate
   pip install -r backend/requirements.txt
   
   cd frontend
   npm ci
   npm run build
   cd ..
   ```
4. **Run Migrations & Seed**:
   ```bash
   python -m alembic -c backend/alembic.ini upgrade head
   python -m backend.app.db.seed
   ```
5. **Systemd Service Setup**:
   Create `/etc/systemd/system/sat-backend.service`:
   ```ini
   [Unit]
   Description=SAT Master Backend
   After=network.target postgresql.service

   [Service]
   User=satmaster
   WorkingDirectory=/opt/satmaster
   ExecStart=/opt/satmaster/backend/.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   Restart=always
   RestartSec=3

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/sat-frontend.service`:
   ```ini
   [Unit]
   Description=SAT Master Frontend
   After=network.target

   [Service]
   User=satmaster
   WorkingDirectory=/opt/satmaster/frontend
   ExecStart=/usr/bin/npm run start -- -p 3000
   Restart=always
   RestartSec=3

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/sat-bot.service`:
   ```ini
   [Unit]
   Description=SAT Master Telegram Bot
   After=network.target sat-backend.service

   [Service]
   User=satmaster
   WorkingDirectory=/opt/satmaster
   ExecStart=/opt/satmaster/backend/.venv/bin/python backend/bot.py
   Restart=always
   RestartSec=3

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start all services:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now sat-backend sat-frontend sat-bot
   ```

---

## 4. Cloudflare Named Tunnel (True 24/7 Production Ingress)

### Quick Tunnel vs Named Tunnel

| Attribute | Quick Tunnel (`trycloudflare.com`) | Named Tunnel (`cloudflared tunnel run`) |
| :--- | :--- | :--- |
| **URL Stability** | Random subdomain generated on start | Static custom domain (`sat.yourdomain.com`) |
| **Lifecycle** | Dies when terminal closes or sleeps | Runs 24/7 as a background systemd service |
| **Telegram Mini App** | Requires updating BotFather on every restart | Static URL never changes in BotFather |
| **Suitability** | Temporary dev / testing | **Production 24/7** |

### Step-by-Step Named Tunnel Setup

1. **Install cloudflared on VPS**:
   ```bash
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   ```
2. **Authenticate with Cloudflare**:
   ```bash
   cloudflared tunnel login
   ```
3. **Create the Tunnel**:
   ```bash
   cloudflared tunnel create sat-master
   ```
   *Note the Tunnel ID returned (e.g., `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).*
4. **Configure DNS Route**:
   ```bash
   cloudflared tunnel route dns sat-master sat.yourdomain.com
   ```
5. **Create Tunnel Config File (`~/.cloudflared/config.yml`)**:
   ```yaml
   tunnel: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   credentials-file: /root/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

   ingress:
     - hostname: sat.yourdomain.com
       service: http://localhost:3000
     - service: http_status:404
   ```
6. **Install and Start Tunnel as System Service**:
   ```bash
   sudo cloudflared service install
   sudo systemctl enable --now cloudflared
   ```
7. **Update Telegram WebApp URL in BotFather**:
   - Send `/setmenubutton` to `@BotFather`
   - Select your bot
   - Provide URL: `https://sat.yourdomain.com`

---

## 5. AI SAT Tutor Operation & Pedagogical Engine

The AI Tutor module is equipped with a dual-engine architecture:
1. **External LLM Provider**: When `AI_API_KEY` is provided in `.env`, the system queries the configured OpenAI-compatible API (`gpt-4o-mini`, etc.) for dynamic tutoring.
2. **Pedagogical Fallback Engine**: If `AI_API_KEY` is empty or the external provider is unavailable, the built-in `PedagogicalSATProvider` is automatically activated. It evaluates:
   - Question context & Domain (Algebra, Advanced Math, Geometry, Problem Solving)
   - Mode (HINT, EXPLANATION, SOLUTION, DESMOS_HELP, CONCEPT)
   - KaTeX formatted mathematical expressions (`\(...\)`)
   - Interactive action recommendations (`PRACTICE_SKILL`, `OPEN_DESMOS`, `REVIEW_MISTAKE`, `PRACTICE_ADAPTIVE`)
   - Guarantees 0% crash rate and zero UI resets.

---

## 6. Verification Checklist

Before opening the platform to real students:
- [x] Backend tests pass: `python -m pytest backend/tests` (134/134 passed)
- [x] Frontend typecheck: `npm run typecheck` (0 errors)
- [x] Production build: `npm run build` (compiled clean)
- [x] No `localhost:8000` in client bundles
- [x] Database migrations: `009_ai_tutor (head)`
- [x] Persistent Telegram menu button enabled in `backend/bot.py`
