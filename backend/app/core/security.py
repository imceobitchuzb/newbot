from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl
import jwt
from backend.app.core.config import settings


class TelegramAuthError(Exception):
    """Base exception for Telegram authentication failures."""
    pass


class InvalidSignatureError(TelegramAuthError):
    """Raised when HMAC signature fails verification."""
    pass


class AuthDateExpiredError(TelegramAuthError):
    """Raised when initData auth_date exceeds maximum allowed age."""
    pass


class MalformedInitDataError(TelegramAuthError):
    """Raised when initData string format is invalid."""
    pass


class TokenAuthError(Exception):
    """Base exception for JWT authentication failures."""
    pass


class InvalidTokenError(TokenAuthError):
    pass


class TokenExpiredError(TokenAuthError):
    pass


def validate_telegram_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> Dict[str, Any]:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256 per Telegram specification.
    
    1. Parse raw query string.
    2. Extract 'hash' and exclude it from verification string.
    3. Sort remaining key=value pairs alphabetically and join with '\n'.
    4. Compute secret_key = HMAC_SHA256("WebAppData", bot_token).
    5. Compute signature = HMAC_SHA256(secret_key, data_check_string).
    6. Compare signature with provided hash using constant-time comparison.
    7. Validate auth_date freshness.
    
    Returns the parsed dictionary including decoded user object.
    """
    if not init_data_raw or not isinstance(init_data_raw, str):
        raise MalformedInitDataError("initData string must be a non-empty string.")

    if not bot_token:
        raise TelegramAuthError("TELEGRAM_BOT_TOKEN is not configured.")

    try:
        parsed_items = dict(parse_qsl(init_data_raw, keep_blank_values=True))
    except Exception as e:
        raise MalformedInitDataError(f"Failed to parse initData: {str(e)}")

    if "hash" not in parsed_items:
        raise MalformedInitDataError("Missing required 'hash' in initData.")

    received_hash = parsed_items["hash"]

    # Filter out hash and sort parameters alphabetically
    data_check_pairs = [
        f"{k}={v}" for k, v in sorted(parsed_items.items()) if k != "hash"
    ]
    data_check_string = "\n".join(data_check_pairs)

    # HMAC-SHA256 secret key derivation
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    # Calculate expected hash
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash.lower(), received_hash.lower()):
        raise InvalidSignatureError("Telegram initData signature verification failed.")

    # Validate auth_date if present
    if "auth_date" in parsed_items:
        try:
            auth_timestamp = int(parsed_items["auth_date"])
            now = int(time.time())
            if max_age_seconds > 0 and (now - auth_timestamp) > max_age_seconds:
                raise AuthDateExpiredError(
                    f"initData auth_date expired ({now - auth_timestamp}s > {max_age_seconds}s limit)."
                )
        except ValueError:
            raise MalformedInitDataError("Invalid integer in auth_date field.")

    result: Dict[str, Any] = dict(parsed_items)

    # Parse nested user JSON if provided
    if "user" in result:
        try:
            result["user_data"] = json.loads(result["user"])
        except json.JSONDecodeError:
            pass

    return result


# --- Application JWT Security ---

JWT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token for an authenticated user.
    Only internal user_id is encoded in the subject claim.
    No secrets or sensitive user information are included.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=DEFAULT_ACCESS_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises TokenExpiredError or InvalidTokenError if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Access token has expired.")
    except jwt.PyJWTError as e:
        raise InvalidTokenError(f"Invalid access token: {str(e)}")
