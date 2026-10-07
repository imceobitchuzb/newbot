import json
import time
from urllib.parse import urlencode
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.tests.test_telegram_auth import generate_test_init_data


@pytest.fixture(autouse=True)
def ensure_bot_token():
    # Ensure settings has the bot token set
    original = settings.TELEGRAM_BOT_TOKEN
    settings.TELEGRAM_BOT_TOKEN = "8922080817:AAGXQJ1aYSVs7M_GPQK6DxTlwllJaY2--Aw"
    yield
    settings.TELEGRAM_BOT_TOKEN = original


@pytest.mark.asyncio
async def test_auth_endpoint_valid():
    now = int(time.time())
    tg_user = {
        "id": 111222333,
        "first_name": "Marcus",
        "last_name": "Aurelius",
        "username": "marcus_sat",
    }
    init_data = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user, auth_date=now)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": init_data},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["telegram_id"] == 111222333
        assert data["user"]["first_name"] == "Marcus"
        assert data["user"]["profile"]["target_score"] == 1400
        assert data["user"]["profile"]["diagnostic_status"] == "not_started"


@pytest.mark.asyncio
async def test_auth_endpoint_invalid_signature():
    now = int(time.time())
    tg_user = {"id": 111222333, "first_name": "Hacker"}
    init_data = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user, auth_date=now)
    tampered_init_data = init_data[:-4] + "dead"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": tampered_init_data},
        )
        assert response.status_code == 401
        assert "Invalid Telegram signature" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_endpoint_expired():
    two_days_ago = int(time.time()) - 172800
    tg_user = {"id": 111222333, "first_name": "OldSession"}
    init_data = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user, auth_date=two_days_ago)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": init_data},
        )
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_auth_endpoint_malformed():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty string
        res1 = await client.post("/api/v1/auth/telegram", json={"init_data": ""})
        assert res1.status_code == 422

        # Missing hash
        res2 = await client.post("/api/v1/auth/telegram", json={"init_data": "query_id=123&auth_date=123"})
        assert res2.status_code == 422


@pytest.mark.asyncio
async def test_new_user_created_and_existing_user_returned():
    now = int(time.time())
    unique_tg_id = 778899001
    tg_user = {
        "id": unique_tg_id,
        "first_name": "OriginalName",
        "username": "orig_user",
    }
    init_data1 = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user, auth_date=now)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. First launch -> creates user
        res1 = await client.post("/api/v1/auth/telegram", json={"init_data": init_data1})
        assert res1.status_code == 200
        user1 = res1.json()["user"]
        user_uuid = user1["id"]
        assert user1["telegram_id"] == unique_tg_id
        assert user1["first_name"] == "OriginalName"
        assert user1["profile"]["diagnostic_status"] == "not_started"

        # 2. Second launch with updated Telegram name -> returns same user, updates name
        tg_user_updated = {
            "id": unique_tg_id,
            "first_name": "UpdatedName",
            "username": "updated_user",
        }
        init_data2 = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user_updated, auth_date=now)
        res2 = await client.post("/api/v1/auth/telegram", json={"init_data": init_data2})
        assert res2.status_code == 200
        user2 = res2.json()["user"]

        # Ensure same user UUID (not duplicate)
        assert user2["id"] == user_uuid
        assert user2["telegram_id"] == unique_tg_id
        assert user2["first_name"] == "UpdatedName"
        assert user2["username"] == "updated_user"


@pytest.mark.asyncio
async def test_users_me_authenticated():
    now = int(time.time())
    tg_user = {"id": 44556677, "first_name": "TestStudent"}
    init_data = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, tg_user, auth_date=now)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        login_res = await client.post("/api/v1/auth/telegram", json={"init_data": init_data})
        token = login_res.json()["access_token"]

        # Request /users/me with valid Bearer token
        me_res = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["telegram_id"] == 44556677
        assert me_data["first_name"] == "TestStudent"
        assert me_data["profile"]["target_score"] == 1400


@pytest.mark.asyncio
async def test_users_me_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No header
        res1 = await client.get("/api/v1/users/me")
        assert res1.status_code == 401

        # Invalid token
        res2 = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert res2.status_code == 401


@pytest.mark.asyncio
async def test_security_forged_telegram_id_rejected():
    """
    Ensures that if an attacker generates a payload claiming to be another telegram_id
    without a valid HMAC signature derived from the bot token, it is rejected.
    """
    now = int(time.time())
    forged_user = {"id": 999999999, "first_name": "Attacker"}
    # Sign with a fake/wrong bot token
    fake_init_data = generate_test_init_data("fake_token:12345", forged_user, auth_date=now)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": fake_init_data},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_security_tampered_payload_rejected():
    """
    Tests modifying user object inside a signed payload invalidates HMAC.
    """
    now = int(time.time())
    user = {"id": 12345, "first_name": "HonestUser"}
    init_data = generate_test_init_data(settings.TELEGRAM_BOT_TOKEN, user, auth_date=now)

    # Replace user ID inside the encoded query string
    tampered = init_data.replace("12345", "99999")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/telegram",
            json={"init_data": tampered},
        )
        assert response.status_code == 401
