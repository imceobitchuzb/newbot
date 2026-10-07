import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.database import async_session_factory
from backend.app.core.math_taxonomy import (
    CANONICAL_MATH_DOMAINS,
    calculate_mastery_level,
    normalize_skill,
)
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.enums import (
    Difficulty,
    MathDomain,
    MathPracticeSessionStatus,
    SkillMasteryLevel,
    Subject,
)
from backend.app.models.math_practice import MathPracticeSession
from backend.app.models.user import User
from backend.app.seed.questions import SEED_QUESTIONS_DATA, seed_questions


@pytest.mark.asyncio
async def test_math_question_bank_quality_and_coverage():
    """Verify that question bank contains at least 80 Math questions with high quality and balance."""
    math_questions = [q for q in SEED_QUESTIONS_DATA if q["subject"] == Subject.MATH.value]
    assert len(math_questions) >= 80, f"Expected at least 80 math questions, found {len(math_questions)}"

    # Check domain distribution
    domains = [q["domain"] for q in math_questions]
    for dom in MathDomain:
        dom_count = sum(1 for d in domains if d == dom.value)
        assert dom_count >= 20, f"Domain {dom.value} has only {dom_count} questions, expected >= 20"

    # Check options integrity and explanations
    for q in math_questions:
        assert len(q["options"]) == 4, f"Question missing 4 options: {q['question_text'][:30]}"
        labels = [opt["label"] for opt in q["options"]]
        assert sorted(labels) == ["A", "B", "C", "D"]
        correct_count = sum(1 for opt in q["options"] if opt["is_correct"])
        assert correct_count == 1, f"Question has {correct_count} correct options: {q['question_text'][:30]}"
        assert len(q["explanation"].strip()) > 10, f"Question has insufficient explanation"
        assert q["difficulty"] in [Difficulty.EASY.value, Difficulty.MEDIUM.value, Difficulty.HARD.value]


@pytest.mark.asyncio
async def test_math_taxonomy_and_mastery():
    """Verify canonical taxonomy normalization and mastery calculation."""
    # Test normalization
    assert normalize_skill("systems of two linear equations") == "Systems of linear equations"
    assert normalize_skill("quadratic equations & factoring") == "Quadratic equations"
    assert normalize_skill("Percentages") == "Percentages"

    # Test mastery calculation
    assert calculate_mastery_level(0, 0.0) == SkillMasteryLevel.NOT_STARTED
    assert calculate_mastery_level(3, 0.33) == SkillMasteryLevel.LEARNING
    assert calculate_mastery_level(1, 1.0) == SkillMasteryLevel.PRACTICING
    assert calculate_mastery_level(3, 0.67) == SkillMasteryLevel.PRACTICING
    assert calculate_mastery_level(2, 0.85) == SkillMasteryLevel.STRONG
    assert calculate_mastery_level(5, 1.0) == SkillMasteryLevel.STRONG


@pytest.mark.asyncio
async def test_practice_session_lifecycle_and_security():
    """Test starting, resuming, answering questions, security guards, and completion of practice session."""
    async with async_session_factory() as session:
        # Seed questions
        await seed_questions(session)

        uid1 = int(uuid.uuid4().int % 1000000000)
        uid2 = int(uuid.uuid4().int % 1000000000)
        user1 = User(
            telegram_id=uid1,
            username=f"math_prodigy_{uid1}",
            first_name="Ada",
            is_active=True,
        )
        user2 = User(
            telegram_id=uid2,
            username=f"other_user_{uid2}",
            first_name="Charles",
            is_active=True,
        )
        session.add_all([user1, user2])
        await session.commit()
        await session.refresh(user1)
        await session.refresh(user2)

    token1 = create_access_token(user1.id)
    token2 = create_access_token(user2.id)
    auth_headers1 = {"Authorization": f"Bearer {token1}"}
    auth_headers2 = {"Authorization": f"Bearer {token2}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Start a 5-question Algebra practice session
        start_payload = {
            "domain": MathDomain.ALGEBRA.value,
            "difficulty": Difficulty.EASY.value,
            "question_count": 5,
        }
        res = await client.post("/api/v1/math/practice", json=start_payload, headers=auth_headers1)
        assert res.status_code == 200
        session_data = res.json()
        session_id = session_data["id"]
        assert session_data["status"] == MathPracticeSessionStatus.IN_PROGRESS.value
        assert session_data["total_questions"] == 5
        assert len(session_data["questions"]) == 5

        # 2. Anti-leak test: verify no answers or explanations are revealed before answering
        for q in session_data["questions"]:
            assert q["explanation"] is None
            assert q["hint"] is None
            assert q["sat_shortcut"] is None
            assert q["correct_option_id"] is None
            for opt in q["options"]:
                assert "is_correct" not in opt

        # 3. Test get /math/practice/current
        curr_res = await client.get("/api/v1/math/practice/current", headers=auth_headers1)
        assert curr_res.status_code == 200
        assert curr_res.json()["id"] == session_id

        # 4. Resume behavior: starting with same params returns existing active session
        resume_res = await client.post("/api/v1/math/practice", json=start_payload, headers=auth_headers1)
        assert resume_res.status_code == 200
        assert resume_res.json()["id"] == session_id

        # 5. Cross-user security: user 2 cannot view or answer user 1's session
        first_q = session_data["questions"][0]
        q_id = first_q["practice_question_id"]
        chosen_opt_id = first_q["options"][0]["id"]

        cross_res = await client.get(f"/api/v1/math/practice/{session_id}", headers=auth_headers2)
        assert cross_res.status_code == 404

        cross_ans = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q_id}/answer",
            json={"selected_option_id": chosen_opt_id, "time_spent_seconds": 25},
            headers=auth_headers2,
        )
        assert cross_ans.status_code == 404

        # 6. Cross-question option tampering protection
        other_q = session_data["questions"][1]
        invalid_opt_id = other_q["options"][0]["id"]
        tamper_res = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q_id}/answer",
            json={"selected_option_id": invalid_opt_id, "time_spent_seconds": 30},
            headers=auth_headers1,
        )
        assert tamper_res.status_code == 422

        # 7. Answer the first question legitimately
        ans_res = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q_id}/answer",
            json={"selected_option_id": chosen_opt_id, "time_spent_seconds": 45},
            headers=auth_headers1,
        )
        assert ans_res.status_code == 200
        ans_data = ans_res.json()
        assert "is_correct" in ans_data
        assert "correct_option_id" in ans_data
        assert ans_data["explanation"] is not None
        assert ans_data["session_completed"] is False

        # 8. Duplicate answer rejection
        dup_res = await client.post(
            f"/api/v1/math/practice/{session_id}/questions/{q_id}/answer",
            json={"selected_option_id": chosen_opt_id, "time_spent_seconds": 10},
            headers=auth_headers1,
        )
        assert dup_res.status_code == 400

        # 9. Verify that fetched session now exposes explanation ONLY for the answered question
        updated_sess_res = await client.get(f"/api/v1/math/practice/{session_id}", headers=auth_headers1)
        updated_sess = updated_sess_res.json()
        q0 = updated_sess["questions"][0]
        q1 = updated_sess["questions"][1]
        assert q0["is_answered"] is True
        assert q0["explanation"] is not None
        assert q1["is_answered"] is False
        assert q1["explanation"] is None

        # 10. Complete the rest of the questions
        for remaining_q in updated_sess["questions"][1:]:
            ans_res = await client.post(
                f"/api/v1/math/practice/{session_id}/questions/{remaining_q['practice_question_id']}/answer",
                json={"selected_option_id": remaining_q["options"][0]["id"], "time_spent_seconds": 30},
                headers=auth_headers1,
            )
            assert ans_res.status_code == 200

        # 11. Verify session result endpoint
        result_res = await client.get(f"/api/v1/math/practice/{session_id}/result", headers=auth_headers1)
        assert result_res.status_code == 200
        result_data = result_res.json()
        assert result_data["status"] == MathPracticeSessionStatus.COMPLETED.value
        assert result_data["total_questions"] == 5
        assert result_data["answered_questions"] == 5
        assert 0.0 <= result_data["accuracy_percentage"] <= 100.0
        assert MathDomain.ALGEBRA.value in result_data["domain_breakdown"]

        # 12. Check analytics endpoint
        analytics_res = await client.get("/api/v1/math/analytics", headers=auth_headers1)
        assert analytics_res.status_code == 200
        analytics_data = analytics_res.json()
        assert analytics_data["total_attempts"] == 5
        assert len(analytics_data["domains"]) == 4
        assert analytics_data["recommended_focus_skill"] is not None

        # 13. Check domain-specific analytics
        dom_res = await client.get("/api/v1/math/domains/ALGEBRA", headers=auth_headers1)
        assert dom_res.status_code == 200
        dom_data = dom_res.json()
        assert dom_data["domain"] == "ALGEBRA"
        assert dom_data["total_attempts"] == 5
        assert len(dom_data["skills"]) == len(CANONICAL_MATH_DOMAINS["ALGEBRA"]["skills"])
