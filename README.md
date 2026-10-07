# SAT MASTER 🎯

> **Personal AI-Powered Digital SAT Training System**  
> Diagnostic Baseline: 700 (Math: ~360, Reading & Writing: ~340) ➔ **Target: 1400+** over a 4-month structured trajectory.

---

## 1. What is SAT MASTER?

**SAT MASTER** is a Telegram Mini App engineered for Digital SAT preparation. Unlike generic test platforms that follow a simple `Question -> Answer -> Next` cycle, SAT MASTER is built around an active **Remediation Loop**:

```
Question ➔ Answer ➔ Analyze ➔ Why Wrong? ➔ Teach ➔ Practice Similar Skill ➔ Retest Later
```

Every mistake serves as an actionable pedagogical signal to eliminate concept gaps, careless misreads, and timing bottlenecks.

---

## 2. Tech Stack

### Frontend
- **Framework**: Next.js 14+ (App Router), React 18, TypeScript (Strict Mode)
- **Styling**: Tailwind CSS with dynamic Telegram theme variable mapping (`@telegram-apps/sdk` variables)
- **State & Data Fetching**: TanStack React Query v5
- **Icons & UI**: Lucide React, mobile-first responsive layout (iPhone, Android, Desktop)
- **Telegram WebApp**: Safe wrapper in `frontend/lib/telegram.ts` with browser development fallback

### Backend
- **Framework**: Python 3.14+ / FastAPI (high-performance async ASGI)
- **Validation**: Pydantic v2 & Pydantic Settings
- **Database & ORM**: PostgreSQL 16+ via SQLAlchemy 2.0 (`asyncpg` driver in production, `aiosqlite` for zero-dependency local test suites)
- **Migrations**: Alembic (async execution)
- **Security**: Cryptographic HMAC-SHA256 Telegram `initData` validation service
- **Testing**: Pytest, Pytest-asyncio, HTTPX

---

## 3. Project Structure

```text
satmathbot/
├── backend/
│   ├── alembic/              # Database migration scripts
│   │   └── versions/
│   ├── app/
│   │   ├── api/v1/           # Versioned API routes (/api/v1/)
│   │   │   ├── endpoints/    # Route handlers (health, etc.)
│   │   │   └── router.py
│   │   ├── core/             # Config, security (HMAC-SHA256), logging, database
│   │   ├── models/           # SQLAlchemy 2.0 models (Base, User)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # TelegramAuthService, etc.
│   │   ├── repositories/     # Data access patterns
│   │   ├── content/          # Structured SAT content library
│   │   └── main.py           # FastAPI app instance with CORS & exception handlers
│   ├── tests/                # Async test suite
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/                  # Next.js App Router (layout, page, providers, globals.css)
│   ├── components/           # UI and layout components
│   ├── features/             # Feature-specific modules
│   ├── lib/                  # Centralized API client, Telegram WebApp abstraction
│   ├── types/                # TypeScript type declarations
│   ├── package.json
│   └── .env.example
│
├── docs/                     # Architectural specifications
│   ├── architecture.md
│   ├── roadmap.md
│   ├── database.md
│   ├── question-engine.md
│   └── adaptive-learning.md
│
├── docker-compose.yml        # PostgreSQL container configuration
├── pytest.ini
├── .gitignore
└── README.md
```

---

## 4. Setup & Running Locally

### 4.1. Prerequisites
- **Python 3.11+** (tested and verified on Python 3.14.4)
- **Node.js 20+** & npm 10+
- **Docker** (optional, for local PostgreSQL container)

### 4.2. Database (PostgreSQL via Docker)
If Docker is installed:
```bash
docker compose up -d postgres
```
*Note: If Docker is not available locally, the system runs with local SQLite (`sqlite+aiosqlite:///./sat_master.db`) by default for zero-friction development and automated tests.*

### 4.3. Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
4. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
5. Start the development server:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
   API interactive docs available at: `http://localhost:8000/docs`

### 4.4. Frontend Setup
1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Configure environment:
   ```bash
   cp .env.example .env.local
   ```
3. Start Next.js development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## 5. Running Tests & Quality Checks

### Backend Tests
```bash
# From repository root
backend\.venv\Scripts\pytest -v
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run typecheck
npm run build
```

---

## 6. Telegram Mini App Integration

When accessed within Telegram:
1. Telegram injects `window.Telegram.WebApp`.
2. The frontend extracts `Telegram.WebApp.initData`.
3. The raw string is transmitted to the backend `TelegramAuthService`.
4. The backend validates the HMAC-SHA256 signature using the secret derived from `TELEGRAM_BOT_TOKEN`.
5. Authenticated users are created or retrieved from the database without trusting raw client IDs.
