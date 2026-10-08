"""Regression tests for Reading & Writing question flow and state consistency:
1. R&W selector returns subject == READING_WRITING.
2. Returned question contains valid options with exactly one correct option.
3. Question object is internally consistent with no Math-only requirements.
4. R&W attempt evaluation and anti-repetition cooldown integration.
"""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.enums import QuestionStatus, Subject
from backend.app.models.question import Question, QuestionOption
from backend.app.models.user import User
from backend.app.seed.questions import seed_questions
from backend.app.services.question_selector import (
    QuestionSelectionCriteria,
    QuestionSelectorService,
)


@pytest.fixture
async def seeded_db():
    async with async_session_factory() as session:
        await seed_questions(session)
    return True


@pytest.fixture
async def learner():
    users_to_delete = []

    async def _create(telegram_id: int, name: str) -> User:
        async with async_session_factory() as session:
            user = User(
                telegram_id=telegram_id,
                first_name=name,
                target_score=1450,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            users_to_delete.append(user.id)
            return user

    yield _create

    async with async_session_factory() as session:
        for uid in users_to_delete:
            u = await session.get(User, uid)
            if u:
                await session.delete(u)
        await session.commit()


@pytest.mark.asyncio
async def test_rw_selector_returns_subject_reading_writing(seeded_db, learner):
    """Verify that QuestionSelectorService selects strictly READING_WRITING questions."""
    user = await learner(991101, "RW_Tester_1")

    async with async_session_factory() as session:
        criteria = QuestionSelectionCriteria(
            subject=Subject.READING_WRITING.value,
            count=10,
        )
        selected = await QuestionSelectorService.select_questions(
            db=session,
            criteria=criteria,
            user_id=user.id,
        )

        assert len(selected) > 0
        for q in selected:
            assert q.subject == Subject.READING_WRITING.value
            assert q.status == QuestionStatus.PUBLISHED.value
            assert q.domain in [
                "INFORMATION_IDEAS",
                "CRAFT_STRUCTURE",
                "EXPRESSION_IDEAS",
                "STANDARD_ENGLISH_CONVENTIONS",
            ]


@pytest.mark.asyncio
async def test_rw_questions_contain_valid_options_and_correct_choice(seeded_db, learner):
    """Verify that all R&W questions have exactly 4 choices with one correct answer."""
    user = await learner(991102, "RW_Tester_2")

    async with async_session_factory() as session:
        criteria = QuestionSelectionCriteria(
            subject=Subject.READING_WRITING.value,
            count=20,
        )
        selected = await QuestionSelectorService.select_questions(
            db=session,
            criteria=criteria,
            user_id=user.id,
        )

        for q in selected:
            # Re-query options to verify database consistency
            opt_res = await session.execute(
                select(QuestionOption)
                .where(QuestionOption.question_id == q.id)
                .order_by(QuestionOption.order_index)
            )
            options = opt_res.scalars().all()
            assert len(options) == 4, f"Question {q.id} has {len(options)} options instead of 4"
            labels = [o.label for o in options]
            assert labels == ["A", "B", "C", "D"]
            correct_opts = [o for o in options if o.is_correct]
            assert len(correct_opts) == 1, f"Question {q.id} has {len(correct_opts)} correct options"
            for o in options:
                assert o.text.strip(), f"Empty option text in question {q.id}"


@pytest.mark.asyncio
async def test_rw_question_api_contract_and_no_math_leak(seeded_db, learner):
    """Verify the /api/v1/questions/random endpoint returns valid R&W question without Math assumptions."""
    user = await learner(991103, "RW_Tester_3")
    token = create_access_token(user_id=str(user.id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/questions/random?subject=READING_WRITING",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["subject"] == "READING_WRITING"
        assert len(data["question_text"]) > 10
        assert len(data["options"]) == 4
        # Verify no answer key leakage
        for opt in data["options"]:
            assert "is_correct" not in opt
            assert opt["text"]
            assert opt["label"] in ["A", "B", "C", "D"]
        # Desmos allowed should be False for R&W questions
        assert data["desmos_allowed"] is False
        assert data["desmos_recommended"] is False


@pytest.mark.asyncio
async def test_rw_attempt_submission_and_anti_repetition_cycle(seeded_db, learner):
    """Verify that submitting an attempt on an R&W question records history and deprioritizes it."""
    user = await learner(991104, "RW_Tester_4")
    token = create_access_token(user_id=str(user.id))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch first question
        q1_resp = await client.get(
            "/api/v1/questions/random?subject=READING_WRITING",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert q1_resp.status_code == 200
        q1 = q1_resp.json()
        q1_id = q1["id"]
        option_id = q1["options"][0]["id"]

        # 2. Submit attempt
        sub_resp = await client.post(
            f"/api/v1/questions/{q1_id}/attempt",
            headers={"Authorization": f"Bearer {token}"},
            json={"selected_option_id": option_id, "time_spent_seconds": 45},
        )
        assert sub_resp.status_code == 200
        sub_data = sub_resp.json()
        assert "is_correct" in sub_data
        assert "explanation" in sub_data
        assert len(sub_data["explanation"]) > 0

        # 3. Next random question should prioritize unseen questions
        q2_resp = await client.get(
            "/api/v1/questions/random?subject=READING_WRITING",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert q2_resp.status_code == 200
        q2 = q2_resp.json()
        # Since bank has 24 R&W questions and only 1 is seen, q2 must NOT be q1
        assert q2["id"] != q1_id, "Recently seen question was served again immediately!"
        assert q2["question_text"] != q1["question_text"]
