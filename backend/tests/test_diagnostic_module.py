import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.diagnostic import (
    DiagnosticModule,
    DiagnosticQuestion,
    DiagnosticResult,
    DiagnosticSession,
)
from backend.app.models.enums import DiagnosticStatus, Subject
from backend.app.models.profile import UserProfile
from backend.app.models.question import Question
from backend.app.models.user import User

from backend.app.seed.questions import seed_questions
from backend.app.services.diagnostic_question_selector import DiagnosticQuestionSelector
from backend.app.services.diagnostic_result_service import DiagnosticResultService


@pytest.fixture
async def diagnostic_fixture():
    async with async_session_factory() as session:
        # Ensure questions are seeded (all 48)
        await seed_questions(session)

        # Create primary test user A
        user_a = User(
            telegram_id=990001,
            first_name="AliceDiagnostic",
            username="alice_diag",
            target_score=1400,
        )
        session.add(user_a)
        await session.flush()

        profile_a = UserProfile(
            user_id=user_a.id,
            target_score=1400,
            diagnostic_status="not_started",
        )
        session.add(profile_a)

        # Create secondary test user B (for cross-user security tests)
        user_b = User(
            telegram_id=990002,
            first_name="BobDiagnostic",
            username="bob_diag",
            target_score=1350,
        )
        session.add(user_b)
        await session.flush()

        profile_b = UserProfile(
            user_id=user_b.id,
            target_score=1350,
            diagnostic_status="not_started",
        )
        session.add(profile_b)

        await session.commit()
        await session.refresh(user_a)
        await session.refresh(user_b)

        token_a = create_access_token(user_id=str(user_a.id))
        token_b = create_access_token(user_id=str(user_b.id))

    async with (
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token_a}"},
        ) as client_a,
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {token_b}"},
        ) as client_b,
    ):
        yield client_a, client_b, user_a, user_b

    # Cleanup test users
    async with async_session_factory() as session:
        ua = await session.get(User, user_a.id)
        if ua:
            await session.delete(ua)
        ub = await session.get(User, user_b.id)
        if ub:
            await session.delete(ub)
        await session.commit()


@pytest.mark.asyncio
async def test_question_selector_balance_and_uniqueness():
    """Validates that DiagnosticQuestionSelector picks exactly 20 Math and 20 RW questions with no duplicates."""
    async with async_session_factory() as session:
        await seed_questions(session)
        math_qs, rw_qs = await DiagnosticQuestionSelector.select_questions(session)

    assert len(math_qs) == 20
    assert len(rw_qs) == 20

    all_ids = {str(q.id) for q in math_qs + rw_qs}
    assert len(all_ids) == 40  # Zero duplicates

    # Check Math domain distribution (5 per domain)
    math_domains = [q.domain for q in math_qs]
    for d in ["ALGEBRA", "ADVANCED_MATH", "PROBLEM_SOLVING_DATA_ANALYSIS", "GEOMETRY_TRIGONOMETRY"]:
        assert math_domains.count(d) == 5

    # Check RW domain distribution (5 per domain)
    rw_domains = [q.domain for q in rw_qs]
    for d in ["INFORMATION_IDEAS", "CRAFT_STRUCTURE", "EXPRESSION_IDEAS", "STANDARD_ENGLISH_CONVENTIONS"]:
        assert rw_domains.count(d) == 5

    # Check difficulty counts for Math
    math_diffs = [q.difficulty for q in math_qs]
    assert math_diffs.count("EASY") >= 4
    assert math_diffs.count("MEDIUM") >= 8
    assert math_diffs.count("HARD") >= 4


@pytest.mark.asyncio
async def test_start_and_resume_diagnostic(diagnostic_fixture):
    """Tests starting a diagnostic session and resuming it upon repeated start calls."""
    client_a, _, user_a, _ = diagnostic_fixture

    # 1. Start new diagnostic
    resp1 = await client_a.post("/api/v1/diagnostics")
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["status"] == "IN_PROGRESS"
    assert data1["current_module"] == "MATH"
    assert data1["total_questions"] == 40
    session_id = data1["id"]

    # 2. Calling start again should resume the existing session (same ID)
    resp2 = await client_a.post("/api/v1/diagnostics")
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["id"] == session_id
    assert data2["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_get_current_diagnostic_without_answer_leak(diagnostic_fixture):
    """Ensures GET /diagnostics/current provides the current question without exposing answer keys."""
    client_a, _, user_a, _ = diagnostic_fixture

    # Start session
    start_resp = await client_a.post("/api/v1/diagnostics")
    assert start_resp.status_code == 201

    # Fetch current state
    curr_resp = await client_a.get("/api/v1/diagnostics/current")
    assert curr_resp.status_code == 200
    curr_data = curr_resp.json()

    assert curr_data["status"] == "IN_PROGRESS"
    assert curr_data["subject"] == "MATH"
    assert curr_data["module_number"] == 1
    assert curr_data["current_question_index"] == 0
    assert curr_data["total_in_module"] == 20
    assert curr_data["total_questions"] == 40
    assert curr_data["answered_in_module"] == 0

    # Strict check: NO answer keys leaked
    q = curr_data["current_question"]
    assert q is not None
    assert "correct_answer" not in q
    assert "explanation" not in q
    assert "is_correct" not in q

    for opt in q["options"]:
        assert "is_correct" not in opt
        assert "id" in opt
        assert "label" in opt
        assert "text" in opt


@pytest.mark.asyncio
async def test_submit_diagnostic_answer_and_validations(diagnostic_fixture):
    """Tests answer submission, duplicate rejection, and cross-question tampering prevention."""
    client_a, _, user_a, _ = diagnostic_fixture

    start_resp = await client_a.post("/api/v1/diagnostics")
    session_id = start_resp.json()["id"]

    curr_resp = await client_a.get("/api/v1/diagnostics/current")
    curr_data = curr_resp.json()
    q = curr_data["current_question"]
    q_id = q["id"]
    valid_opt_id = q["options"][0]["id"]

    # 1. Reject invalid time_spent (< 0 or > 3600)
    bad_time_resp = await client_a.post(
        f"/api/v1/diagnostics/{session_id}/questions/{q_id}/answer",
        json={"selected_option_id": valid_opt_id, "time_spent_seconds": -5},
    )
    assert bad_time_resp.status_code == 422

    # 2. Reject cross-question option (option from a different question)
    fake_opt_id = str(uuid.uuid4())
    cross_opt_resp = await client_a.post(
        f"/api/v1/diagnostics/{session_id}/questions/{q_id}/answer",
        json={"selected_option_id": fake_opt_id, "time_spent_seconds": 30},
    )
    assert cross_opt_resp.status_code in [404, 422]

    # 3. Successful answer submission
    ans_resp = await client_a.post(
        f"/api/v1/diagnostics/{session_id}/questions/{q_id}/answer",
        json={"selected_option_id": valid_opt_id, "time_spent_seconds": 45},
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert ans_data["module_completed"] is False
    assert ans_data["diagnostic_completed"] is False
    assert ans_data["total_answered"] == 1

    # 4. Reject duplicate answer to the same question
    dup_resp = await client_a.post(
        f"/api/v1/diagnostics/{session_id}/questions/{q_id}/answer",
        json={"selected_option_id": valid_opt_id, "time_spent_seconds": 45},
    )
    assert dup_resp.status_code == 400


@pytest.mark.asyncio
async def test_cross_user_security_protection(diagnostic_fixture):
    """Ensures User B cannot submit answers or access results for User A's diagnostic session."""
    client_a, client_b, user_a, user_b = diagnostic_fixture

    # User A starts diagnostic
    start_resp = await client_a.post("/api/v1/diagnostics")
    session_id_a = start_resp.json()["id"]

    curr_resp = await client_a.get("/api/v1/diagnostics/current")
    q_id = curr_resp.json()["current_question"]["id"]
    opt_id = curr_resp.json()["current_question"]["options"][0]["id"]

    # User B attempts to submit an answer to User A's diagnostic
    b_submit_resp = await client_b.post(
        f"/api/v1/diagnostics/{session_id_a}/questions/{q_id}/answer",
        json={"selected_option_id": opt_id, "time_spent_seconds": 25},
    )
    assert b_submit_resp.status_code == 403

    # User B attempts to access User A's diagnostic result
    b_result_resp = await client_b.get(f"/api/v1/diagnostics/{session_id_a}/result")
    assert b_result_resp.status_code == 403


@pytest.mark.asyncio
async def test_deterministic_scoring_algorithm():
    """Validates deterministic score calculations for 0%, 50%, and 100% boundary cases."""
    # 0% correct (0 / 20) -> [200, 240]
    m_low, m_high = DiagnosticResultService.calculate_section_estimate(0, 20)
    assert m_low == 200
    assert m_high == 240

    # 50% correct (10 / 20) -> midpoint 500 -> [470, 530]
    m_low, m_high = DiagnosticResultService.calculate_section_estimate(10, 20)
    assert m_low == 470
    assert m_high == 530

    # 100% correct (20 / 20) -> [760, 800]
    m_low, m_high = DiagnosticResultService.calculate_section_estimate(20, 20)
    assert m_low == 760
    assert m_high == 800

    # Total combinations
    tot_low, tot_high = DiagnosticResultService.calculate_total_estimate((470, 530), (470, 530))
    assert tot_low == 940
    assert tot_high == 1060


@pytest.mark.asyncio
async def test_full_diagnostic_completion_and_profile_update(diagnostic_fixture):
    """
    Tests completing all 40 questions in a diagnostic session.
    Verifies module transition, score estimation, domain breakdown,
    and UserProfile update while preserving target_score.
    """
    client_a, _, user_a, _ = diagnostic_fixture

    # Start diagnostic
    start_resp = await client_a.post("/api/v1/diagnostics")
    session_id = uuid.UUID(start_resp.json()["id"])

    # Load session and questions from DB to answer all 40 questions directly through the service/endpoint
    async with async_session_factory() as session:
        diag_session_stmt = (
            select(DiagnosticSession)
            .where(DiagnosticSession.id == session_id)
            .options(
                selectinload(DiagnosticSession.modules)
                .selectinload(DiagnosticModule.questions)
                .selectinload(DiagnosticQuestion.question)
                .selectinload(Question.options),
            )
        )
        res = await session.execute(diag_session_stmt)
        diag_session = res.scalar_one()

        mod1 = next(m for m in diag_session.modules if m.module_number == 1)
        mod2 = next(m for m in diag_session.modules if m.module_number == 2)

        # Answer all 20 questions in Module 1
        for dq in mod1.questions:
            # Pick the correct option for first 14 questions, incorrect for rest
            correct_opt = next(o for o in dq.question.options if o.is_correct)
            wrong_opt = next(o for o in dq.question.options if not o.is_correct)
            chosen_opt = correct_opt if dq.order_index < 14 else wrong_opt

            resp = await client_a.post(
                f"/api/v1/diagnostics/{session_id}/questions/{dq.question_id}/answer",
                json={"selected_option_id": str(chosen_opt.id), "time_spent_seconds": 40},
            )
            assert resp.status_code == 200

        # After 20 questions of Module 1, Module 1 should be complete and transitioned to RW
        curr_state = await client_a.get("/api/v1/diagnostics/current")
        assert curr_state.json()["subject"] == "READING_WRITING"
        assert curr_state.json()["module_number"] == 2

        # Answer all 20 questions in Module 2
        for dq in mod2.questions:
            correct_opt = next(o for o in dq.question.options if o.is_correct)
            wrong_opt = next(o for o in dq.question.options if not o.is_correct)
            chosen_opt = correct_opt if dq.order_index < 16 else wrong_opt

            resp = await client_a.post(
                f"/api/v1/diagnostics/{session_id}/questions/{dq.question_id}/answer",
                json={"selected_option_id": str(chosen_opt.id), "time_spent_seconds": 50},
            )
            assert resp.status_code == 200

        last_ans = resp.json()
        assert last_ans["diagnostic_completed"] is True
        assert last_ans["total_answered"] == 40

    # Fetch completed results via GET /api/v1/diagnostics/{id}/result
    result_resp = await client_a.get(f"/api/v1/diagnostics/{session_id}/result")
    assert result_resp.status_code == 200
    res_data = result_resp.json()

    assert res_data["math_correct"] == 14
    assert res_data["math_total"] == 20
    assert res_data["rw_correct"] == 16
    assert res_data["rw_total"] == 20
    assert res_data["estimated_math_low"] > 200
    assert res_data["estimated_rw_low"] > 200
    assert res_data["estimated_total_low"] == res_data["estimated_math_low"] + res_data["estimated_rw_low"]
    assert len(res_data["domain_breakdown"]) > 0

    # Verify UserProfile was updated
    async with async_session_factory() as session:
        prof = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_a.id)
        )
        user_prof = prof.scalar_one()
        assert user_prof.diagnostic_status == "completed"
        assert user_prof.math_estimate is not None
        assert user_prof.rw_estimate is not None
        assert user_prof.target_score == 1400  # Strictly preserved!
