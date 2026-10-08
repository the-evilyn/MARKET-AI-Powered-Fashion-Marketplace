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


def test_jwt_secret_development_default_allowed():
    settings = Settings(APP_ENV="development")
    assert settings.JWT_SECRET == "super_secret_jwt_signing_key_replace_in_production_min32chars"


def test_jwt_secret_empty_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="development", JWT_SECRET="")
    assert "JWT signing key must not be empty" in str(exc_info.value)


def test_jwt_secret_production_default_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="production")
    assert "Insecure default JWT signing key detected" in str(exc_info.value)


def test_jwt_secret_production_short_rejected():
    import pytest
    from pydantic import ValidationError

    secret_attempt = "short_secret_123"
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="production", JWT_SECRET=secret_attempt)
    err_msg = str(exc_info.value)
    assert "JWT signing key must be at least 32 characters long" in err_msg
    # Ensure secret is never printed in error message
    assert secret_attempt not in err_msg


def test_jwt_secret_production_valid_allowed():
    valid_secret = "a_very_secure_and_cryptographically_strong_production_key_12345"
    settings = Settings(APP_ENV="production", JWT_SECRET=valid_secret)
    assert settings.JWT_SECRET == valid_secret


def test_jwt_secret_staging_default_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="staging")
    assert "Insecure default JWT signing key detected" in str(exc_info.value)


def test_jwt_secret_staging_short_rejected():
    import pytest
    from pydantic import ValidationError

    secret_attempt = "short_staging_key"
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_ENV="staging", JWT_SECRET=secret_attempt)
    err_msg = str(exc_info.value)
    assert "JWT signing key must be at least 32 characters long" in err_msg
    assert secret_attempt not in err_msg


def test_jwt_secret_staging_valid_allowed():
    valid_secret = "a_very_secure_and_cryptographically_strong_staging_key_1234567"
    settings = Settings(APP_ENV="staging", JWT_SECRET=valid_secret)
    assert settings.JWT_SECRET == valid_secret

