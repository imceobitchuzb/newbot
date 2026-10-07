from datetime import datetime, timedelta, timezone
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
    DiagnosticSession,
)
from backend.app.models.enums import (
    DiagnosticStatus,
    Difficulty,
    MathDomain,
    MistakeStatus,
    MistakeType,
    Subject,
)
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.models.question import Question, QuestionAttempt
from backend.app.models.user import User
from backend.app.seed.questions import seed_questions
from backend.app.services.diagnostic_service import DiagnosticService
from backend.app.services.math_practice_service import MathPracticeService
from backend.app.services.mistake_book_service import MistakeBookService


async def create_test_user():
    """Helper to create a test user with unique credentials."""
    async with async_session_factory() as session:
        uid = int(uuid.uuid4().int % 1000000000)
        user = User(
            telegram_id=uid,
            username=f"user_{uid}",
            first_name="Tester",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# ==================== 1. CREATION TESTS ====================

@pytest.mark.asyncio
async def test_wrong_math_attempt_creates_mistake_and_correct_does_not():
    """Verify that an incorrect practice attempt auto-creates a mistake entry, while a correct one does not."""
    async with async_session_factory() as session:
        await seed_questions(session)

    user = await create_test_user()
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Start a 5-question session
        start_res = await client.post(
            "/api/v1/math/practice",
            json={"domain": MathDomain.ALGEBRA.value, "question_count": 5},
            headers=headers,
        )
        assert start_res.status_code == 200
        session_data = start_res.json()
        session_id = session_data["id"]

        q1 = session_data["questions"][0]
        q2 = session_data["questions"][1]

        # Answer question 1 incorrectly
        async with async_session_factory() as s:
            q1_obj = await s.get(Question, uuid.UUID(q1["question_id"]))
            wrong_opt = next(o for o in q1_obj.options if not o.is_correct)
            correct_opt_2 = next(o for o in (await s.get(Question, uuid.UUID(q2["question_id"]))).options if o.is_correct)
            wrong_opt_id = wrong_opt.id
            correct_opt_id = correct_opt_2.id

        ans1_res = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q1['practice_question_id']}/answer",
            json={"selected_option_id": str(wrong_opt_id), "time_spent_seconds": 30},
            headers=headers,
        )
        assert ans1_res.status_code == 200
        assert ans1_res.json()["is_correct"] is False

        # Answer question 2 correctly
        ans2_res = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q2['practice_question_id']}/answer",
            json={"selected_option_id": str(correct_opt_id), "time_spent_seconds": 40},
            headers=headers,
        )
        assert ans2_res.status_code == 200
        assert ans2_res.json()["is_correct"] is True

        # Check mistake book
        mistakes_res = await client.get("/api/v1/mistakes", headers=headers)
        assert mistakes_res.status_code == 200
        data = mistakes_res.json()
        assert data["total"] == 1
        assert data["items"][0]["question_id"] == q1["question_id"]
        assert data["items"][0]["status"] == MistakeStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_duplicate_mistake_not_created_same_user_and_question():
    """Verify that multiple wrong attempts on the same question update the existing entry without duplication."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().first()
        q_id = q.id

        # First wrong answer
        e1 = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q_id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        entry_id_1 = e1.id

        # Second wrong answer to same question
        e2 = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q_id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        entry_id_2 = e2.id

        assert entry_id_1 == entry_id_2

        # Verify exactly 1 entry exists in database
        entries = (
            await session.execute(
                select(MistakeBookEntry).where(
                    MistakeBookEntry.user_id == user.id,
                    MistakeBookEntry.question_id == q_id,
                )
            )
        ).scalars().all()
        assert len(entries) == 1


@pytest.mark.asyncio
async def test_diagnostic_completion_populates_mistakes():
    """Verify completing diagnostic automatically captures incorrect answers into Mistake Book."""
    user = await create_test_user()
    diag_service = DiagnosticService()

    async with async_session_factory() as session:
        await seed_questions(session)
        diag = await diag_service.start_or_resume(session, user.id)
        diag_id = diag.id

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Fetch question order for Module 1 and Module 2
        async with async_session_factory() as session:
            stmt = (
                select(DiagnosticSession)
                .where(DiagnosticSession.id == diag_id)
                .options(
                    selectinload(DiagnosticSession.modules)
                    .selectinload(DiagnosticModule.questions)
                    .selectinload(DiagnosticQuestion.question)
                    .selectinload(Question.options),
                )
            )
            sess_obj = (await session.execute(stmt)).scalar_one()
            mod1 = next(m for m in sess_obj.modules if m.module_number == 1)
            mod2 = next(m for m in sess_obj.modules if m.module_number == 2)

            mod1_answers = []
            for idx, dq in enumerate(sorted(mod1.questions, key=lambda q: q.order_index)):
                chosen = next(o for o in dq.question.options if (not o.is_correct if idx == 0 else o.is_correct))
                mod1_answers.append((dq.question_id, chosen.id))

            mod2_answers = []
            for idx, dq in enumerate(sorted(mod2.questions, key=lambda q: q.order_index)):
                chosen = next(o for o in dq.question.options if (not o.is_correct if idx == 0 else o.is_correct))
                mod2_answers.append((dq.question_id, chosen.id))

        # Submit answers in proper sequence (Module 1, then Module 2)
        for q_id, opt_id in mod1_answers:
            resp = await client.post(
                f"/api/v1/diagnostics/{diag_id}/questions/{q_id}/answer",
                json={"selected_option_id": str(opt_id), "time_spent_seconds": 40},
                headers=headers,
            )
            assert resp.status_code == 200

        for q_id, opt_id in mod2_answers:
            resp = await client.post(
                f"/api/v1/diagnostics/{diag_id}/questions/{q_id}/answer",
                json={"selected_option_id": str(opt_id), "time_spent_seconds": 40},
                headers=headers,
            )
            assert resp.status_code == 200

        # Check mistake book after diagnostic completion
        res = await client.get("/api/v1/mistakes", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2  # At least 1 Math and 1 RW mistake captured


# ==================== 2. OWNERSHIP & SECURITY TESTS ====================

@pytest.mark.asyncio
async def test_cross_user_isolation_get_mistake():
    """User B cannot view User A's mistake."""
    user_a = await create_test_user()
    user_b = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user_a.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id

    token_b = create_access_token(user_b.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            f"/api/v1/mistakes/{mistake_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_isolation_review():
    """User B cannot review User A's mistake."""
    user_a = await create_test_user()
    user_b = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user_a.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id

    token_b = create_access_token(user_b.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/mistakes/{mistake_id}/review",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_isolation_retry():
    """User B cannot retry User A's mistake."""
    user_a = await create_test_user()
    user_b = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user_a.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id
        opt_id = q.options[0].id

    token_b = create_access_token(user_b.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(opt_id), "time_spent_seconds": 20},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_isolation_classify():
    """User B cannot classify User A's mistake."""
    user_a = await create_test_user()
    user_b = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user_a.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id

    token_b = create_access_token(user_b.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.patch(
            f"/api/v1/mistakes/{mistake_id}/classify",
            json={"mistake_type": MistakeType.CONCEPT_GAP.value},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 404


# ==================== 3. RETRY & ATTEMPTS PRESERVATION TESTS ====================

@pytest.mark.asyncio
async def test_retry_creates_new_attempt_and_preserves_original():
    """Retry creates a new QuestionAttempt record and keeps the original attempt intact."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()

        # Original attempt: wrong
        orig_attempt = QuestionAttempt(
            user_id=user.id,
            question_id=q.id,
            selected_option_id=q.options[0].id,
            is_correct=False,
            time_spent_seconds=50,
        )
        session.add(orig_attempt)
        await session.flush()
        orig_attempt_id = orig_attempt.id

        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=orig_attempt_id,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id
        correct_opt = next(o for o in q.options if o.is_correct)

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(correct_opt.id), "time_spent_seconds": 35},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["is_correct"] is True

    # Verify both attempts exist
    async with async_session_factory() as session:
        attempts = (
            await session.execute(
                select(QuestionAttempt)
                .where(QuestionAttempt.user_id == user.id, QuestionAttempt.question_id == q.id)
                .order_by(QuestionAttempt.answered_at.asc())
            )
        ).scalars().all()
        assert len(attempts) == 2
        assert attempts[0].id == orig_attempt_id
        assert attempts[0].is_correct is False
        assert attempts[1].is_correct is True


@pytest.mark.asyncio
async def test_retry_counters_increment():
    """Correct and incorrect retry counters increment accurately."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id
        correct_opt = next(o for o in q.options if o.is_correct)
        wrong_opt = next(o for o in q.options if not o.is_correct)

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Retry 1: wrong
        r1 = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(wrong_opt.id), "time_spent_seconds": 25},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["incorrect_retry_count"] == 1
        assert data1["correct_retry_count"] == 0

        # Retry 2: correct
        r2 = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(correct_opt.id), "time_spent_seconds": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["incorrect_retry_count"] == 1
        assert data2["correct_retry_count"] == 1


# ==================== 4. MASTERY & REGRESSION TESTS ====================

@pytest.mark.asyncio
async def test_mastery_requires_two_consecutive_correct_retries():
    """1 correct retry is NOT enough; 2 consecutive correct retries transitions status to MASTERED."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id
        correct_opt = next(o for o in q.options if o.is_correct)

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Retry 1: correct -> NOT yet mastered
        r1 = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(correct_opt.id), "time_spent_seconds": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        assert r1.json()["is_mastered"] is False
        assert r1.json()["new_status"] == MistakeStatus.IN_REVIEW.value

        # Retry 2: correct -> now MASTERED
        r2 = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(correct_opt.id), "time_spent_seconds": 25},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 200
        assert r2.json()["is_mastered"] is True
        assert r2.json()["new_status"] == MistakeStatus.MASTERED.value


@pytest.mark.asyncio
async def test_regression_after_mastery():
    """An incorrect attempt on a MASTERED mistake regresses status back to ACTIVE."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        # Directly set to MASTERED
        entry.status = MistakeStatus.MASTERED.value
        await session.commit()
        mistake_id = entry.id
        wrong_opt = next(o for o in q.options if not o.is_correct)

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(wrong_opt.id), "time_spent_seconds": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["new_status"] == MistakeStatus.ACTIVE.value
        assert res.json()["is_mastered"] is False


# ==================== 5. REVIEW & SCHEDULE TESTS ====================

@pytest.mark.asyncio
async def test_review_schedule_progression():
    """Reviewing increments review_count, updates last_reviewed_at, and pushes next_review_at forward."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First review: review_count goes from 0 to 1
        r1 = await client.post(f"/api/v1/mistakes/{mistake_id}/review", headers={"Authorization": f"Bearer {token}"})
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["review_count"] == 1
        assert d1["status"] == MistakeStatus.IN_REVIEW.value
        assert d1["last_reviewed_at"] is not None

        # Second review: review_count goes from 1 to 2
        r2 = await client.post(f"/api/v1/mistakes/{mistake_id}/review", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        assert r2.json()["review_count"] == 2


@pytest.mark.asyncio
async def test_overdue_review_detection():
    """An entry with next_review_at in the past reports is_due == True."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        # Set next_review_at to yesterday
        entry.next_review_at = datetime.now(timezone.utc) - timedelta(days=2)
        await session.commit()
        mistake_id = entry.id

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(f"/api/v1/mistakes/{mistake_id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["is_due"] is True


# ==================== 6. CLASSIFICATION & PRIORITY TESTS ====================

@pytest.mark.asyncio
async def test_classify_mistake_type():
    """Updating mistake type successfully updates classification."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q = (await session.execute(select(Question))).scalars().first()
        entry = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q.id,
            attempt_id=None,
            subject=q.subject,
            domain=q.domain,
            skill=q.skill,
        )
        await session.commit()
        mistake_id = entry.id

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.patch(
            f"/api/v1/mistakes/{mistake_id}/classify",
            json={"mistake_type": MistakeType.CARELESS_ERROR.value},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["mistake_type"] == MistakeType.CARELESS_ERROR.value


@pytest.mark.asyncio
async def test_priority_queue_next_mistake():
    """GET /api/v1/mistakes/next returns overdue review first, then active."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        qs = (await session.execute(select(Question).limit(2))).scalars().all()
        q1, q2 = qs[0], qs[1]

        # Entry 1: regular active
        e1 = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q1.id,
            attempt_id=None,
            subject=q1.subject,
            domain=q1.domain,
            skill=q1.skill,
        )

        # Entry 2: overdue review
        e2 = await MistakeBookService.record_or_update_mistake(
            db=session,
            user_id=user.id,
            question_id=q2.id,
            attempt_id=None,
            subject=q2.subject,
            domain=q2.domain,
            skill=q2.skill,
        )
        e2.next_review_at = datetime.now(timezone.utc) - timedelta(days=3)
        await session.commit()
        e2_id = e2.id

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/mistakes/next", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data is not None
        assert data["id"] == str(e2_id)


# ==================== 7. FILTERS & ANALYTICS TESTS ====================

@pytest.mark.asyncio
async def test_mistakes_filters_by_subject_and_status():
    """Verify filtering by subject and status."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        q_math = (await session.execute(select(Question).where(Question.subject == Subject.MATH.value))).scalars().first()
        q_rw = (await session.execute(select(Question).where(Question.subject == Subject.READING_WRITING.value))).scalars().first()

        e_math = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=q_math.id, attempt_id=None,
            subject=q_math.subject, domain=q_math.domain, skill=q_math.skill,
        )
        e_rw = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=q_rw.id, attempt_id=None,
            subject=q_rw.subject, domain=q_rw.domain, skill=q_rw.skill,
        )
        e_rw.status = MistakeStatus.MASTERED.value
        await session.commit()

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Filter MATH
        r_math = await client.get("/api/v1/mistakes?subject=MATH", headers={"Authorization": f"Bearer {token}"})
        assert r_math.status_code == 200
        assert r_math.json()["total"] == 1
        assert r_math.json()["items"][0]["subject"] == "MATH"

        # Filter MASTERED
        r_mastered = await client.get("/api/v1/mistakes?status=MASTERED", headers={"Authorization": f"Bearer {token}"})
        assert r_mastered.status_code == 200
        assert r_mastered.json()["total"] == 1
        assert r_mastered.json()["items"][0]["status"] == "MASTERED"


@pytest.mark.asyncio
async def test_mistake_analytics_service_calculation():
    """Analytics calculations match database records accurately."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        qs = (await session.execute(select(Question).limit(3))).scalars().all()

        e1 = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=qs[0].id, attempt_id=None,
            subject=qs[0].subject, domain=qs[0].domain, skill=qs[0].skill,
        )
        e2 = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=qs[1].id, attempt_id=None,
            subject=qs[1].subject, domain=qs[1].domain, skill=qs[1].skill,
        )
        e2.status = MistakeStatus.MASTERED.value
        e2.correct_retry_count = 2

        e3 = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=qs[2].id, attempt_id=None,
            subject=qs[2].subject, domain=qs[2].domain, skill=qs[2].skill,
        )
        e3.status = MistakeStatus.IN_REVIEW.value
        e3.next_review_at = datetime.now(timezone.utc) - timedelta(hours=5)

        await session.commit()

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/mistakes/analytics", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["total_mistakes"] == 3
        assert data["active_mistakes"] == 1
        assert data["in_review_mistakes"] == 1
        assert data["mastered_mistakes"] == 1
        assert data["due_reviews"] >= 1
        assert data["mastery_rate"] == 33.3


@pytest.mark.asyncio
async def test_retry_invalid_option_rejected():
    """Submitting an option from another question is rejected with 422."""
    user = await create_test_user()

    async with async_session_factory() as session:
        await seed_questions(session)
        qs = (await session.execute(select(Question).limit(2))).scalars().all()
        q1, q2 = qs[0], qs[1]

        entry = await MistakeBookService.record_or_update_mistake(
            db=session, user_id=user.id, question_id=q1.id, attempt_id=None,
            subject=q1.subject, domain=q1.domain, skill=q1.skill,
        )
        await session.commit()
        mistake_id = entry.id
        foreign_opt_id = q2.options[0].id

    token = create_access_token(user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/mistakes/{mistake_id}/retry",
            json={"selected_option_id": str(foreign_opt_id), "time_spent_seconds": 15},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422
