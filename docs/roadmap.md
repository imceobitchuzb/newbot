# SAT MASTER — Implementation Roadmap & Student Curriculum

## 1. Student Target Trajectory: 700 ➔ 1400+

- **Initial Diagnostic Baseline**: ~700 SAT
  - Math: ~360 (Algebra gaps, arithmetic hesitations, no Desmos fluency)
  - Reading & Writing: ~340 (Vocabulary limitations, punctuation/boundary rules missing, reading pacing)
- **Target Score**: **1400+** (Math: 720+, Reading & Writing: 680+)
- **Preparation Horizon**: 4 Months (~16 Weeks)
- **Pedagogical Axiom**: 1400+ is a rigorous **TARGET**, never an unearned guarantee. Progress requires disciplined remediation of each detected error signal.

---

## 2. 4-Month Pedagogical Curriculum Plan

```
┌────────────────────────────────────────────────────────────────────────┐
│                          4-MONTH TIMELINE                              │
├─────────────┬─────────────────┬───────────────────┬────────────────────┤
│   MONTH 1   │     MONTH 2     │      MONTH 3      │      MONTH 4       │
│ Foundation  │ Skill Building  │   Advanced SAT    │  Exam Simulation   │
├─────────────┼─────────────────┼───────────────────┼────────────────────┤
│ Linear Eq.  │ Quadratics/Poly │ High-difficulty Q │ Full SAT Tests     │
│ Basic Conv. │ Transitions     │ Mixed Domains     │ Timing Strategy    │
│ Vocab core  │ Inference       │ Speed Drills      │ Desmos Automation  │
│ Desmos 101  │ Evidence Qs     │ Error Elimination │ Final Polish       │
└─────────────┴─────────────────┴───────────────────┴────────────────────┘
```

### Month 1: Foundation & Diagnostic Calibration
- **Objectives**: Eradicate fundamental errors, establish daily streak habit, achieve Desmos baseline competency.
- **Math Focus**:
  - Linear equations with one and two variables.
  - Linear function graphs ($y = mx + b$, interpreting slope and intercepts).
  - Systems of linear equations (substitution, elimination, Desmos graphing).
  - Inequalities and number line interpretations.
  - Fractions, ratios, rates, and unit conversions.
- **Reading & Writing Focus**:
  - Standard English Conventions: Boundaries (periods, semicolons, comma splices).
  - Subject-verb agreement and pronoun-antecedent agreement.
  - High-frequency SAT Academic Vocabulary (Tier 2 words in context).
  - Core paragraph structure: Identifying the central claim.
- **Desmos Fundamentals**:
  - Finding roots/zeros/intersections via point inspection.
  - Using sliders for parameter exploration ($y = ax^2 + bx + c$).
- **Weekly Target**: 250 questions solved, 100% review of logged mistakes.

### Month 2: Skill Building & Strategy
- **Objectives**: Master multi-step problem solving, understand College Board question traps, develop active reading skills.
- **Math Focus**:
  - Quadratics (factoring, quadratic formula, vertex form, discriminant $\Delta$).
  - Nonlinear functions and exponential growth/decay ($y = a(1 \pm r)^t$).
  - Percentages, percent increase/decrease, margin of error, data interpretation.
  - Angles, triangles, Pythagorean theorem, basic circle equations.
- **Reading & Writing Focus**:
  - Rhetorical transitions (contrast, addition, cause-and-effect).
  - Command of Evidence (textual and quantitative/tables).
  - Inference questions and logical conclusions without speculation.
  - Modifier placement and parallel structure.
- **Desmos Strategies**:
  - Solving nonlinear systems via graphical intersections.
  - Linear regression (`y1 ~ m x1 + b`) for best-fit problems.
- **Weekly Target**: 300 questions, 2 targeted topic mini-tests per week.

### Month 3: Advanced SAT & Timing Drills
- **Objectives**: Eliminate careless errors under time pressure; elevate accuracy to 85%+ on Hard/Adaptive Module 2 questions.
- **Math Focus**:
  - Advanced polynomials, remainder theorem, synthetic division.
  - Circle theorems, trigonometry ratios ($\sin, \cos, \tan$, complementary angles).
  - Complex statistical concepts: standard deviation, random sampling, confidence intervals.
  - Mixed domain problem sets.
- **Reading & Writing Focus**:
  - Dual text comparisons and author perspectives.
  - Nuanced vocabulary in context (secondary definitions).
  - Dense historical/scientific passages analysis.
  - Rhetorical synthesis (note-taking to specific prompt goal).
- **Weekly Target**: 350 questions, 4 timed sections per week, error analysis within 12 hours.

### Month 4: Exam Simulation & Peak Readiness
- **Objectives**: Perfect pacing, eliminate mental fatigue, simulate exact Digital SAT conditions.
- **Focus**:
  - Complete Digital SAT simulations (Modules 1 & 2 Math + Modules 1 & 2 R&W with countdown timer).
  - Module 2 hard adaptive routing readiness.
  - Desmos keyboard shortcuts and instant visual confirmation.
  - Strategic flagging, educated elimination, and time-banking.
- **Weekly Target**: 2 Full SAT exams per week + targeted Mistake Book remediation.

---

## 3. Engineering Phase Breakdown

| Phase | Title | Scope & Deliverables | Verification Gateway |
|:---:|---|---|---|
| **0** | **Audit** | Inspection of workspace, tooling verification, baseline architecture documents. | Clean repository audit report and approval to proceed. |
| **1** | **Foundation** | Backend FastAPI skeleton, Next.js client initialization, Docker/environment configurations, unified error handling, healthcheck endpoints. | `pytest` passes, `npm run build` succeeds, `/api/health` returns 200 OK. |
| **2** | **Telegram, User & DB** | PostgreSQL models (Alembic), Telegram HMAC-SHA256 Auth Service, user creation, mock dev auth. | Auth tests pass with valid and tampered initData. User persistent creation verified. |
| **3** | **Dashboard** | Mobile-first Dashboard UI with real-time stats, current estimate display, daily study plan card, streak counter. | Responsive UI rendering cleanly across simulated iPhone/Android viewports. |
| **4** | **Question Engine** | Relational question store, tags, choices, filtering, session state, submission verification API. | CRUD tests for questions; randomized & targeted question retrieval passing. |
| **5** | **Math Module** | Math question repository (Algebra, Advanced Math, Problem Solving, Geometry), KaTeX rendering. | 100+ vetted math questions seeded with LaTeX formulas and step explanations. |
| **6** | **Reading & Writing Module** | R&W question engine, passage display, highlight support, split-screen mobile viewer. | Passage + questions UI tested for long-read comfort and question transitions. |
| **7** | **Mistake Book & Spaced Review** | Mistake tracking by categorization (`concept_gap`, `careless_mistake`, etc.), automated retry scheduling. | Incorrect answers automatically populate Mistake Book; retries update mistake status. |
| **8** | **Adaptive Practice Engine** | IRT/Elo difficulty scaling, response-time weighting, dynamic weak-topic prioritization. | Algorithmic test suite verifies difficulty increases on correct answers and scales down on errors. |
| **9** | **Desmos Lab & Shortcuts** | Desmos Graphing Calculator integration, 15+ interactive shortcut guides, visual graphing questions. | Embedded calculator loads smoothly; interactive slider exercises functional. |
| **10** | **AI SAT Tutor** | Backend proxy to LLM with 5 distinct prompt modes (Hint, Explain, Solve, Another Method, SAT Trick). | Socratic behavior verified: Hint mode does not leak final answers; fallback triggers on network error. |
| **11** | **Full SAT Exam Simulation** | Multi-module timed exam engine (Module 1 -> Module 2 adaptive routing), score estimation report. | Timed test runs without client desync; results generate score range. |
| **12** | **Progress & Gamification** | Radar mastery charts, score projection over time, XP rewards, streaks, 10+ achievements. | User progress graphs update dynamically; achievement badges unlock upon triggers. |
| **13** | **Competitive Mode (Duels)** | 5-10 question asynchronous/simulated duel engine, fast-answer multipliers, leaderboard. | Multiplayer state machine runs end-to-end; leaderboard computes ranks. |
| **14** | **Hardening & Performance** | End-to-end testing, rate limiting, SQL index optimization, bundle optimization. | 95+ Lighthouse mobile score, zero unhandled exceptions under concurrency. |
| **15** | **Production Deployment** | Production Dockerfiles, CI/CD pipeline, webhook integration, Telegram Bot registration. | Live Telegram Mini App accessible and responsive in official Telegram clients. |
