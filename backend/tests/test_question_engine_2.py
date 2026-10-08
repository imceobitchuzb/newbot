"""Tests for SAT MASTER Question Engine 2.0:
Anti-repetition, adaptive weighting, randomized selection, history tracking, and parameterized generation.
"""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.core.database import async_session_factory
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.enums import Difficulty, QuestionStatus, Subject
from backend.app.models.question import Question, QuestionAttempt, QuestionOption
from backend.app.models.user import User
from backend.app.seed.questions import seed_questions
from backend.app.services.question_generator import LinearEquationTemplate
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
async def create_learner():
    users_to_delete = []

    async def _create(telegram_id: int, name: str) -> User:
        async with async_session_factory() as session:
            user = User(
                telegram_id=telegram_id,
                first_name=name,
                target_score=1400,
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
async def test_different_users_can_receive_different_questions(seeded_db, create_learner):
    """Verify that user history and randomization allow different users to receive different question sets."""
    user_a = await create_learner(998801, "StudentA")
    user_b = await create_learner(998802, "StudentB")

    async with async_session_factory() as session:
        # Give User A attempts on several algebra questions
        q_res = await session.execute(
            select(Question)
            .where(Question.subject == Subject.MATH.value, Question.domain == "ALGEBRA")
            .limit(3)
        )
        questions_seen_by_a = list(q_res.scalars().all())

        for q in questions_seen_by_a:
            opt = q.options[0]
            att = QuestionAttempt(
                user_id=user_a.id,
                question_id=q.id,
                selected_option_id=opt.id,
                is_correct=True,
                time_spent_seconds=40,
            )
            session.add(att)
        await session.commit()

        # Both users request 3 algebra questions
        criteria = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            domain="ALGEBRA",
            count=3,
            avoid_recently_seen=True,
            prefer_unseen=True,
        )
        selected_for_a = await QuestionSelectorService.select_questions(session, criteria, user_id=user_a.id)
        selected_for_b = await QuestionSelectorService.select_questions(session, criteria, user_id=user_b.id)

        ids_a = {q.id for q in selected_for_a}
        ids_b = {q.id for q in selected_for_b}

        # User A should NOT get the 3 questions they just answered
        seen_ids = {q.id for q in questions_seen_by_a}
        assert not ids_a.issubset(seen_ids), "User A received already answered questions despite available unseen pool"
        # User A and User B received distinct sets
        assert ids_a != ids_b


@pytest.mark.asyncio
async def test_anti_repetition_same_user_deprioritizes_seen(seeded_db, create_learner):
    """Verify that a user who has answered questions does not repeatedly get the exact same questions."""
    user = await create_learner(998803, "StudentRepeat")

    async with async_session_factory() as session:
        # 1. First selection for user
        criteria = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            domain="ALGEBRA",
            count=2,
            avoid_recently_seen=True,
            prefer_unseen=True,
            seed=42,
        )
        first_batch = await QuestionSelectorService.select_questions(session, criteria, user_id=user.id)
        assert len(first_batch) == 2
        first_ids = {q.id for q in first_batch}

        # 2. Record attempts for first batch
        for q in first_batch:
            session.add(
                QuestionAttempt(
                    user_id=user.id,
                    question_id=q.id,
                    selected_option_id=q.options[0].id,
                    is_correct=True,
                    time_spent_seconds=45,
                )
            )
        await session.commit()

        # 3. Second selection for same user
        second_batch = await QuestionSelectorService.select_questions(session, criteria, user_id=user.id)
        second_ids = {q.id for q in second_batch}

        # The second batch must prefer unseen questions over the freshly answered ones
        assert not second_ids.issubset(first_ids), "User repeatedly received identical questions without anti-repetition"


@pytest.mark.asyncio
async def test_recently_seen_cooldown_penalty(seeded_db, create_learner):
    """Verify that recent cooldown questions receive severe score penalties."""
    user = await create_learner(998804, "StudentCooldown")

    async with async_session_factory() as session:
        # Fetch 2 questions from Geometry
        q_res = await session.execute(
            select(Question)
            .where(Question.subject == Subject.MATH.value, Question.domain == "GEOMETRY_TRIGONOMETRY")
            .limit(2)
        )
        geom_qs = list(q_res.scalars().all())
        q_seen = geom_qs[0]

        # Log attempt for q_seen
        session.add(
            QuestionAttempt(
                user_id=user.id,
                question_id=q_seen.id,
                selected_option_id=q_seen.options[0].id,
                is_correct=True,
                time_spent_seconds=30,
            )
        )
        await session.commit()

        # Select 1 question from Geometry
        criteria = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            domain="GEOMETRY_TRIGONOMETRY",
            count=1,
            avoid_recently_seen=True,
            prefer_unseen=True,
        )
        picked = await QuestionSelectorService.select_single_question(session, criteria, user_id=user.id)
        assert picked is not None
        assert picked.id != q_seen.id, "Recently seen question was not deprioritized"


@pytest.mark.asyncio
async def test_weak_skills_receive_higher_priority(seeded_db, create_learner):
    """Verify that questions from skills where the user struggles are prioritized."""
    user = await create_learner(998805, "StudentWeakSkills")

    async with async_session_factory() as session:
        # Create incorrect attempts in 'Linear equations in one variable' (making it a weak skill)
        q_weak_res = await session.execute(
            select(Question)
            .where(Question.skill == "Linear equations in one variable")
            .limit(2)
        )
        weak_qs = list(q_weak_res.scalars().all())
        for q in weak_qs:
            session.add(
                QuestionAttempt(
                    user_id=user.id,
                    question_id=q.id,
                    selected_option_id=q.options[0].id,
                    is_correct=False,
                    time_spent_seconds=60,
                )
            )

        # Create correct attempts in 'Circles' (making it a strong/mastered skill)
        q_strong_res = await session.execute(
            select(Question).where(Question.skill == "Circles").limit(3)
        )
        strong_qs = list(q_strong_res.scalars().all())
        for q in strong_qs:
            session.add(
                QuestionAttempt(
                    user_id=user.id,
                    question_id=q.id,
                    selected_option_id=q.options[0].id,
                    is_correct=True,
                    time_spent_seconds=30,
                )
            )
        await session.commit()

        history = await QuestionSelectorService.get_user_history_snapshot(session, user.id)
        assert "Linear equations in one variable" in history.weak_skills
        assert "Circles" in history.mastered_skills

        # When selecting Math practice with prefer_weak_skills=True
        criteria = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            count=3,
            prefer_weak_skills=True,
            avoid_recently_seen=False,  # allow remediation
        )
        selected = await QuestionSelectorService.select_questions(session, criteria, user_id=user.id)
        skills = [q.skill for q in selected]
        assert "Linear equations in one variable" in skills


@pytest.mark.asyncio
async def test_difficulty_filtering_and_distribution(seeded_db):
    """Verify that target difficulty filtering is strictly respected."""
    async with async_session_factory() as session:
        # Hard filter
        crit_hard = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            difficulty=Difficulty.HARD.value,
            count=5,
        )
        hard_qs = await QuestionSelectorService.select_questions(session, crit_hard)
        assert len(hard_qs) > 0
        assert all(q.difficulty == Difficulty.HARD.value for q in hard_qs)

        # Easy filter
        crit_easy = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            difficulty=Difficulty.EASY.value,
            count=5,
        )
        easy_qs = await QuestionSelectorService.select_questions(session, crit_easy)
        assert len(easy_qs) > 0
        assert all(q.difficulty == Difficulty.EASY.value for q in easy_qs)


@pytest.mark.asyncio
async def test_section_filtering_math_and_rw(seeded_db):
    """Verify that subject filtering cleanly separates Math and Reading & Writing."""
    async with async_session_factory() as session:
        crit_math = QuestionSelectionCriteria(subject=Subject.MATH.value, count=10)
        math_qs = await QuestionSelectorService.select_questions(session, crit_math)
        assert len(math_qs) == 10
        assert all(q.subject == Subject.MATH.value for q in math_qs)

        crit_rw = QuestionSelectionCriteria(subject=Subject.READING_WRITING.value, count=10)
        rw_qs = await QuestionSelectorService.select_questions(session, crit_rw)
        assert len(rw_qs) == 10
        assert all(q.subject == Subject.READING_WRITING.value for q in rw_qs)


@pytest.mark.asyncio
async def test_small_pools_fail_gracefully(seeded_db):
    """Verify that requesting more questions than available in a narrow slice degrades gracefully without error."""
    async with async_session_factory() as session:
        # Request 100 questions from a skill with only 2-3 questions
        criteria = QuestionSelectionCriteria(
            subject=Subject.MATH.value,
            skill="Linear inequalities",
            count=100,
        )
        selected = await QuestionSelectorService.select_questions(session, criteria)
        assert len(selected) > 0
        assert len(selected) < 100  # returns all available gracefully

        # Request with impossible subject
        empty_criteria = QuestionSelectionCriteria(
            subject="NONEXISTENT_SUBJECT",
            count=5,
        )
        empty_selected = await QuestionSelectorService.select_questions(session, empty_criteria)
        assert empty_selected == []


@pytest.mark.asyncio
async def test_deterministic_seed_for_reproducible_selection(seeded_db):
    """Verify that providing seed=123 yields identical deterministic question ordering."""
    async with async_session_factory() as session:
        criteria1 = QuestionSelectionCriteria(subject=Subject.MATH.value, count=5, seed=123)
        res1 = await QuestionSelectorService.select_questions(session, criteria1)

        criteria2 = QuestionSelectionCriteria(subject=Subject.MATH.value, count=5, seed=123)
        res2 = await QuestionSelectorService.select_questions(session, criteria2)

        ids1 = [q.id for q in res1]
        ids2 = [q.id for q in res2]
        assert ids1 == ids2, "Deterministic seed did not produce identical question order"


@pytest.mark.asyncio
async def test_production_selection_is_randomized(seeded_db):
    """Verify that without a fixed seed, selection exhibits natural randomized entropy."""
    async with async_session_factory() as session:
        distinct_orderings = set()
        for _ in range(5):
            crit = QuestionSelectionCriteria(subject=Subject.MATH.value, count=5, seed=None)
            res = await QuestionSelectorService.select_questions(session, crit)
            order = tuple(q.id for q in res)
            distinct_orderings.add(order)

        # Over 5 random selections from a pool of 85 math questions, at least 2 distinct orders should occur
        assert len(distinct_orderings) >= 2, "Production selection lacks randomized entropy"


@pytest.mark.asyncio
async def test_api_backward_compatibility(seeded_db, create_learner):
    """Verify existing GET /api/v1/questions and GET /api/v1/questions/random maintain exact response schema."""
    user = await create_learner(998806, "ApiCompatUser")
    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. List questions
        res_list = await client.get("/api/v1/questions?limit=5", headers=headers)
        assert res_list.status_code == 200
        items = res_list.json()
        assert len(items) == 5
        for item in items:
            assert "id" in item
            assert "subject" in item
            assert "domain" in item
            assert "skill" in item
            assert "difficulty" in item
            assert "options" in item
            assert "is_correct" not in item  # no leak

        # 2. Random question
        res_rand = await client.get("/api/v1/questions/random?subject=MATH", headers=headers)
        assert res_rand.status_code == 200
        rand_item = res_rand.json()
        assert rand_item["subject"] == "MATH"
        assert len(rand_item["options"]) == 4


def test_parameterized_question_generator_template():
    """Verify future generator template interface produces valid, verified question variants."""
    template = LinearEquationTemplate()
    assert template.template_id == "math_algebra_linear_001"
    assert template.subject == "MATH"

    # Generate 10 variants with distinct seeds
    for seed in range(10):
        variant = template.generate_variant(seed=seed)
        val_result = template.validate_variant(variant)
        assert val_result.is_valid, f"Variant validation failed: {val_result.errors}"
        assert len(variant.options) == 4
        assert sum(1 for o in variant.options if o.is_correct) == 1
        assert "If $" in variant.question_text
        assert variant.metadata["target_value"] is not None
