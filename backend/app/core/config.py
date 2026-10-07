import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "SAT MASTER API"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "sat-master-dev-secret-key-32chars-minimum-safe"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBAPP_URL: str = "https://001214c36c6783.lhr.life"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sat_master.db"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://127.0.0.1:3000"

    # AI Tutor
    AI_PROVIDER: str = "openai"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_BASE_URL: str = ""
    AI_MAX_TOKENS: int = 1500
    AI_TEMPERATURE: float = 0.3
    TUTOR_MAX_MESSAGES_PER_MINUTE: int = 10
    TUTOR_MAX_MESSAGES_PER_HOUR: int = 100
    TUTOR_MAX_MESSAGE_LENGTH: int = 4000
    TUTOR_SLIDING_WINDOW_SIZE: int = 12

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()
