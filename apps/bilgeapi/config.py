import os
import secrets
from typing import Optional
from enum import Enum

class AutonomyMode(str, Enum):
    OFF = "OFF"
    OBSERVE_ONLY = "OBSERVE_ONLY"
    DIAGNOSE_ONLY = "DIAGNOSE_ONLY"
    SAFE_AUTONOMY = "SAFE_AUTONOMY"
    SUPERVISED_AUTONOMY = "SUPERVISED_AUTONOMY"
    POLICY_BOUND_AUTONOMY = "POLICY_BOUND_AUTONOMY"

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
    def BILGEAPI_VERSION(self) -> str:
        return os.getenv("BILGEAPI_VERSION", "1.2.0")

    @BILGEAPI_VERSION.setter
    def BILGEAPI_VERSION(self, value):
        os.environ["BILGEAPI_VERSION"] = str(value)

    @property
    def BILGEAPI_AUTONOMY_MODE(self) -> str:
        mode = os.getenv("BILGEAPI_AUTONOMY_MODE", "").upper()
        if not mode:
            return "OBSERVE_ONLY" if self.APP_ENV == "production" else "SAFE_AUTONOMY"
        try:
            return AutonomyMode(mode).value
        except ValueError:
            return "OBSERVE_ONLY" if self.APP_ENV == "production" else "SAFE_AUTONOMY"

    @BILGEAPI_AUTONOMY_MODE.setter
    def BILGEAPI_AUTONOMY_MODE(self, value):
        os.environ["BILGEAPI_AUTONOMY_MODE"] = str(value).upper()

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

    # GitHub issue adapter configuration
    @property
    def BILGEAPI_GITHUB_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_GITHUB_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_GITHUB_ENABLED.setter
    def BILGEAPI_GITHUB_ENABLED(self, value):
        os.environ["BILGEAPI_GITHUB_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_GITHUB_TOKEN(self) -> Optional[str]:
        return os.getenv("BILGEAPI_GITHUB_TOKEN")

    @BILGEAPI_GITHUB_TOKEN.setter
    def BILGEAPI_GITHUB_TOKEN(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_GITHUB_TOKEN", None)
        else:
            os.environ["BILGEAPI_GITHUB_TOKEN"] = str(value)

    @property
    def BILGEAPI_GITHUB_OWNER(self) -> Optional[str]:
        return os.getenv("BILGEAPI_GITHUB_OWNER")

    @BILGEAPI_GITHUB_OWNER.setter
    def BILGEAPI_GITHUB_OWNER(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_GITHUB_OWNER", None)
        else:
            os.environ["BILGEAPI_GITHUB_OWNER"] = str(value)

    @property
    def BILGEAPI_GITHUB_REPO(self) -> Optional[str]:
        return os.getenv("BILGEAPI_GITHUB_REPO")

    @BILGEAPI_GITHUB_REPO.setter
    def BILGEAPI_GITHUB_REPO(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_GITHUB_REPO", None)
        else:
            os.environ["BILGEAPI_GITHUB_REPO"] = str(value)

    @property
    def BILGEAPI_GITHUB_LABELS(self) -> str:
        return os.getenv("BILGEAPI_GITHUB_LABELS", "bilgeapi,repair-request")

    @BILGEAPI_GITHUB_LABELS.setter
    def BILGEAPI_GITHUB_LABELS(self, value):
        os.environ["BILGEAPI_GITHUB_LABELS"] = str(value)

    # Jira adapter configuration
    @property
    def BILGEAPI_JIRA_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_JIRA_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_JIRA_ENABLED.setter
    def BILGEAPI_JIRA_ENABLED(self, value):
        os.environ["BILGEAPI_JIRA_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_JIRA_BASE_URL(self) -> Optional[str]:
        return os.getenv("BILGEAPI_JIRA_BASE_URL")

    @BILGEAPI_JIRA_BASE_URL.setter
    def BILGEAPI_JIRA_BASE_URL(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_JIRA_BASE_URL", None)
        else:
            os.environ["BILGEAPI_JIRA_BASE_URL"] = str(value)

    @property
    def BILGEAPI_JIRA_EMAIL(self) -> Optional[str]:
        return os.getenv("BILGEAPI_JIRA_EMAIL")

    @BILGEAPI_JIRA_EMAIL.setter
    def BILGEAPI_JIRA_EMAIL(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_JIRA_EMAIL", None)
        else:
            os.environ["BILGEAPI_JIRA_EMAIL"] = str(value)

    @property
    def BILGEAPI_JIRA_API_TOKEN(self) -> Optional[str]:
        return os.getenv("BILGEAPI_JIRA_API_TOKEN")

    @BILGEAPI_JIRA_API_TOKEN.setter
    def BILGEAPI_JIRA_API_TOKEN(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_JIRA_API_TOKEN", None)
        else:
            os.environ["BILGEAPI_JIRA_API_TOKEN"] = str(value)

    @property
    def BILGEAPI_JIRA_PROJECT_KEY(self) -> str:
        return os.getenv("BILGEAPI_JIRA_PROJECT_KEY", "OPS")

    @BILGEAPI_JIRA_PROJECT_KEY.setter
    def BILGEAPI_JIRA_PROJECT_KEY(self, value):
        os.environ["BILGEAPI_JIRA_PROJECT_KEY"] = str(value)

    @property
    def BILGEAPI_JIRA_ISSUE_TYPE(self) -> str:
        return os.getenv("BILGEAPI_JIRA_ISSUE_TYPE", "Task")

    @BILGEAPI_JIRA_ISSUE_TYPE.setter
    def BILGEAPI_JIRA_ISSUE_TYPE(self, value):
        os.environ["BILGEAPI_JIRA_ISSUE_TYPE"] = str(value)

    # Sovereign Repair Lab configuration
    @property
    def BILGEAPI_SOVEREIGN_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_SOVEREIGN_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_SOVEREIGN_ENABLED.setter
    def BILGEAPI_SOVEREIGN_ENABLED(self, value):
        os.environ["BILGEAPI_SOVEREIGN_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_SOVEREIGN_BASE_URL(self) -> Optional[str]:
        return os.getenv("BILGEAPI_SOVEREIGN_BASE_URL")

    @BILGEAPI_SOVEREIGN_BASE_URL.setter
    def BILGEAPI_SOVEREIGN_BASE_URL(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_SOVEREIGN_BASE_URL", None)
        else:
            os.environ["BILGEAPI_SOVEREIGN_BASE_URL"] = str(value)

    @property
    def BILGEAPI_SOVEREIGN_API_KEY(self) -> Optional[str]:
        return os.getenv("BILGEAPI_SOVEREIGN_API_KEY")

    @BILGEAPI_SOVEREIGN_API_KEY.setter
    def BILGEAPI_SOVEREIGN_API_KEY(self, value):
        if value is None:
            os.environ.pop("BILGEAPI_SOVEREIGN_API_KEY", None)
        else:
            os.environ["BILGEAPI_SOVEREIGN_API_KEY"] = str(value)

    @property
    def BILGEAPI_SOVEREIGN_DEFAULT_PROJECT(self) -> str:
        return os.getenv("BILGEAPI_SOVEREIGN_DEFAULT_PROJECT", "default")

    @BILGEAPI_SOVEREIGN_DEFAULT_PROJECT.setter
    def BILGEAPI_SOVEREIGN_DEFAULT_PROJECT(self, value):
        os.environ["BILGEAPI_SOVEREIGN_DEFAULT_PROJECT"] = str(value)

    @property
    def BILGEAPI_METRICS_PUBLIC(self) -> bool:
        raw = os.getenv("BILGEAPI_METRICS_PUBLIC", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_METRICS_PUBLIC.setter
    def BILGEAPI_METRICS_PUBLIC(self, value):
        os.environ["BILGEAPI_METRICS_PUBLIC"] = str(value).lower()

    @property
    def BILGEAPI_SHUTDOWN_TIMEOUT_S(self) -> float:
        return float(os.getenv("BILGEAPI_SHUTDOWN_TIMEOUT_S", "5.0"))

    @BILGEAPI_SHUTDOWN_TIMEOUT_S.setter
    def BILGEAPI_SHUTDOWN_TIMEOUT_S(self, value):
        os.environ["BILGEAPI_SHUTDOWN_TIMEOUT_S"] = str(value)

    @property
    def BILGEAPI_RELEASE_MIN_COVERAGE(self) -> float:
        return float(os.getenv("BILGEAPI_RELEASE_MIN_COVERAGE", "80.0"))

    @BILGEAPI_RELEASE_MIN_COVERAGE.setter
    def BILGEAPI_RELEASE_MIN_COVERAGE(self, value):
        os.environ["BILGEAPI_RELEASE_MIN_COVERAGE"] = str(value)

    @property
    def BILGEAPI_REDIS_URL(self) -> str:
        return os.getenv("BILGEAPI_REDIS_URL", "")

    @BILGEAPI_REDIS_URL.setter
    def BILGEAPI_REDIS_URL(self, value):
        os.environ["BILGEAPI_REDIS_URL"] = str(value)

    @property
    def BILGEAPI_STATIC_KEY_HASHES(self) -> list[str]:
        raw = os.getenv("BILGEAPI_STATIC_KEY_HASHES", "")
        return [k.strip() for k in raw.split(",") if k.strip()]

    @BILGEAPI_STATIC_KEY_HASHES.setter
    def BILGEAPI_STATIC_KEY_HASHES(self, value):
        if isinstance(value, list):
            os.environ["BILGEAPI_STATIC_KEY_HASHES"] = ",".join(value)
        else:
            os.environ["BILGEAPI_STATIC_KEY_HASHES"] = str(value)

    @property
    def BILGEAPI_JWT_SECRETS(self) -> list[str]:
        raw = os.getenv("BILGEAPI_JWT_SECRETS", "")
        secrets_list = [k.strip() for k in raw.split(",") if k.strip()]
        if not secrets_list:
            return [self.BILGEAPI_JWT_SECRET]
        return secrets_list

    @BILGEAPI_JWT_SECRETS.setter
    def BILGEAPI_JWT_SECRETS(self, value):
        if isinstance(value, list):
            os.environ["BILGEAPI_JWT_SECRETS"] = ",".join(value)
        else:
            os.environ["BILGEAPI_JWT_SECRETS"] = str(value)

    @property
    def BILGEAPI_DURABLE_QUEUE_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_DURABLE_QUEUE_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_DURABLE_QUEUE_ENABLED.setter
    def BILGEAPI_DURABLE_QUEUE_ENABLED(self, value):
        os.environ["BILGEAPI_DURABLE_QUEUE_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_SLACK_WEBHOOK_URL(self) -> str:
        return os.getenv("BILGEAPI_SLACK_WEBHOOK_URL", "")

    @BILGEAPI_SLACK_WEBHOOK_URL.setter
    def BILGEAPI_SLACK_WEBHOOK_URL(self, value):
        os.environ["BILGEAPI_SLACK_WEBHOOK_URL"] = str(value)

    @property
    def BILGEAPI_TEAMS_WEBHOOK_URL(self) -> str:
        return os.getenv("BILGEAPI_TEAMS_WEBHOOK_URL", "")

    @BILGEAPI_TEAMS_WEBHOOK_URL.setter
    def BILGEAPI_TEAMS_WEBHOOK_URL(self, value):
        os.environ["BILGEAPI_TEAMS_WEBHOOK_URL"] = str(value)

    @property
    def BILGEAPI_SEARCH_PROVIDER(self) -> str:
        return os.getenv("BILGEAPI_SEARCH_PROVIDER", "mock").lower()

    @BILGEAPI_SEARCH_PROVIDER.setter
    def BILGEAPI_SEARCH_PROVIDER(self, value):
        os.environ["BILGEAPI_SEARCH_PROVIDER"] = str(value)

    @property
    def BILGEAPI_SERPER_API_KEY(self) -> str:
        return os.getenv("BILGEAPI_SERPER_API_KEY", os.getenv("SERPER_API_KEY", ""))

    @BILGEAPI_SERPER_API_KEY.setter
    def BILGEAPI_SERPER_API_KEY(self, value):
        os.environ["BILGEAPI_SERPER_API_KEY"] = str(value)

    @property
    def BILGEAPI_PR_PROVIDER(self) -> str:
        return os.getenv("BILGEAPI_PR_PROVIDER", "mock").lower()

    @BILGEAPI_PR_PROVIDER.setter
    def BILGEAPI_PR_PROVIDER(self, value):
        os.environ["BILGEAPI_PR_PROVIDER"] = str(value)

    @property
    def BILGEAPI_GITHUB_TOKEN(self) -> str:
        return os.getenv("BILGEAPI_GITHUB_TOKEN", "")

    @BILGEAPI_GITHUB_TOKEN.setter
    def BILGEAPI_GITHUB_TOKEN(self, value):
        os.environ["BILGEAPI_GITHUB_TOKEN"] = str(value)

    @property
    def BILGEAPI_GITHUB_OWNER(self) -> str:
        return os.getenv("BILGEAPI_GITHUB_OWNER", "")

    @BILGEAPI_GITHUB_OWNER.setter
    def BILGEAPI_GITHUB_OWNER(self, value):
        os.environ["BILGEAPI_GITHUB_OWNER"] = str(value)

    @property
    def BILGEAPI_GITHUB_REPO(self) -> str:
        return os.getenv("BILGEAPI_GITHUB_REPO", "")

    @BILGEAPI_GITHUB_REPO.setter
    def BILGEAPI_GITHUB_REPO(self, value):
        os.environ["BILGEAPI_GITHUB_REPO"] = str(value)

    @property
    def BILGEAPI_GITHUB_BASE_BRANCH(self) -> str:
        return os.getenv("BILGEAPI_GITHUB_BASE_BRANCH", "main")

    @BILGEAPI_GITHUB_BASE_BRANCH.setter
    def BILGEAPI_GITHUB_BASE_BRANCH(self, value):
        os.environ["BILGEAPI_GITHUB_BASE_BRANCH"] = str(value)

    @property
    def BILGEAPI_ALLOW_REAL_DRAFT_PR(self) -> bool:
        raw = os.getenv("BILGEAPI_ALLOW_REAL_DRAFT_PR", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_ALLOW_REAL_DRAFT_PR.setter
    def BILGEAPI_ALLOW_REAL_DRAFT_PR(self, value):
        os.environ["BILGEAPI_ALLOW_REAL_DRAFT_PR"] = str(value).lower()

    @property
    def BILGEAPI_AI_PATCH_PROVIDER(self) -> str:
        return os.getenv("BILGEAPI_AI_PATCH_PROVIDER", "mock").lower()

    @BILGEAPI_AI_PATCH_PROVIDER.setter
    def BILGEAPI_AI_PATCH_PROVIDER(self, value):
        os.environ["BILGEAPI_AI_PATCH_PROVIDER"] = str(value)

    @property
    def BILGEAPI_ALLOW_REAL_AI_PATCH(self) -> bool:
        raw = os.getenv("BILGEAPI_ALLOW_REAL_AI_PATCH", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_ALLOW_REAL_AI_PATCH.setter
    def BILGEAPI_ALLOW_REAL_AI_PATCH(self, value):
        os.environ["BILGEAPI_ALLOW_REAL_AI_PATCH"] = str(value).lower()

    @property
    def BILGEAPI_AI_PATCH_MODEL(self) -> str:
        return os.getenv("BILGEAPI_AI_PATCH_MODEL", "gpt-4.1-mini")

    @BILGEAPI_AI_PATCH_MODEL.setter
    def BILGEAPI_AI_PATCH_MODEL(self, value):
        os.environ["BILGEAPI_AI_PATCH_MODEL"] = str(value)

    @property
    def BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS(self) -> int:
        return int(os.getenv("BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS", "12000"))

    @BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS.setter
    def BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS(self, value):
        os.environ["BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS"] = str(value)

    @property
    def BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS(self) -> int:
        return int(os.getenv("BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS", "8000"))

    @BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS.setter
    def BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS(self, value):
        os.environ["BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS"] = str(value)

    @property
    def BILGEAPI_WATCHDOG_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_WATCHDOG_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_WATCHDOG_ENABLED.setter
    def BILGEAPI_WATCHDOG_ENABLED(self, value):
        os.environ["BILGEAPI_WATCHDOG_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_WATCHDOG_RISK_THRESHOLD(self) -> int:
        return int(os.getenv("BILGEAPI_WATCHDOG_RISK_THRESHOLD", "70"))

    @BILGEAPI_WATCHDOG_RISK_THRESHOLD.setter
    def BILGEAPI_WATCHDOG_RISK_THRESHOLD(self, value):
        os.environ["BILGEAPI_WATCHDOG_RISK_THRESHOLD"] = str(value)

    @property
    def BILGEAPI_WATCHDOG_AUTO_FINDING(self) -> bool:
        raw = os.getenv("BILGEAPI_WATCHDOG_AUTO_FINDING", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_WATCHDOG_AUTO_FINDING.setter
    def BILGEAPI_WATCHDOG_AUTO_FINDING(self, value):
        os.environ["BILGEAPI_WATCHDOG_AUTO_FINDING"] = str(value).lower()

    @property
    def BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED(self) -> bool:
        raw = os.getenv("BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED.setter
    def BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED(self, value):
        os.environ["BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED"] = str(value).lower()

    @property
    def BILGEAPI_SELF_HEALING_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_SELF_HEALING_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_SELF_HEALING_ENABLED.setter
    def BILGEAPI_SELF_HEALING_ENABLED(self, value):
        os.environ["BILGEAPI_SELF_HEALING_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_SELF_HEALING_SAFE_MODE(self) -> bool:
        raw = os.getenv("BILGEAPI_SELF_HEALING_SAFE_MODE", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_SELF_HEALING_SAFE_MODE.setter
    def BILGEAPI_SELF_HEALING_SAFE_MODE(self, value):
        os.environ["BILGEAPI_SELF_HEALING_SAFE_MODE"] = str(value).lower()

    @property
    def BILGEAPI_SELF_HEALING_MAX_ATTEMPTS(self) -> int:
        return int(os.getenv("BILGEAPI_SELF_HEALING_MAX_ATTEMPTS", "2"))

    @BILGEAPI_SELF_HEALING_MAX_ATTEMPTS.setter
    def BILGEAPI_SELF_HEALING_MAX_ATTEMPTS(self, value):
        os.environ["BILGEAPI_SELF_HEALING_MAX_ATTEMPTS"] = str(value)

    @property
    def BILGEAPI_SELF_HEALING_COOLDOWN_SECONDS(self) -> int:
        return int(os.getenv("BILGEAPI_SELF_HEALING_COOLDOWN_SECONDS", "300"))

    @BILGEAPI_SELF_HEALING_COOLDOWN_SECONDS.setter
    def BILGEAPI_SELF_HEALING_COOLDOWN_SECONDS(self, value):
        os.environ["BILGEAPI_SELF_HEALING_COOLDOWN_SECONDS"] = str(value)

    @property
    def BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS(self) -> list[str]:
        raw = os.getenv("BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS", "")
        if not raw:
            return [
                "restart_stateless_service",
                "restart_worker",
                "retry_failed_job",
                "retry_stuck_taskflow_run",
                "rerun_smoke_test",
                "rerun_release_gate",
                "clear_local_cache"
            ]
        return [a.strip() for a in raw.split(",") if a.strip()]

    @BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS.setter
    def BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS(self, value):
        if isinstance(value, list):
            os.environ["BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS"] = ",".join(value)
        else:
            os.environ["BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS"] = str(value)

    @property
    def BILGEAPI_EMERGENCY_RECOVERY_ENABLED(self) -> bool:
        raw = os.getenv("BILGEAPI_EMERGENCY_RECOVERY_ENABLED", "false").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_EMERGENCY_RECOVERY_ENABLED.setter
    def BILGEAPI_EMERGENCY_RECOVERY_ENABLED(self, value):
        os.environ["BILGEAPI_EMERGENCY_RECOVERY_ENABLED"] = str(value).lower()

    @property
    def BILGEAPI_HUMAN_GATE_REQUIRED_FOR_HIGH(self) -> bool:
        raw = os.getenv("BILGEAPI_HUMAN_GATE_REQUIRED_FOR_HIGH", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_HUMAN_GATE_REQUIRED_FOR_HIGH.setter
    def BILGEAPI_HUMAN_GATE_REQUIRED_FOR_HIGH(self, value):
        os.environ["BILGEAPI_HUMAN_GATE_REQUIRED_FOR_HIGH"] = str(value).lower()

    @property
    def BILGEAPI_HUMAN_GATE_REQUIRED_FOR_CRITICAL(self) -> bool:
        raw = os.getenv("BILGEAPI_HUMAN_GATE_REQUIRED_FOR_CRITICAL", "true").lower()
        return raw in ("1", "true", "yes", "on")

    @BILGEAPI_HUMAN_GATE_REQUIRED_FOR_CRITICAL.setter
    def BILGEAPI_HUMAN_GATE_REQUIRED_FOR_CRITICAL(self, value):
        os.environ["BILGEAPI_HUMAN_GATE_REQUIRED_FOR_CRITICAL"] = str(value).lower()


settings = Settings()
