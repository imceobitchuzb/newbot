# SAT MASTER — Adaptive Learning & Intelligent Remediation Engine

## 1. Core Philosophy: The Remediation Loop

Traditional test-prep platforms operate on a passive `Question ➔ Answer ➔ Next` loop. This fails to address root conceptual deficits, leaving students trapped at plateau scores.

SAT MASTER enforces a rigorous, adaptive **Remediation Loop**:

```
Question
   │
   ▼
Student Answer
   │
   ▼
Detailed Telemetry Analysis (Accuracy, Time-to-solve, Hints used)
   │
   ├───────────────────────────────┬───────────────────────────────┐
[CORRECT]                                                      [INCORRECT]
   │                                                               │
Reinforce Mastery (+Elo)                                  Classify Mistake Signal
   │                                                               │
Advance Difficulty Tier                                   Record in "My Mistakes"
   │                                                               │
Schedule Retention Check (Spaced Repetition)              Trigger Remediation:
                                                          • Why was it wrong?
                                                          • Concept Lesson
                                                          • Practice similar skill
                                                          • Retest later (Interval Spacing)
```

---

## 2. Adaptive Engine Mathematical Formulation

### 2.1. Skill Mastery (Modified Item Response Theory & Elo)
Each student possesses a latent ability parameter $\theta_s \in [0.0, 1.0]$ for each subtopic $k$.
Each question possesses a calibrated difficulty rating $\beta_q \in [0.5, 3.0]$ and estimated solve time $T_q$ (in seconds).

The probability of a student with mastery $\theta_{s,k}$ answering question $q$ correctly is modeled as:

$$P(\text{Correct} \mid \theta_{s,k}, \beta_q) = \frac{1}{1 + e^{-D \cdot (\theta_{s,k} \cdot 3.0 - \beta_q)}}$$

Where scaling constant $D = 1.702$.

### 2.2. Post-Attempt Telemetry Updates
Upon attempt submission with outcome $y \in \{0, 1\}$ and elapsed time $t$:

1. **Accuracy Delta**:
   $$\Delta \theta = K \cdot (y - P(\text{Correct}))$$
   where $K$ adapts dynamically based on attempt count ($K = 0.15$ for early questions, dropping to $K = 0.05$ as confidence narrows).

2. **Pacing Penalty / Bonus**:
   - If answered correctly with $t \le 0.7 \cdot T_q$: Pacing mastery bonus awarded (fluency confirmed).
   - If answered correctly with $t > 1.8 \cdot T_q$: Flagged as "Slow Success" (requires speed drills).
   - If answered incorrectly with $t < 0.3 \cdot T_q$: Flagged as `careless_mistake` or `misread_question` (hasty submission).

---

## 3. Dynamic Question Selection Algorithm

When generating the next practice question via `GET /api/v1/adaptive/next`:

1. **Candidate Pool Partitioning**:
   - 40% Weight: Active Spaced Review questions due for retention test.
   - 35% Weight: Identified Weak Topics ($\theta_{s,k} < 0.60$ or recent mistake frequency $> 30\%$).
   - 25% Weight: Adjacent Progression Topics (advancing towards Hard Tier).
2. **Difficulty Tier Routing**:
   - If recent 3 attempts on topic are correct: Escalate difficulty (`easy` $\rightarrow$ `medium` $\rightarrow$ `hard`).
   - If user misses a `hard` question: Fall back to `medium` question on identical skill.
   - If user misses a `medium` question: Fall back to `easy` foundational drill.
   - If user misses an `easy` question: Interrupt flow with immediate **Concept Lesson** card.

---

## 4. Spaced Review & Retention System

Based on the validated SuperMemo SM-2 spaced repetition paradigm adapted for SAT mastery:

```
Mistake Registered (Day 0)
   ├── Review 1: Day 1 (+24 hours)  ➔ 1 similar target question
   ├── Review 2: Day 3 (+72 hours)  ➔ 1 slightly harder variant
   └── Review 3: Day 7 (+1 week)    ➔ Mixed-practice reappearance
```

Each mistake entry tracks:
- `interval_days`: Current spacing interval.
- `ease_factor`: Multiplier (default 2.5), adjusted by user response speed and retry success.
- `remediation_status`: Transitions from `unresolved` $\rightarrow$ `in_review` $\rightarrow$ `resolved` after 3 consecutive successful spaced reviews.

---

## 5. Mistake Book Taxonomy

Mistakes are diagnosed and logged across 8 distinct categories:

| Error Category | Characteristic Signature | Remediation Action |
|---|---|---|
| `concept_gap` | Fundamental formula or grammar rule unknown. | Redirect to Lesson & foundational drill. |
| `careless_mistake` | Solved rapidly, missed negative sign or arithmetic step. | Prompt self-check before answer confirmation. |
| `misread_question` | Solved for $x$ when question asked for $3x + 1$. | Highlight question prompt keywords. |
| `time_pressure` | Answered in last 10 seconds or timed out. | Timed pacing drill with shortcut focus. |
| `calculation_error` | Arithmetic error in non-calculator style step. | Recommend Desmos scratch verification. |
| `vocabulary_gap` | Passage comprehension failed due to unfamiliar academic word. | Add word to Personal SAT Lexicon. |
| `grammar_gap` | Misidentified clause boundary or modifier attachment. | Show punctuation & syntax breakdown. |
| `strategy_error` | Attempted brute-force algebra instead of Desmos shortcut. | Present Desmos Lab interactive trick. |

---

## 6. Score Estimator Service (`ScoreEstimator`)

To protect student motivation and ensure scientific accuracy, the platform **never presents illusory single-point guarantees** (e.g. "You will score 1380"). Instead, it presents **Calibrated Score Bands**:

- **Math Estimate Band**: e.g., $580 \pm 30$ ($[550, 610]$)
- **Reading & Writing Estimate Band**: e.g., $540 \pm 40$ ($[500, 580]$)
- **Composite Digital SAT Band**: e.g., $1120 \pm 50$ ($[1070, 1170]$)

The band width narrows as:
- Total questions solved increases ($N > 200$).
- Recent Full SAT Module simulations are logged.
- Consistency across all 8 SAT domains stabilizes.

---

## 7. Phase 5 Diagnostic Calibration Engine

### 7.1. Diagnostic Structure & Controlled Selection
Unlike adaptive practice (Phase 8), the baseline Diagnostic is a **controlled, non-adaptive calibration instrument**:
- **Math Module**: Exactly 20 questions (5 Algebra, 5 Advanced Math, 5 Problem-Solving & Data Analysis, 5 Geometry & Trigonometry).
- **Reading & Writing Module**: Exactly 20 questions (5 Information & Ideas, 5 Craft & Structure, 5 Expression of Ideas, 5 Standard English Conventions).
- **Difficulty Balance**: Targeted at ~25% Easy (5 questions), ~50% Medium (10 questions), ~25% Hard (5 questions) per section.
- **Uniqueness & Anti-Duplication**: Exactly 40 unique question IDs assigned to the session. Duplicate questions within a session are strictly prevented.

### 7.2. Deterministic Scoring Algorithm
For section raw correct count $C \in [0, 20]$ with ratio $r = C / 20.0$:
- **Midpoint Scaled Score**:
  $$S_{mid} = 200 + \text{round}\left(\frac{600 \cdot r}{10}\right) \cdot 10$$
- **Score Range**:
  $$S_{low} = \max(200, S_{mid} - 30), \quad S_{high} = \min(800, S_{mid} + 30)$$
  - Boundary: $C = 0 \implies [200, 240]$
  - Boundary: $C = 10 (50\%) \implies [470, 530]$
  - Boundary: $C = 20 (100\%) \implies [760, 800]$
- **Total Estimated Range**:
  $$Total_{low} = Math_{low} + RW_{low}, \quad Total_{high} = Math_{high} + RW_{high}$$

### 7.3. Weak & Strong Domain Classification
Configurable accuracy thresholds classify each of the 8 SAT domains:
- **`WEAK`**: Accuracy $< 60\%$ (Flagged as priority focus areas for practice and mistake review)
- **`MODERATE`**: $60\% \le \text{Accuracy} < 75\%$
- **`STRONG`**: Accuracy $\ge 75\%$ (Foundational mastery confirmed)

### 7.4. UserProfile Synchronization
Upon diagnostic completion:
- `UserProfile.diagnostic_status` transitions to `completed`.
- `UserProfile.math_estimate` and `UserProfile.rw_estimate` are populated with section midpoints.
- `UserProfile.target_score` (default 1400) is **strictly preserved** (never overwritten by baseline results).

### 7.5. Diagnostic vs. Official SAT Score Disclaimer
The calculated range is an algorithmic **diagnostic approximation** designed for EdTech study pacing and gap identification. It is explicitly labeled as an estimate and does not represent official College Board psychometric scaling.

---

## 8. Phase 7 Mistake Book & Deliberate Remediation Engine

### 8.1. Automatic Capture & Idempotency
- **Triggers**:
  - `MathPracticeService.submit_answer`: Any incorrect answer immediately records or updates an entry in `mistake_book_entries`.
  - `DiagnosticService.submit_answer`: When the final diagnostic module completes, all incorrect diagnostic questions are automatically captured.
- **Uniqueness**: Enforced by composite database constraint `UNIQUE(user_id, question_id)`. Subsequent errors on the same question update telemetry (`incorrect_retry_count`, timestamps) without creating duplicate records.

### 8.2. Spaced Repetition Schedule
Reviews are scheduled deterministically using exponential interval spacing based on review progression:
- Review 0 $\rightarrow$ +1 day (24 hours)
- Review 1 $\rightarrow$ +3 days (72 hours)
- Review 2 $\rightarrow$ +7 days (1 week)
- Review 3 $\rightarrow$ +14 days (2 weeks)
- Review 4+ $\rightarrow$ +30 days (1 month)

### 8.3. Strict Mastery Criteria & Regression Logic
- **Mastery Rule**: An entry transitions to `status = 'MASTERED'` **only** when:
  1. At least 2 retries have been submitted (`total_retries >= 2`).
  2. The last 2 consecutive attempts on the question were correct.
- **Regression Logic**: If a user later answers a `MASTERED` question incorrectly during subsequent practice drills or reviews, it immediately regresses to `status = 'ACTIVE'` with review due interval reset to +1 day.

### 8.4. Immutability of Attempt History
- Retries create **new** `QuestionAttempt` rows linked to the user and question.
- Historical attempts are strictly preserved and never mutated or overwritten.


