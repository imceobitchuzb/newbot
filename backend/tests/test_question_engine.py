import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.enums import Difficulty, QuestionStatus, Subject
from backend.app.models.question import Question, QuestionOption
from backend.app.models.user import User
from backend.app.seed.questions import seed_questions


@pytest.fixture
async def authenticated_client():
    async with async_session_factory() as session:
        # Ensure questions are seeded
        await seed_questions(session)

        # Create a test user
        test_user = User(
            telegram_id=8811223344,
            first_name="QuestionTester",
            username="q_tester",
            target_score=1450,
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)

        token = create_access_token(user_id=str(test_user.id))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client, test_user

    # Cleanup user
    async with async_session_factory() as session:
        user_to_del = await session.get(User, test_user.id)
        if user_to_del:
            await session.delete(user_to_del)
            await session.commit()


@pytest.mark.asyncio
async def test_list_questions_authenticated(authenticated_client):
    client, user = authenticated_client
    response = await client.get("/api/v1/questions?limit=10")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) > 0
    assert len(questions) <= 10

    # Ensure no answer leakage in list
    for q in questions:
        assert "is_correct" not in q
        assert "correct_answer" not in q
        assert "correct_option_id" not in q
        for opt in q["options"]:
            assert "is_correct" not in opt
            assert "label" in opt
            assert "text" in opt


@pytest.mark.asyncio
async def test_question_filters(authenticated_client):
    client, user = authenticated_client

    # Filter Math
    res_math = await client.get("/api/v1/questions?subject=MATH&limit=20")
    assert res_math.status_code == 200
    math_questions = res_math.json()
    assert len(math_questions) > 0
    assert all(q["subject"] == "MATH" for q in math_questions)

    # Filter Reading & Writing
    res_rw = await client.get("/api/v1/questions?subject=READING_WRITING&limit=20")
    assert res_rw.status_code == 200
    rw_questions = res_rw.json()
    assert len(rw_questions) > 0
    assert all(q["subject"] == "READING_WRITING" for q in rw_questions)

    # Filter Difficulty
    res_easy = await client.get("/api/v1/questions?difficulty=EASY&limit=20")
    assert res_easy.status_code == 200
    easy_questions = res_easy.json()
    assert all(q["difficulty"] == "EASY" for q in easy_questions)


@pytest.mark.asyncio
async def test_no_answer_leak_on_get_by_id(authenticated_client):
    client, user = authenticated_client
    # Fetch a question
    list_res = await client.get("/api/v1/questions?limit=1")
    q_id = list_res.json()[0]["id"]

    res = await client.get(f"/api/v1/questions/{q_id}")
    assert res.status_code == 200
    q_data = res.json()

    # STRICT SECURITY CHECK: No is_correct anywhere in question or options!
    assert "is_correct" not in q_data
    assert "correct_answer" not in q_data
    assert "correct_option_id" not in q_data
    assert len(q_data["options"]) == 4
    for opt in q_data["options"]:
        assert "is_correct" not in opt


@pytest.mark.asyncio
async def test_draft_and_archived_questions_hidden():
    async with async_session_factory() as session:
        # Create a draft question
        draft_q = Question(
            subject=Subject.MATH.value,
            domain="ALGEBRA",
            skill="Hidden Draft",
            difficulty=Difficulty.EASY.value,
            question_text="Draft question not for learners",
            explanation="Draft explanation",
            status=QuestionStatus.DRAFT.value,
        )
        opt = QuestionOption(label="A", text="Draft answer", is_correct=True)
        draft_q.options.append(opt)
        session.add(draft_q)
        await session.commit()
        await session.refresh(draft_q)
        draft_id = draft_q.id

        # Create temporary user token
        u = User(telegram_id=99001122, first_name="DraftTester")
        session.add(u)
        await session.commit()
        await session.refresh(u)
        token = create_access_token(user_id=str(u.id))

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        # Requesting draft question must return 404
        res = await client.get(f"/api/v1/questions/{draft_id}")
        assert res.status_code == 404

        # Listing questions must not contain draft
        res_list = await client.get("/api/v1/questions?limit=50")
        assert all(q["id"] != str(draft_id) for q in res_list.json())

    # Cleanup
    async with async_session_factory() as session:
        q_del = await session.get(Question, draft_id)
        if q_del:
            await session.delete(q_del)
        u_del = await session.get(User, u.id)
        if u_del:
            await session.delete(u_del)
        await session.commit()


@pytest.mark.asyncio
async def test_submit_correct_and_incorrect_attempt(authenticated_client):
    client, user = authenticated_client

    # Fetch a question
    list_res = await client.get("/api/v1/questions?limit=1")
    q_data = list_res.json()[0]
    q_id = q_data["id"]

    # Retrieve internal correct option from database directly for test expectation
    async with async_session_factory() as session:
        db_q = await session.get(Question, uuid.UUID(q_id))
        correct_opt = next(opt for opt in db_q.options if opt.is_correct)
        wrong_opt = next(opt for opt in db_q.options if not opt.is_correct)

    # 1. Submit incorrect attempt
    wrong_res = await client.post(
        f"/api/v1/questions/{q_id}/attempt",
        json={"selected_option_id": str(wrong_opt.id), "time_spent_seconds": 35},
    )
    assert wrong_res.status_code == 200
    wrong_data = wrong_res.json()
    assert wrong_data["is_correct"] is False
    assert wrong_data["selected_option_id"] == str(wrong_opt.id)
    assert wrong_data["correct_option_id"] == str(correct_opt.id)
    assert "explanation" in wrong_data
    assert wrong_data["time_spent_seconds"] == 35

    # 2. Submit correct attempt
    correct_res = await client.post(
        f"/api/v1/questions/{q_id}/attempt",
        json={"selected_option_id": str(correct_opt.id), "time_spent_seconds": 42},
    )
    assert correct_res.status_code == 200
    correct_data = correct_res.json()
    assert correct_data["is_correct"] is True
    assert correct_data["selected_option_id"] == str(correct_opt.id)
    assert correct_data["correct_option_id"] == str(correct_opt.id)


@pytest.mark.asyncio
async def test_cross_question_option_rejection(authenticated_client):
    client, user = authenticated_client

    # Fetch two distinct questions
    list_res = await client.get("/api/v1/questions?limit=2")
    questions = list_res.json()
    q1 = questions[0]
    q2 = questions[1]

    # Try submitting option from Q2 to Q1
    q2_option_id = q2["options"][0]["id"]
    res = await client.post(
        f"/api/v1/questions/{q1['id']}/attempt",
        json={"selected_option_id": q2_option_id, "time_spent_seconds": 15},
    )
    assert res.status_code == 422
    assert "does not belong" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET /questions without auth -> 401
        res1 = await client.get("/api/v1/questions")
        assert res1.status_code == 401

        # POST attempt without auth -> 401
        dummy_id = str(uuid.uuid4())
        res2 = await client.post(
            f"/api/v1/questions/{dummy_id}/attempt",
            json={"selected_option_id": dummy_id, "time_spent_seconds": 10},
        )
        assert res2.status_code == 401
