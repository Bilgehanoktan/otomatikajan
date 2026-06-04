import os
import secrets

class Settings:
    @property
    def BILGEAPI_PORT(self) -> int:
        return int(os.getenv("BILGEAPI_PORT", "8100"))

    @BILGEAPI_PORT.setter
    def BILGEAPI_PORT(self, value):
        os.environ["BILGEAPI_PORT"] = str(value)

    @property
    def BILGEAPI_AUTH_MODE(self) -> str:
        return os.getenv("BILGEAPI_AUTH_MODE", "disabled").lower()

    @BILGEAPI_AUTH_MODE.setter
    def BILGEAPI_AUTH_MODE(self, value):
        os.environ["BILGEAPI_AUTH_MODE"] = str(value)

    @property
    def BILGEAPI_DATABASE_URL(self) -> str:
        return os.getenv("BILGEAPI_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/bilgeapi")

    @BILGEAPI_DATABASE_URL.setter
    def BILGEAPI_DATABASE_URL(self, value):
        os.environ["BILGEAPI_DATABASE_URL"] = str(value)

    @property
    def BILGEAPI_STATIC_KEYS(self):
        raw_keys = os.getenv("BILGEAPI_STATIC_KEYS", "")
        return [k.strip() for k in raw_keys.split(",") if k.strip()]

    @BILGEAPI_STATIC_KEYS.setter
    def BILGEAPI_STATIC_KEYS(self, value):
        if isinstance(value, list):
            os.environ["BILGEAPI_STATIC_KEYS"] = ",".join(value)
        else:
            os.environ["BILGEAPI_STATIC_KEYS"] = str(value)

    @property
    def BILGEAPI_JWT_SECRET(self) -> str:
        secret = os.getenv("BILGEAPI_JWT_SECRET", os.getenv("JWT_SECRET", ""))
        if not secret:
            if not hasattr(self, "_jwt_fallback_secret"):
                self._jwt_fallback_secret = secrets.token_hex(64)
            return self._jwt_fallback_secret
        return secret

    @BILGEAPI_JWT_SECRET.setter
    def BILGEAPI_JWT_SECRET(self, value):
        os.environ["BILGEAPI_JWT_SECRET"] = str(value)

    @property
    def BILGEAPI_RATE_LIMIT_RPS(self) -> int:
        return int(os.getenv("BILGEAPI_RATE_LIMIT_RPS", "10"))

    @BILGEAPI_RATE_LIMIT_RPS.setter
    def BILGEAPI_RATE_LIMIT_RPS(self, value):
        os.environ["BILGEAPI_RATE_LIMIT_RPS"] = str(value)

    @property
    def BILGEAPI_MAX_CONTENT_LENGTH(self) -> int:
        return int(os.getenv("BILGEAPI_MAX_CONTENT_LENGTH", "1048576"))

    @BILGEAPI_MAX_CONTENT_LENGTH.setter
    def BILGEAPI_MAX_CONTENT_LENGTH(self, value):
        os.environ["BILGEAPI_MAX_CONTENT_LENGTH"] = str(value)

    @property
    def BILGEAPI_CORS_ALLOWLIST(self):
        raw_cors = os.getenv("BILGEAPI_CORS_ALLOWLIST", "")
        allowlist = [o.strip() for o in raw_cors.split(",") if o.strip()]
        return allowlist if allowlist else ["*"]

    @BILGEAPI_CORS_ALLOWLIST.setter
    def BILGEAPI_CORS_ALLOWLIST(self, value):
        if isinstance(value, list):
            os.environ["BILGEAPI_CORS_ALLOWLIST"] = ",".join(value)
        else:
            os.environ["BILGEAPI_CORS_ALLOWLIST"] = str(value)

    @property
    def APP_ENV(self) -> str:
        return os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()

    @property
    def BILGEAPI_WEBHOOK_SECRET(self) -> str:
        secret = os.getenv("BILGEAPI_WEBHOOK_SECRET", "webhook_secret")
        if self.APP_ENV == "production" and (not secret or secret == "webhook_secret"):
            raise RuntimeError("Production mode requires a secure and custom BILGEAPI_WEBHOOK_SECRET!")
        return secret

    @BILGEAPI_WEBHOOK_SECRET.setter
    def BILGEAPI_WEBHOOK_SECRET(self, value):
        os.environ["BILGEAPI_WEBHOOK_SECRET"] = str(value)

    @property
    def BILGEAPI_ALLOW_PRIVATE_WEBHOOKS(self) -> bool:
        if self.APP_ENV == "production":
            return False
        raw = os.getenv("BILGEAPI_ALLOW_PRIVATE_WEBHOOKS", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_ALLOW_PRIVATE_WEBHOOKS.setter
    def BILGEAPI_ALLOW_PRIVATE_WEBHOOKS(self, value):
        os.environ["BILGEAPI_ALLOW_PRIVATE_WEBHOOKS"] = str(value).lower()

    @property
    def BILGEAPI_WEBHOOK_TIMEOUT(self) -> int:
        return int(os.getenv("BILGEAPI_WEBHOOK_TIMEOUT", "5"))

    @BILGEAPI_WEBHOOK_TIMEOUT.setter
    def BILGEAPI_WEBHOOK_TIMEOUT(self, value):
        os.environ["BILGEAPI_WEBHOOK_TIMEOUT"] = str(value)

    @property
    def BILGEAPI_WEBHOOK_MAX_RETRIES(self) -> int:
        return int(os.getenv("BILGEAPI_WEBHOOK_MAX_RETRIES", "5"))

    @BILGEAPI_WEBHOOK_MAX_RETRIES.setter
    def BILGEAPI_WEBHOOK_MAX_RETRIES(self, value):
        os.environ["BILGEAPI_WEBHOOK_MAX_RETRIES"] = str(value)

    @property
    def BILGEAPI_WEBHOOK_BACKOFF_FACTOR(self) -> float:
        return float(os.getenv("BILGEAPI_WEBHOOK_BACKOFF_FACTOR", "2.0"))

    @BILGEAPI_WEBHOOK_BACKOFF_FACTOR.setter
    def BILGEAPI_WEBHOOK_BACKOFF_FACTOR(self, value):
        os.environ["BILGEAPI_WEBHOOK_BACKOFF_FACTOR"] = str(value)

    @property
    def BILGEAPI_WEBHOOK_URL(self) -> str:
        return os.getenv("BILGEAPI_WEBHOOK_URL", "")

    @BILGEAPI_WEBHOOK_URL.setter
    def BILGEAPI_WEBHOOK_URL(self, value):
        if value is None:
            if "BILGEAPI_WEBHOOK_URL" in os.environ:
                del os.environ["BILGEAPI_WEBHOOK_URL"]
        else:
            os.environ["BILGEAPI_WEBHOOK_URL"] = str(value)

settings = Settings()

