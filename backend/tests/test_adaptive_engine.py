from datetime import datetime, timedelta, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.adaptive import (
    AdaptivePracticeQuestion,
    AdaptivePracticeSession,
    AdaptiveProfile,
)
from backend.app.models.diagnostic import DiagnosticResult, DiagnosticSession
from backend.app.models.enums import (
    AdaptiveSessionStatus,
    AdaptiveSkillStatus,
    Difficulty,
    DomainClassification,
    MathDomain,
    MistakeStatus,
    RecommendationType,
    Subject,
)
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.models.question import Question, QuestionAttempt
from backend.app.models.user import User
from backend.app.seed.questions import seed_questions
from backend.app.services.adaptive_engine_service import AdaptiveEngineService
from backend.app.services.adaptive_session_service import AdaptiveSessionService


async def create_test_user():
    """Helper to create a test user with unique credentials."""
    async with async_session_factory() as session:
        uid = int(uuid.uuid4().int % 1000000000)
        user = User(
            telegram_id=uid,
            username=f"user_{uid}",
            first_name="AdaptiveTester",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# ==================== 1. MASTERY & CONFIDENCE UNIT TESTS ====================

def test_confidence_formula_bounds():
    """Verify confidence formula: min(attempts / 10.0, 1.0)."""
    assert AdaptiveEngineService.calculate_confidence(0) == 0.0
    assert AdaptiveEngineService.calculate_confidence(1) == 0.1
    assert AdaptiveEngineService.calculate_confidence(5) == 0.5
    assert AdaptiveEngineService.calculate_confidence(10) == 1.0
    assert AdaptiveEngineService.calculate_confidence(25) == 1.0


def test_recent_accuracy_calculation():
    """Verify rolling accuracy on last 10 attempts sorted newest first."""
    assert AdaptiveEngineService.calculate_recent_accuracy([]) == 0.0
    # 3 attempts: 2 correct, 1 wrong -> 2/3 = 0.6667
    assert AdaptiveEngineService.calculate_recent_accuracy([True, False, True]) == 0.6667
    # 12 attempts: first 10 are taken
    outcomes = [True] * 8 + [False] * 2 + [False, False]
    assert AdaptiveEngineService.calculate_recent_accuracy(outcomes) == 0.80


def test_mastery_score_and_low_confidence_capping():
    """1 correct out of 1 should NOT give 100% mastery because confidence is 0.1."""
    m_1_of_1 = AdaptiveEngineService.calculate_mastery_score(
        overall_accuracy=1.0,
        recent_accuracy=1.0,
        confidence=0.1,
    )
    # 0.1 * 1.0 = 0.10
    assert m_1_of_1 == 0.10

    # 10 of 10 correct: confidence is 1.0 -> 1.0
    m_10_of_10 = AdaptiveEngineService.calculate_mastery_score(
        overall_accuracy=1.0,
        recent_accuracy=1.0,
        confidence=1.0,
    )
    assert m_10_of_10 == 1.0


def test_mastery_penalized_by_active_mistake():
    """Active mistake applies 0.85 factor to mastery score."""
    m_clean = AdaptiveEngineService.calculate_mastery_score(
        overall_accuracy=0.8,
        recent_accuracy=0.8,
        confidence=1.0,
        has_active_mistake=False,
    )
    m_mistake = AdaptiveEngineService.calculate_mastery_score(
        overall_accuracy=0.8,
        recent_accuracy=0.8,
        confidence=1.0,
        has_active_mistake=True,
    )
    assert m_clean == 0.80
    assert m_mistake == round(0.80 * 0.85, 4)  # 0.68
    assert m_mistake < m_clean


def test_mastered_status_threshold_strictness():
    """Mastered status requires attempts >= 10, mastery >= 0.90, recent_accuracy >= 0.85."""
    # High mastery with only 2 attempts -> capped at STRONG
    status_few_attempts = AdaptiveEngineService.determine_skill_status(
        attempts=2,
        mastery_score=0.95,
        recent_accuracy=1.0,
    )
    assert status_few_attempts == AdaptiveSkillStatus.STRONG.value

    # High mastery with 10 attempts and high recent accuracy -> MASTERED
    status_mastered = AdaptiveEngineService.determine_skill_status(
        attempts=12,
        mastery_score=0.92,
        recent_accuracy=0.90,
    )
    assert status_mastered == AdaptiveSkillStatus.MASTERED.value

    # High mastery with 10 attempts but recent accuracy dipped below 0.85 -> capped at STRONG
    status_dipped = AdaptiveEngineService.determine_skill_status(
        attempts=12,
        mastery_score=0.91,
        recent_accuracy=0.80,
    )
    assert status_dipped == AdaptiveSkillStatus.STRONG.value


# ==================== 2. DIFFICULTY TRANSITIONS ====================

def test_difficulty_transition_step_up():
    """Rolling window >= 80% increases difficulty by single step."""
    # EASY -> MEDIUM
    next_d1 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.EASY.value,
        [True, True, True, True, False],  # 4/5 = 80%
    )
    assert next_d1 == Difficulty.MEDIUM.value

    # MEDIUM -> HARD
    next_d2 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.MEDIUM.value,
        [True, True, True, True, True],  # 5/5 = 100%
    )
    assert next_d2 == Difficulty.HARD.value

    # HARD -> HARD (capped)
    next_d3 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.HARD.value,
        [True, True, True, True, True],
    )
    assert next_d3 == Difficulty.HARD.value


def test_difficulty_transition_step_down():
    """Rolling window <= 40% decreases difficulty by single step."""
    # HARD -> MEDIUM
    next_d1 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.HARD.value,
        [False, False, False, True, False],  # 1/5 = 20%
    )
    assert next_d1 == Difficulty.MEDIUM.value

    # MEDIUM -> EASY
    next_d2 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.MEDIUM.value,
        [False, False, True, False, False],
    )
    assert next_d2 == Difficulty.EASY.value

    # EASY -> EASY (floor)
    next_d3 = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.EASY.value,
        [False, False, False, False, False],
    )
    assert next_d3 == Difficulty.EASY.value


def test_difficulty_transition_maintenance():
    """Rolling window between 41% and 79% maintains current difficulty."""
    # 3/5 = 60%
    next_d = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.MEDIUM.value,
        [True, False, True, False, True],
    )
    assert next_d == Difficulty.MEDIUM.value


def test_no_double_step_difficulty_jumps():
    """Strictly guarantees no jumping EASY -> HARD or HARD -> EASY in single step."""
    # 100% on EASY should only reach MEDIUM, NEVER HARD
    d_step = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.EASY.value,
        [True] * 5,
    )
    assert d_step == Difficulty.MEDIUM.value
    assert d_step != Difficulty.HARD.value

    # 0% on HARD should only reach MEDIUM, NEVER EASY
    d_step_down = AdaptiveEngineService.calculate_next_difficulty(
        Difficulty.HARD.value,
        [False] * 5,
    )
    assert d_step_down == Difficulty.MEDIUM.value
    assert d_step_down != Difficulty.EASY.value


# ==================== 3. RECOMMENDATION ENGINE TESTS ====================

@pytest.mark.asyncio
async def test_recommendation_overdue_mistake_highest_priority():
    """Overdue mistake in Mistake Book takes precedence over all skills."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().first()

        # Create an overdue mistake entry
        entry = MistakeBookEntry(
            user_id=user.id,
            question_id=q.id,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
            status=MistakeStatus.ACTIVE.value,
            next_review_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        session.add(entry)
        await session.commit()

        rec_type, domain, skill, diff, reason, mistake_qid = (
            await AdaptiveEngineService.determine_next_recommendation(
                db=session,
                user_id=user.id,
                subject=Subject.MATH.value,
            )
        )
        assert rec_type == RecommendationType.MISTAKE_REVIEW.value
        assert skill == q.skill
        assert mistake_qid == q.id
        assert "overdue" in reason.lower()


@pytest.mark.asyncio
async def test_recommendation_weak_skill_prioritized():
    """Skill with lowest mastery is prioritized when no overdue mistakes exist."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        # Find 2 questions in different skills
        qs = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().all()
        q_weak = qs[0]
        q_strong = next(q for q in qs if q.skill != q_weak.skill)

        # Log 5 incorrect attempts on q_weak (low mastery)
        for _ in range(5):
            session.add(
                QuestionAttempt(
                    user_id=user.id,
                    question_id=q_weak.id,
                    selected_option_id=q_weak.options[0].id,
                    is_correct=False,
                    time_spent_seconds=30,
                    answered_at=datetime.now(timezone.utc),
                )
            )

        # Log 5 correct attempts on q_strong (higher mastery)
        for _ in range(5):
            session.add(
                QuestionAttempt(
                    user_id=user.id,
                    question_id=q_strong.id,
                    selected_option_id=q_strong.options[0].id,
                    is_correct=True,
                    time_spent_seconds=30,
                    answered_at=datetime.now(timezone.utc),
                )
            )
        await session.commit()

        rec_type, domain, skill, diff, reason, _ = (
            await AdaptiveEngineService.determine_next_recommendation(
                db=session,
                user_id=user.id,
                subject=Subject.MATH.value,
            )
        )
        assert rec_type == RecommendationType.WEAK_SKILL.value
        assert skill == q_weak.skill
        assert "accuracy" in reason.lower() or "mastery" in reason.lower()


@pytest.mark.asyncio
async def test_recommendation_new_skill_when_zero_attempts():
    """For a new user with 0 attempts, recommendations introduce new syllabus skills."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        rec_type, domain, skill, diff, reason, _ = (
            await AdaptiveEngineService.determine_next_recommendation(
                db=session,
                user_id=user.id,
                subject=Subject.MATH.value,
            )
        )
        assert rec_type == RecommendationType.NEW_SKILL.value
        assert "syllabus" in reason.lower() or "coverage" in reason.lower()


# ==================== 4. QUESTION SELECTOR & COOLDOWN TESTS ====================

@pytest.mark.asyncio
async def test_question_selector_respects_cooldown():
    """Recently answered questions within the last 20 attempts are excluded from selection."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        # Fetch two algebra questions
        algebra_qs = (
            await session.execute(
                select(Question).where(
                    Question.subject == Subject.MATH.value,
                    Question.domain == MathDomain.ALGEBRA.value,
                )
            )
        ).scalars().all()
        q1 = algebra_qs[0]
        q2 = algebra_qs[1]

        # Put q1 in cooldown
        session.add(
            QuestionAttempt(
                user_id=user.id,
                question_id=q1.id,
                selected_option_id=q1.options[0].id,
                is_correct=True,
                time_spent_seconds=20,
                answered_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        chosen_q = await AdaptiveEngineService.select_question(
            db=session,
            user_id=user.id,
            target_domain=q1.domain,
            target_skill=q1.skill,
            target_difficulty=q1.difficulty,
            subject=Subject.MATH.value,
        )
        assert chosen_q is not None
        assert chosen_q.id != q1.id


@pytest.mark.asyncio
async def test_question_selector_fallback_when_difficulty_absent():
    """When target difficulty is not found for skill, falls back gracefully without crashing."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        # Request HARD for a skill with only EASY/MEDIUM
        chosen_q = await AdaptiveEngineService.select_question(
            db=session,
            user_id=user.id,
            target_domain=MathDomain.ALGEBRA.value,
            target_skill="Linear equations in one variable",
            target_difficulty=Difficulty.HARD.value,
            subject=Subject.MATH.value,
        )
        assert chosen_q is not None
        assert chosen_q.subject == Subject.MATH.value


@pytest.mark.asyncio
async def test_get_next_api_no_answer_leak():
    """GET /api/v1/adaptive/next provides recommendation without leaking answer keys."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/adaptive/next", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "question" in data
        assert "recommendation_type" in data
        assert "reason" in data
        q = data["question"]
        assert "explanation" not in q
        for opt in q["options"]:
            assert "is_correct" not in opt


# ==================== 5. ADAPTIVE PRACTICE SESSIONS ====================

@pytest.mark.asyncio
async def test_session_lifecycle_start_and_resume():
    """Starting an adaptive session creates it; repeating the call resumes the active session."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start new session
        r1 = await client.post("/api/v1/adaptive/session", json={"total_questions": 5}, headers=headers)
        assert r1.status_code == 200
        d1 = r1.json()
        sess_id = d1["id"]
        assert d1["status"] == "IN_PROGRESS"
        assert d1["current_question_index"] == 0
        assert d1["current_question"] is not None

        # Repeat call -> should return the same session ID
        r2 = await client.post("/api/v1/adaptive/session", json={"total_questions": 5}, headers=headers)
        assert r2.status_code == 200
        assert r2.json()["id"] == sess_id

        # GET /adaptive/session/current returns active session
        r_curr = await client.get("/api/v1/adaptive/session/current", headers=headers)
        assert r_curr.status_code == 200
        assert r_curr.json()["id"] == sess_id


@pytest.mark.asyncio
async def test_session_answer_submission_and_progression():
    """Submitting an answer updates session, adjusts difficulty, and advances to next question."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start 5-question session
        start_res = await client.post("/api/v1/adaptive/session", json={"total_questions": 5}, headers=headers)
        sess_data = start_res.json()
        sess_id = sess_data["id"]
        curr_q = sess_data["current_question"]["question"]
        q_id = curr_q["id"]
        opt_id = curr_q["options"][0]["id"]

        # Submit answer
        ans_res = await client.post(
            f"/api/v1/adaptive/session/{sess_id}/questions/{q_id}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 40},
            headers=headers,
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert "is_correct" in ans_data
        assert "explanation" in ans_data
        assert ans_data["session_completed"] is False
        assert ans_data["next_question"] is not None
        assert ans_data["next_question"]["order_index"] == 1


@pytest.mark.asyncio
async def test_session_duplicate_answer_rejected():
    """Answering the same adaptive question twice returns 400 error."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_res = await client.post("/api/v1/adaptive/session", json={"total_questions": 5}, headers=headers)
        sess_id = start_res.json()["id"]
        curr_q = start_res.json()["current_question"]["question"]
        q_id = curr_q["id"]
        opt_id = curr_q["options"][0]["id"]

        # First answer: success
        await client.post(
            f"/api/v1/adaptive/session/{sess_id}/questions/{q_id}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 30},
            headers=headers,
        )

        # Duplicate answer: rejected with 400
        dup_res = await client.post(
            f"/api/v1/adaptive/session/{sess_id}/questions/{q_id}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 30},
            headers=headers,
        )
        assert dup_res.status_code == 400


@pytest.mark.asyncio
async def test_session_cross_question_option_rejected():
    """Submitting an option that belongs to a different question is rejected with 422."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)
        qs = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().all()
        q1, q2 = qs[0], qs[1]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_res = await client.post("/api/v1/adaptive/session", json={"total_questions": 5}, headers=headers)
        sess_id = start_res.json()["id"]
        curr_q = start_res.json()["current_question"]["question"]
        q_id = curr_q["id"]

        # Option from foreign question q2
        foreign_opt_id = q2.options[0].id if q2.id != uuid.UUID(q_id) else q1.options[0].id

        bad_res = await client.post(
            f"/api/v1/adaptive/session/{sess_id}/questions/{q_id}/answer",
            json={"selected_option_id": str(foreign_opt_id), "time_spent_seconds": 30},
            headers=headers,
        )
        assert bad_res.status_code == 422


@pytest.mark.asyncio
async def test_session_full_completion_and_summary():
    """Completing all questions in a session marks it COMPLETED and produces summary."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start a 3-question short session
        r = await client.post("/api/v1/adaptive/session", json={"total_questions": 3}, headers=headers)
        sess_data = r.json()
        sess_id = sess_data["id"]

        # Step through 3 questions
        for idx in range(3):
            # Fetch current question
            curr_res = await client.get("/api/v1/adaptive/session/current", headers=headers)
            curr_q = curr_res.json()["current_question"]["question"]
            qid = curr_q["id"]
            opt_id = curr_q["options"][0]["id"]

            ans_res = await client.post(
                f"/api/v1/adaptive/session/{sess_id}/questions/{qid}/answer",
                json={"selected_option_id": opt_id, "time_spent_seconds": 25},
                headers=headers,
            )
            assert ans_res.status_code == 200
            if idx == 2:
                # Last question
                last_data = ans_res.json()
                assert last_data["session_completed"] is True
                assert last_data["session_summary"] is not None
                assert last_data["session_summary"]["total_completed"] == 3


# ==================== 6. SECURITY & USER ISOLATION ====================

@pytest.mark.asyncio
async def test_cross_user_session_isolation():
    """User B cannot access or submit answers to User A's adaptive session."""
    user_a = await create_test_user()
    user_b = await create_test_user()
    token_a = create_access_token(user_a.id)
    token_b = create_access_token(user_b.id)

    async with async_session_factory() as session:
        await seed_questions(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User A starts session
        r_a = await client.post(
            "/api/v1/adaptive/session",
            json={"total_questions": 5},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        sess_id = r_a.json()["id"]
        q_id = r_a.json()["current_question"]["question"]["id"]
        opt_id = r_a.json()["current_question"]["question"]["options"][0]["id"]

        # User B attempts to access User A's session
        b_get = await client.get(
            f"/api/v1/adaptive/session/{sess_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert b_get.status_code == 404

        # User B attempts to submit answer to User A's session
        b_ans = await client.post(
            f"/api/v1/adaptive/session/{sess_id}/questions/{q_id}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 20},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert b_ans.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected():
    """Unauthenticated requests to adaptive endpoints return 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/api/v1/adaptive/next")).status_code == 401
        assert (await client.get("/api/v1/adaptive/analytics")).status_code == 401
        assert (await client.post("/api/v1/adaptive/session", json={})).status_code == 401


# ==================== 7. ANALYTICS & DIAGNOSTIC INTEGRATION ====================

@pytest.mark.asyncio
async def test_adaptive_analytics_endpoint():
    """GET /api/v1/adaptive/analytics accurately reflects user skill progression."""
    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        await seed_questions(session)
        # Add 1 attempt
        q = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().first()
        session.add(
            QuestionAttempt(
                user_id=user.id,
                question_id=q.id,
                selected_option_id=q.options[0].id,
                is_correct=True,
                time_spent_seconds=20,
                answered_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/adaptive/analytics", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "overall_mastery" in data
        assert "skills" in data
        assert len(data["skills"]) >= 20  # Covers all canonical math skills
        assert "recommended_skill" in data


@pytest.mark.asyncio
async def test_diagnostic_weak_domain_influences_recommendation():
    """When diagnostic flags a domain as WEAK, skills in that domain get early recommendation priority."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)

        # Create diagnostic result with Geometry as WEAK
        diag_sess = DiagnosticSession(
            user_id=user.id,
            status="COMPLETED",
            current_module=Subject.READING_WRITING.value,
        )
        session.add(diag_sess)
        await session.flush()

        diag_res = DiagnosticResult(
            session_id=diag_sess.id,
            math_correct=10,
            math_total=20,
            rw_correct=10,
            rw_total=20,
            math_accuracy=0.5,
            rw_accuracy=0.5,
            total_accuracy=0.5,
            estimated_math_low=450,
            estimated_math_high=510,
            estimated_rw_low=450,
            estimated_rw_high=510,
            estimated_total_low=900,
            estimated_total_high=1020,
            duration_seconds=1200,
            domain_breakdown={
                MathDomain.GEOMETRY_TRIGONOMETRY.value: {
                    "correct": 1,
                    "total": 5,
                    "classification": DomainClassification.WEAK.value,
                },
                MathDomain.ALGEBRA.value: {
                    "correct": 5,
                    "total": 5,
                    "classification": DomainClassification.STRONG.value,
                },
            },
            weak_domains=[MathDomain.GEOMETRY_TRIGONOMETRY.value],
            strong_domains=[MathDomain.ALGEBRA.value],
        )
        session.add(diag_res)
        await session.commit()

        # Recommendation for new practice should prioritize the WEAK diagnostic domain (Geometry)
        rec_type, domain, skill, diff, reason, _ = (
            await AdaptiveEngineService.determine_next_recommendation(
                db=session,
                user_id=user.id,
                subject=Subject.MATH.value,
            )
        )
        assert domain == MathDomain.GEOMETRY_TRIGONOMETRY.value
