import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
import pytest

from backend.app.core.security import (
    AuthDateExpiredError,
    InvalidSignatureError,
    MalformedInitDataError,
    validate_telegram_init_data,
)
from backend.app.services.telegram_auth import TelegramAuthService

TEST_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"


def generate_test_init_data(
    bot_token: str,
    user_dict: dict,
    auth_date: int,
    query_id: str = "AAHdF6IQAAAAAN0XohDhrOrc",
) -> str:
    """Generates a valid Telegram initData string with valid HMAC signature."""
    params = {
        "query_id": query_id,
        "user": json.dumps(user_dict, separators=(",", ":")),
        "auth_date": str(auth_date),
    }

    # Sort parameters alphabetically
    sorted_pairs = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(sorted_pairs)

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    sig = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    params["hash"] = sig
    return urlencode(params)


def test_valid_telegram_init_data():
    now = int(time.time())
    user_data = {
        "id": 987654321,
        "first_name": "Alex",
        "last_name": "Student",
        "username": "sat_achiever",
        "language_code": "en",
    }

    init_data = generate_test_init_data(TEST_BOT_TOKEN, user_data, auth_date=now)
    result = validate_telegram_init_data(init_data, TEST_BOT_TOKEN)

    assert result["hash"] is not None
    assert int(result["auth_date"]) == now
    assert result["user_data"]["id"] == 987654321
    assert result["user_data"]["first_name"] == "Alex"
    assert result["user_data"]["username"] == "sat_achiever"


def test_invalid_signature():
    now = int(time.time())
    user_data = {"id": 12345, "first_name": "Imposter"}
    init_data = generate_test_init_data(TEST_BOT_TOKEN, user_data, auth_date=now)

    # Tamper with the hash
    tampered_init_data = init_data[:-4] + "ffff"

    with pytest.raises(InvalidSignatureError):
        validate_telegram_init_data(tampered_init_data, TEST_BOT_TOKEN)


def test_expired_auth_date():
    two_days_ago = int(time.time()) - 172800  # 48 hours ago
    user_data = {"id": 12345, "first_name": "DelayedUser"}
    init_data = generate_test_init_data(TEST_BOT_TOKEN, user_data, auth_date=two_days_ago)

    with pytest.raises(AuthDateExpiredError):
        validate_telegram_init_data(init_data, TEST_BOT_TOKEN, max_age_seconds=86400)


def test_malformed_init_data():
    with pytest.raises(MalformedInitDataError):
        validate_telegram_init_data("", TEST_BOT_TOKEN)

    with pytest.raises(MalformedInitDataError):
        validate_telegram_init_data("query_id=123&user={}", TEST_BOT_TOKEN)


def test_telegram_auth_service():
    now = int(time.time())
    user_data = {
        "id": 555666777,
        "first_name": "Elena",
        "username": "elena_sat",
    }
    init_data = generate_test_init_data(TEST_BOT_TOKEN, user_data, auth_date=now)

    service = TelegramAuthService(bot_token=TEST_BOT_TOKEN)
    user_info = service.authenticate_init_data(init_data)

    assert user_info.id == 555666777
    assert user_info.first_name == "Elena"
    assert user_info.username == "elena_sat"
