"""Tests for BilgeAPI startup validation module."""
import os
import pytest
from apps.bilgeapi.config import settings
from apps.bilgeapi.startup import validate_production_config, StartupValidationError


# Keys that startup validation reads
_STARTUP_KEYS = [
    "APP_ENV", "ENVIRONMENT",
    "BILGEAPI_JWT_SECRET", "JWT_SECRET",
    "BILGEAPI_WEBHOOK_SECRET",
    "BILGEAPI_DATABASE_URL", "DATABASE_URL",
    "BILGEAPI_AUTH_MODE",
    "BILGEAPI_CORS_ALLOWLIST",
]


@pytest.fixture(autouse=True)
def _isolate_startup_env():
    """Save and restore all startup-related env vars to prevent cross-test contamination."""
    saved = {k: os.environ.get(k) for k in _STARTUP_KEYS}
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _clean_env():
    """Remove all BilgeAPI startup env vars for a clean test."""
    for k in _STARTUP_KEYS:
        os.environ.pop(k, None)


class TestStartupValidation:
    """Test startup validation logic."""

    def test_settings_default_auth_mode_is_api_key_outside_test_env(self):
        """Config defaults to api_key unless test env explicitly disables auth."""
        _clean_env()
        os.environ["APP_ENV"] = "development"

        assert settings.BILGEAPI_AUTH_MODE == "api_key"

    def test_settings_default_auth_mode_is_disabled_in_test_env(self):
        """Unit test env keeps explicit disabled default for isolated tests."""
        _clean_env()
        os.environ["APP_ENV"] = "test"

        assert settings.BILGEAPI_AUTH_MODE == "disabled"

    def test_settings_default_cors_allowlist_is_localhost_only(self):
        """Fallback CORS policy should be restricted to local control-plane origins."""
        _clean_env()

        assert settings.BILGEAPI_CORS_ALLOWLIST == [
            "http://127.0.0.1:3100",
            "http://localhost:3100",
        ]

    def test_development_mode_passes_with_defaults(self):
        """In development mode, default/missing values produce warnings but no error."""
        _clean_env()
        os.environ["APP_ENV"] = "development"
        warnings = validate_production_config()
        assert isinstance(warnings, list)
        # Should have warning about default webhook secret
        assert any("BILGEAPI_WEBHOOK_SECRET" in w for w in warnings)

    def test_development_mode_no_warnings_when_configured(self):
        """In development mode with all secrets set, no warnings."""
        _clean_env()
        os.environ["APP_ENV"] = "development"
        os.environ["BILGEAPI_JWT_SECRET"] = "test-secret-long-enough"
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "custom-webhook-secret"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        warnings = validate_production_config()
        assert len(warnings) == 0

    def test_production_fails_without_jwt_secret_in_jwt_mode(self):
        """Production mode raises error when JWT secret is missing and auth_mode is 'jwt'."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "jwt"
        with pytest.raises(StartupValidationError, match="BILGEAPI_JWT_SECRET"):
            validate_production_config()

    def test_production_passes_without_jwt_secret_in_api_key_mode(self):
        """Production mode passes without JWT secret when auth_mode is 'api_key'."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        os.environ["BILGEAPI_CORS_ALLOWLIST"] = "https://app.example.com"
        warnings = validate_production_config()
        # Should pass — JWT secret is not required in api_key mode
        assert not any("JWT" in w for w in warnings)

    def test_production_fails_with_default_webhook_secret(self):
        """Production mode raises error when webhook secret is default."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "webhook_secret"  # default!
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        with pytest.raises(StartupValidationError, match="BILGEAPI_WEBHOOK_SECRET"):
            validate_production_config()

    def test_production_fails_with_localhost_db(self):
        """Production mode raises error when DATABASE_URL points to localhost."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        with pytest.raises(StartupValidationError, match="localhost"):
            validate_production_config()

    def test_production_fails_with_disabled_auth(self):
        """Production mode raises error when auth is disabled."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "disabled"
        with pytest.raises(StartupValidationError, match="BILGEAPI_AUTH_MODE"):
            validate_production_config()

    def test_production_passes_with_all_configured(self):
        """Production mode passes when all secrets and config are properly set."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret-unique"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        os.environ["BILGEAPI_CORS_ALLOWLIST"] = "https://app.example.com"
        warnings = validate_production_config()
        assert len(warnings) == 0

    def test_production_warns_on_wildcard_cors(self):
        """Production mode warns when CORS allowlist is wildcard."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret-unique"
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        os.environ["BILGEAPI_CORS_ALLOWLIST"] = "*"
        warnings = validate_production_config()
        assert any("CORS" in w for w in warnings)

    def test_bilgeapi_database_url_takes_precedence(self):
        """BILGEAPI_DATABASE_URL is checked before DATABASE_URL."""
        _clean_env()
        os.environ["APP_ENV"] = "production"
        os.environ["BILGEAPI_JWT_SECRET"] = "a" * 64
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = "prod-webhook-secret-unique"
        os.environ["BILGEAPI_DATABASE_URL"] = "postgresql+asyncpg://user:pass@db-host:5432/bilgeapi"
        os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
        os.environ["BILGEAPI_CORS_ALLOWLIST"] = "https://app.example.com"
        # Even without DATABASE_URL, BILGEAPI_DATABASE_URL should suffice
        warnings = validate_production_config()
        assert len(warnings) == 0
