from backend.app.core.config import Settings


def test_config_defaults():
    settings = Settings()
    assert settings.APP_NAME == "SAT MASTER API"
    assert settings.APP_VERSION == "0.1.0"
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_cors_origins_parsing():
    settings = Settings(CORS_ORIGINS="http://localhost:3000, https://satmaster.app")
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://satmaster.app"]
