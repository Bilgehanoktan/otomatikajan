"""
BilgeAPI Startup Validation
============================
Validates critical configuration before the application starts.
In production, missing or default secrets cause a hard failure (fail-fast).

Usage:
    # As a module (Docker CMD pre-check):
    python -m apps.bilgeapi.startup

    # Programmatically (lifespan event):
    from apps.bilgeapi.startup import validate_production_config
    validate_production_config()
"""
import logging
import os
import sys

logger = logging.getLogger("bilgeapi.startup")


class StartupValidationError(RuntimeError):
    """Raised when startup validation fails in production."""
    pass


def validate_production_config() -> list[str]:
    """
    Validate configuration for production readiness.

    Returns:
        List of warning messages (non-fatal in development).

    Raises:
        StartupValidationError: In production, if critical config is missing or insecure.
    """
    app_env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    is_production = app_env == "production"
    warnings: list[str] = []
    errors: list[str] = []

    # 1. Auth Mode (checked first because JWT secret depends on it)
    auth_mode = os.getenv("BILGEAPI_AUTH_MODE", "disabled").lower()
    if is_production and auth_mode == "disabled":
        errors.append(
            "BILGEAPI_AUTH_MODE is 'disabled' in production. "
            "Authentication must be enabled (api_key or jwt)."
        )

    # 2. JWT Secret (only required when auth_mode is 'jwt')
    jwt_secret = os.getenv("BILGEAPI_JWT_SECRET", os.getenv("JWT_SECRET", ""))
    if auth_mode == "jwt" and not jwt_secret:
        msg = "BILGEAPI_JWT_SECRET is not set but BILGEAPI_AUTH_MODE is 'jwt'."
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[DEV] {msg} Auto-generated fallback will be used.")
    elif auth_mode != "jwt" and not jwt_secret:
        # Informational only — JWT secret is optional in api_key mode
        pass

    # 3. Webhook Secret
    webhook_secret = os.getenv("BILGEAPI_WEBHOOK_SECRET", "webhook_secret")
    if not webhook_secret or webhook_secret == "webhook_secret":
        msg = "BILGEAPI_WEBHOOK_SECRET is missing or using the default value 'webhook_secret'."
        if is_production:
            errors.append(msg)
        else:
            warnings.append(f"[DEV] {msg}")

    # 4. Database URL
    db_url = os.getenv("BILGEAPI_DATABASE_URL", "")
    if not db_url:
        db_url = os.getenv("DATABASE_URL", "")
    if is_production:
        if not db_url:
            errors.append("Neither BILGEAPI_DATABASE_URL nor DATABASE_URL is set.")
        elif "localhost" in db_url or "127.0.0.1" in db_url:
            errors.append(
                f"Database URL points to localhost in production: {db_url[:50]}... "
                "This is likely a misconfiguration."
            )

    # 5. CORS Allowlist
    cors_raw = os.getenv("BILGEAPI_CORS_ALLOWLIST", "")
    if is_production and (not cors_raw or cors_raw.strip() == "*"):
        warnings.append(
            "[PROD] BILGEAPI_CORS_ALLOWLIST is wildcard or empty. "
            "Consider restricting to specific origins."
        )

    # Log results
    for w in warnings:
        logger.warning(f"Startup validation: {w}")

    if errors:
        error_summary = "\n".join(f"  - {e}" for e in errors)
        full_msg = (
            f"BilgeAPI startup validation FAILED in '{app_env}' mode.\n"
            f"Critical errors:\n{error_summary}\n"
            f"Fix these issues before deploying to production."
        )
        logger.error(full_msg)
        if is_production:
            raise StartupValidationError(full_msg)

    if not errors and not warnings:
        logger.info(f"Startup validation passed for '{app_env}' mode.")
    elif not errors:
        logger.info(
            f"Startup validation passed for '{app_env}' mode with "
            f"{len(warnings)} warning(s)."
        )

    return warnings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        validate_production_config()
        try:
            print("✅ BilgeAPI startup validation passed.")
        except UnicodeEncodeError:
            print("[OK] BilgeAPI startup validation passed.")
        sys.exit(0)
    except StartupValidationError as e:
        try:
            print(f"❌ {e}", file=sys.stderr)
        except UnicodeEncodeError:
            print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(1)
