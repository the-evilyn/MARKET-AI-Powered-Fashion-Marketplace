from app.core.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.APP_NAME == "AI Fashion Marketplace"
    assert settings.PORT == 8000
    assert settings.JWT_ALGORITHM == "HS256"
    assert len(settings.CORS_ORIGINS) > 0


def test_cors_origins_json_parsing():
    settings = Settings(CORS_ORIGINS='["http://example.com", "http://test.com"]')
    assert "http://example.com" in settings.CORS_ORIGINS
    assert "http://test.com" in settings.CORS_ORIGINS


def test_cors_origins_comma_separated():
    settings = Settings(CORS_ORIGINS="http://foo.com, http://bar.com")
    assert "http://foo.com" in settings.CORS_ORIGINS
    assert "http://bar.com" in settings.CORS_ORIGINS
