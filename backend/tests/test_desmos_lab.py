from datetime import datetime, timezone
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.desmos import (
    DesmosPracticeQuestion,
    DesmosPracticeSession,
    DesmosTechnique,
    QuestionDesmosTechnique,
)
from backend.app.models.enums import (
    DesmosSessionStatus,
    DesmosTechniqueType,
    Difficulty,
    MathDomain,
    MistakeStatus,
    Subject,
)
from backend.app.models.mistake_book import MistakeBookEntry
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.models.user import User
from backend.app.seed.desmos_techniques_seed import seed_desmos_techniques
from backend.app.seed.questions import seed_questions
from backend.app.services.desmos_service import DesmosService


async def create_test_user(first_name: str = "DesmosTester") -> User:
    """Helper to create a test user with unique credentials."""
    async with async_session_factory() as session:
        uid = int(uuid.uuid4().int % 1000000000)
        user = User(
            telegram_id=uid,
            username=f"desmos_user_{uid}",
            first_name=first_name,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.fixture(autouse=True)
async def ensure_seed_data():
    """Ensure math questions and desmos techniques are seeded before tests."""
    async with async_session_factory() as session:
        await seed_questions(session)
        await seed_desmos_techniques(session)


# ==================== 1. TECHNIQUE EXPLORATION TESTS ====================

@pytest.mark.asyncio
async def test_technique_list_authenticated():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/techniques", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert data["total"] >= 10
        slugs = [t["slug"] for t in data["items"]]
        assert "intersection" in slugs
        assert "zero-finding" in slugs
        assert "linear-regression" in slugs


@pytest.mark.asyncio
async def test_technique_detail_by_slug():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/techniques/intersection", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["slug"] == "intersection"
        assert data["technique_type"] == DesmosTechniqueType.INTERSECTION.value
        assert len(data["steps"]) >= 3
        assert len(data["common_mistakes"]) >= 1
        assert "sat_tip" in data
        assert data["question_count"] >= 1


@pytest.mark.asyncio
async def test_technique_not_found_404():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/techniques/non-existent-technique", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/techniques")
        assert res.status_code in (401, 403)

        res2 = await ac.post("/api/v1/desmos/session", json={"target_count": 5})
        assert res2.status_code in (401, 403)


# ==================== 2. QUESTIONS QUERYING & FILTERING TESTS ====================

@pytest.mark.asyncio
async def test_get_desmos_questions_endpoint():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/questions?limit=10", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["desmos_allowed"] is True
            assert item["subject"] == "MATH"


@pytest.mark.asyncio
async def test_question_filtering_desmos_allowed_only():
    """Verify non-desmos questions or RW questions are never included in Desmos question queries."""
    no_desmos_id = None
    async with async_session_factory() as db:
        # Create a non-desmos question with 4 options
        no_desmos_q = Question(
            subject=Subject.MATH.value,
            domain=MathDomain.ALGEBRA.value,
            skill="No Calculator Drill",
            difficulty=Difficulty.MEDIUM.value,
            question_text="No calc question",
            explanation="Manual only",
            desmos_allowed=False,
            desmos_recommended=False,
            options=[
                QuestionOption(label="A", text="1", is_correct=True, order_index=0),
                QuestionOption(label="B", text="2", is_correct=False, order_index=1),
                QuestionOption(label="C", text="3", is_correct=False, order_index=2),
                QuestionOption(label="D", text="4", is_correct=False, order_index=3),
            ],
        )
        db.add(no_desmos_q)
        await db.commit()
        no_desmos_id = no_desmos_q.id

    try:
        user = await create_test_user()
        token = create_access_token(user.id)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/desmos/questions?limit=100", headers={"Authorization": f"Bearer {token}"})
            assert res.status_code == 200
            data = res.json()
            q_ids = [item["id"] for item in data["items"]]
            assert str(no_desmos_id) not in q_ids
    finally:
        async with async_session_factory() as db:
            to_del = await db.scalar(select(Question).where(Question.id == no_desmos_id))
            if to_del:
                await db.delete(to_del)
                await db.commit()


@pytest.mark.asyncio
async def test_question_filtering_desmos_recommended():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/questions?recommended_only=true&limit=10", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        for item in data["items"]:
            assert item["desmos_recommended"] is True


@pytest.mark.asyncio
async def test_technique_question_filtering():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/desmos/questions?technique_slug=intersection&limit=10", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) >= 1


# ==================== 3. SESSION LIFECYCLE TESTS ====================

@pytest.mark.asyncio
async def test_desmos_session_creation():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5, "technique_slug": "intersection"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == DesmosSessionStatus.IN_PROGRESS.value
        assert data["technique_slug"] == "intersection"
        assert len(data["questions"]) == 5
        assert data["current_question"] is not None
        assert data["current_question"]["recommendation_status"] in ("RECOMMENDED", "ALLOWED")


@pytest.mark.asyncio
async def test_session_resume_in_progress():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create session
        res1 = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5, "technique_slug": "intersection"},
            headers={"Authorization": f"Bearer {token}"},
        )
        sid1 = res1.json()["id"]

        # Call again with identical params
        res2 = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5, "technique_slug": "intersection"},
            headers={"Authorization": f"Bearer {token}"},
        )
        sid2 = res2.json()["id"]
        assert sid1 == sid2

        # Check GET /current
        cur_res = await ac.get("/api/v1/desmos/session/current", headers={"Authorization": f"Bearer {token}"})
        assert cur_res.status_code == 200
        assert cur_res.json()["id"] == sid1


@pytest.mark.asyncio
async def test_session_ownership_protection():
    user1 = await create_test_user("UserOne")
    user2 = await create_test_user("UserTwo")
    token1 = create_access_token(user1.id)
    token2 = create_access_token(user2.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User 1 creates session
        res1 = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token1}"},
        )
        sid1 = res1.json()["id"]

        # User 2 tries to access User 1's session
        res2 = await ac.get(f"/api/v1/desmos/session/{sid1}", headers={"Authorization": f"Bearer {token2}"})
        assert res2.status_code == 404


@pytest.mark.asyncio
async def test_no_answer_leak_before_submission():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = res.json()
        current_q = session["current_question"]
        assert current_q is not None

        # Verify no option leaks 'is_correct'
        for opt in current_q["options"]:
            assert "is_correct" not in opt
        assert "explanation" not in current_q


# ==================== 4. ANSWER SUBMISSION & SCORING TESTS ====================

@pytest.mark.asyncio
async def test_submit_correct_answer():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        q_item = session["current_question"]
        qid = q_item["question_id"]

        # Find correct option directly in DB
        async with async_session_factory() as db:
            cor_opt = await db.scalar(
                select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(qid), QuestionOption.is_correct == True)
            )

        ans_res = await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": str(cor_opt), "time_spent_seconds": 35, "desmos_used": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert ans_data["is_correct"] is True
        assert ans_data["correct_option_id"] == str(cor_opt)
        assert "explanation" in ans_data
        assert ans_data["session_accuracy"] == 100.0


@pytest.mark.asyncio
async def test_submit_incorrect_answer():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        q_item = session["current_question"]
        qid = q_item["question_id"]

        # Find wrong option in DB
        async with async_session_factory() as db:
            wrong_opt = await db.scalar(
                select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(qid), QuestionOption.is_correct == False)
            )

        ans_res = await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": str(wrong_opt), "time_spent_seconds": 50, "desmos_used": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert ans_data["is_correct"] is False
        assert ans_data["session_accuracy"] == 0.0


@pytest.mark.asyncio
async def test_question_attempt_recorded_on_answer():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        qid = session["current_question"]["question_id"]
        opt_id = session["current_question"]["options"][0]["id"]

        await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 42},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Verify attempt in DB
    async with async_session_factory() as db:
        att = await db.scalar(
            select(QuestionAttempt).where(QuestionAttempt.user_id == user.id, QuestionAttempt.question_id == uuid.UUID(qid))
        )
        assert att is not None
        assert att.time_spent_seconds == 42


@pytest.mark.asyncio
async def test_mistake_book_integration_on_incorrect():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        qid = session["current_question"]["question_id"]

        # Wrong option
        async with async_session_factory() as db:
            wrong_opt = await db.scalar(
                select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(qid), QuestionOption.is_correct == False)
            )

        await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": str(wrong_opt), "time_spent_seconds": 60},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Verify MistakeBookEntry created
    async with async_session_factory() as db:
        m_entry = await db.scalar(
            select(MistakeBookEntry).where(MistakeBookEntry.user_id == user.id, MistakeBookEntry.question_id == uuid.UUID(qid))
        )
        assert m_entry is not None
        assert m_entry.status == MistakeStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_duplicate_answer_rejection():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        qid = session["current_question"]["question_id"]
        opt_id = session["current_question"]["options"][0]["id"]

        # First answer
        res1 = await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res1.status_code == 200

        # Second answer to same question -> 400
        res2 = await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": opt_id, "time_spent_seconds": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res2.status_code == 400


@pytest.mark.asyncio
async def test_cross_question_option_rejection():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]
        qid = session["current_question"]["question_id"]

        # Option from question 2
        q2_opt_id = session["questions"][1]["options"][0]["id"]

        res = await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
            json={"selected_option_id": q2_opt_id, "time_spent_seconds": 30},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422


# ==================== 5. SESSION COMPLETION & ABANDON ====================

@pytest.mark.asyncio
async def test_session_full_completion_and_summary():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]

        for q in session["questions"]:
            qid = q["question_id"]
            # Fetch correct option
            async with async_session_factory() as db:
                cor_opt = await db.scalar(
                    select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(qid), QuestionOption.is_correct == True)
                )

            ans_res = await ac.post(
                f"/api/v1/desmos/session/{sid}/questions/{qid}/answer",
                json={"selected_option_id": str(cor_opt), "time_spent_seconds": 25},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert ans_res.status_code == 200

        # Final check on session
        final_res = await ac.get(f"/api/v1/desmos/session/{sid}", headers={"Authorization": f"Bearer {token}"})
        final_data = final_res.json()
        assert final_data["status"] == DesmosSessionStatus.COMPLETED.value
        assert final_data["completed_count"] == 3
        assert final_data["correct_count"] == 3
        assert final_data["accuracy_percent"] == 100.0


@pytest.mark.asyncio
async def test_abandon_session():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        sid = s_res.json()["id"]

        ab_res = await ac.post(f"/api/v1/desmos/session/{sid}/abandon", headers={"Authorization": f"Bearer {token}"})
        assert ab_res.status_code == 200
        assert ab_res.json()["status"] == DesmosSessionStatus.ABANDONED.value

        # Active session should now be None
        cur_res = await ac.get("/api/v1/desmos/session/current", headers={"Authorization": f"Bearer {token}"})
        assert cur_res.status_code == 200
        assert cur_res.json() is None


# ==================== 6. ANALYTICS & CROSS-USER ISOLATION ====================

@pytest.mark.asyncio
async def test_desmos_analytics_calculation():
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start and answer 2 questions (1 right, 1 wrong)
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        session = s_res.json()
        sid = session["id"]

        # Q1 correct
        q1_id = session["questions"][0]["question_id"]
        async with async_session_factory() as db:
            cor_opt = await db.scalar(
                select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(q1_id), QuestionOption.is_correct == True)
            )
        await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{q1_id}/answer",
            json={"selected_option_id": str(cor_opt), "time_spent_seconds": 40},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Q2 wrong
        q2_id = session["questions"][1]["question_id"]
        async with async_session_factory() as db:
            wrong_opt = await db.scalar(
                select(QuestionOption.id).where(QuestionOption.question_id == uuid.UUID(q2_id), QuestionOption.is_correct == False)
            )
        await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{q2_id}/answer",
            json={"selected_option_id": str(wrong_opt), "time_spent_seconds": 60},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Fetch analytics
        an_res = await ac.get("/api/v1/desmos/analytics", headers={"Authorization": f"Bearer {token}"})
        assert an_res.status_code == 200
        an_data = an_res.json()
        assert an_data["total_questions_attempted"] == 2
        assert an_data["total_correct"] == 1
        assert an_data["overall_accuracy"] == 50.0
        assert an_data["avg_time_seconds"] == 50.0
        assert len(an_data["techniques"]) >= 10


@pytest.mark.asyncio
async def test_cross_user_analytics_isolation():
    user1 = await create_test_user("AnalyticUser1")
    user2 = await create_test_user("AnalyticUser2")
    token1 = create_access_token(user1.id)
    token2 = create_access_token(user2.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User 1 practices
        s_res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 3},
            headers={"Authorization": f"Bearer {token1}"},
        )
        session = s_res.json()
        sid = session["id"]
        q1_id = session["questions"][0]["question_id"]
        opt1 = session["questions"][0]["options"][0]["id"]
        await ac.post(
            f"/api/v1/desmos/session/{sid}/questions/{q1_id}/answer",
            json={"selected_option_id": opt1, "time_spent_seconds": 40},
            headers={"Authorization": f"Bearer {token1}"},
        )

        # User 2 checks analytics -> should be 0 attempts
        an_res2 = await ac.get("/api/v1/desmos/analytics", headers={"Authorization": f"Bearer {token2}"})
        assert an_res2.status_code == 200
        data2 = an_res2.json()
        assert data2["total_questions_attempted"] == 0
        assert data2["total_correct"] == 0
        assert data2["overall_accuracy"] == 0.0


@pytest.mark.asyncio
async def test_technique_question_fallback():
    """Verify requesting a technique with few linked questions falls back smoothly to Desmos-allowed math questions."""
    user = await create_test_user()
    token = create_access_token(user.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/desmos/session",
            json={"target_count": 10, "technique_slug": "quadratic-regression"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201
        data = res.json()
        assert len(data["questions"]) == 10
        for q in data["questions"]:
            assert q["desmos_allowed"] is True
