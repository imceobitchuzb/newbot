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

## 6. Telegram Mini App Authentication & User System

### 6.1. Production Telegram Flow
1. When opened inside Telegram (iOS, Android, or Desktop), Telegram injects `window.Telegram.WebApp`.
2. The frontend extracts `Telegram.WebApp.initData` (raw query string).
3. The frontend calls `POST /api/v1/auth/telegram` with `{"init_data": "<raw_init_data>"}`.
4. The backend `TelegramAuthService` cryptographically validates:
   - Secret key derived via `HMAC_SHA256("WebAppData", TELEGRAM_BOT_TOKEN)`.
   - Data-check string assembled from sorted parameters excluding `hash`.
   - Signature match via constant-time comparison.
   - `auth_date` freshness check (must be within 24 hours).
5. The backend `UserService` retrieves or creates the student account and linked `UserProfile` (with `diagnostic_status = "not_started"`).
6. The backend issues a short-lived signed JWT access token (`HS256`).
7. The frontend uses `Authorization: Bearer <token>` on all future requests (such as `GET /api/v1/users/me`).

### 6.2. Desktop Browser Development Mode
To develop and test outside of Telegram:
- Start backend and frontend servers as usual.
- Navigate to `http://localhost:3000`.
- The app detects that `Telegram.WebApp` is not active and renders **Development Browser Mode**.
- This allows full local UI and API verification without launching the Telegram client.
- *Note: `POST /api/v1/auth/dev` is strictly disabled when `APP_ENV=production`.*

---

## 7. Question Engine & Interactive Practice Demo

### 7.1. Question Engine Features
- **Extensible Schema**: `passages`, `questions`, `question_options`, and `question_attempts` backed by PostgreSQL / SQLite.
- **Strict Answer Protection**: Answer keys, correct flags, and full explanations are never leaked across `GET` queries. They are returned only after verified submission (`POST /api/v1/questions/{id}/attempt`).
- **Math Notation**: Integrated KaTeX for LaTeX equations (inline `$x^2$` and block `$$\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$`).
- **Seed Content**: 24 original SAT practice questions across Math (Algebra, Advanced Math, Problem-Solving, Geometry) and Reading & Writing (Information & Ideas, Craft & Structure, Expression of Ideas, Standard English Conventions).

### 7.2. Interactive Demo Route
Visit `http://localhost:3000/practice/demo` to try the Question Engine directly:
- Filter questions by Subject, Domain, and Difficulty.
- Step through interactive SAT questions with instant submission, correctness feedback, explanations, and SAT shortcuts.

---

## 8. Real Diagnostic Module

### 8.1. Diagnostic Structure & Calibration
- **Length**: Exactly 40 questions (Module 1: 20 Math questions; Module 2: 20 Reading & Writing questions).
- **Balanced Coverage**: 5 questions from each of the 8 Digital SAT domains, with controlled difficulty mix (~25% Easy, ~50% Medium, ~25% Hard).
- **Zero In-Test Leaks**: Answers, hints, and explanations remain hidden throughout the assessment until completion.
- **Estimated Score Range**: Deterministic calculation mapping section performance to SAT ranges ($200 - 800$ per section, $400 - 1600$ total).
- **Weak Domain Diagnosis**: Classifies each domain as `WEAK` ($<60\%$), `MODERATE`, or `STRONG` ($\ge 75\%$) to anchor personalized study plans.
- **User Profile Sync**: Marks `diagnostic_status = "completed"` and sets baseline estimates while preserving the student's target score.

### 8.2. Diagnostic API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/diagnostics` | Start a new diagnostic test or resume active session |
| `GET` | `/api/v1/diagnostics/current` | Get current active diagnostic progress and next question |
| `POST` | `/api/v1/diagnostics/{id}/questions/{qid}/answer` | Submit an answer to an assigned diagnostic question |
| `GET` | `/api/v1/diagnostics/{id}/result` | Retrieve completed diagnostic report and score ranges |
| `GET` | `/api/v1/diagnostics/latest/result` | Retrieve most recent completed diagnostic result |

### 8.3. Frontend Routes
- `/diagnostic`: Comprehensive intro screen with Start/Resume CTA and interactive question runner.
- `/diagnostic/result`: Calibrated score report with total & section ranges, strong areas, and weak domain growth priorities.

---

## 9. Real SAT Math Learning Module

### 9.1. Math Content Architecture
- **84 Original Math Questions**: Spanning all 4 College Board domains (Algebra, Advanced Math, Problem-Solving & Data Analysis, Geometry & Trigonometry) across 20 distinct skills.
- **Customizable Practice Drills**: Filter practice sessions by specific domain, target skill, and question count (5, 10, or 20 questions).
- **Domain & Skill Mastery Telemetry**: Real database-computed mastery analytics per domain and skill.

---

## 10. Real Mistake Book & Error Remediation (Phase 7)

### 10.1. Mistake Book Features
- **Automatic Capture**: Automatically logs incorrect questions from both Math Practice sessions and completed Diagnostics.
- **Strict Anti-Duplication**: Exactly 1 active record per `(user_id, question_id)` with cumulative retry metrics.
- **Spaced Review Schedule**: Spaced repetition interval progression: +1d $\rightarrow$ +3d $\rightarrow$ +7d $\rightarrow$ +14d $\rightarrow$ +30d.
- **Strict Mastery Criteria**: Demands at least 2 retries and 2 consecutive correct submissions to promote to `MASTERED`.
- **Regression Logic**: An incorrect answer on a previously mastered question immediately regresses it to `ACTIVE`.
- **Attempt History Preservation**: Every retry creates a new `QuestionAttempt` record without mutating prior attempts.
- **Deterministic Priority Queue**: `GET /api/v1/mistakes/next` prioritizes overdue reviews first, then active errors.

### 10.2. Mistake Book Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/mistakes` | List user's mistakes with subject, status, type, and domain filters |
| `GET` | `/api/v1/mistakes/next` | Fetch highest priority mistake due for remediation |
| `GET` | `/api/v1/mistakes/analytics` | Summary error telemetry (active, due, mastered, mastery rate %) |
| `GET` | `/api/v1/mistakes/{id}` | Get single mistake book entry with question details |
| `POST` | `/api/v1/mistakes/{id}/review` | Record spaced repetition review progression |
| `PATCH` | `/api/v1/mistakes/{id}/classify` | Update error classification (Concept Gap, Careless Error, etc.) |
| `POST` | `/api/v1/mistakes/{id}/retry` | Submit retry attempt and evaluate mastery progression |

### 10.3. Frontend Views
- `/mistakes`: Overview dashboard with error telemetry chips, priority remediation banner, filter tabs, and KaTeX math snippets.
- `/mistakes/[id]`: Interactive remediation view with self-diagnosis classification pills, multiple-choice retry runner, instant evaluation, explanations, hints, and SAT shortcuts.



