"""
Production-mode hardening smoke for BilgeAPI.

This script uses FastAPI TestClient and does not mutate a live deployment.
It verifies production auth guardrails that are easy to regress:
- plaintext static keys are not accepted in APP_ENV=production
- hashed static admin keys are accepted
- /metrics requires admin privileges when BILGEAPI_METRICS_PUBLIC=false
- X-Tenant-ID header spoofing is ignored in production metering fallback
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _configure_env() -> tuple[str, str, str]:
    admin_key = "phase16_admin_hash_only_key"
    operator_key = "phase16_operator_hash_only_key"
    plaintext_only_key = "phase16_plaintext_should_fail"

    os.environ["APP_ENV"] = "production"
    os.environ["BILGEAPI_AUTH_MODE"] = "api_key"
    os.environ["BILGEAPI_WEBHOOK_SECRET"] = "phase16_secure_webhook_secret_32chars"
    os.environ["BILGEAPI_METRICS_PUBLIC"] = "false"
    os.environ["BILGEAPI_STATIC_KEYS"] = f"{plaintext_only_key}:admin"
    os.environ["BILGEAPI_STATIC_KEY_HASHES"] = f"{_hash(admin_key)}:admin,{_hash(operator_key)}:operator"
    try:
        import libs.config as core_config

        core_config.APP_ENV = "production"
        core_config.is_prod = True
        core_config.is_dev = False
        core_config.is_test = False
    except Exception:
        pass
    return admin_key, operator_key, plaintext_only_key


def _line(name: str, ok: bool, detail: str) -> str:
    return f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |"


async def _disabled_db_metrics_key(api_key: str) -> bool:
    return False


async def _disabled_db_key_validation(self, **kwargs):
    return None


async def _disabled_audit_log(self, **kwargs):
    return None


class _NoopAuditService:
    async def log_event(self, **kwargs):
        return None


def run() -> tuple[bool, list[str]]:
    admin_key, operator_key, plaintext_only_key = _configure_env()

    from fastapi.testclient import TestClient
    from starlette.requests import Request
    from apps.bilgeapi.main import app, extract_tenant_id
    from apps.bilgeapi.repositories.memory import InMemoryApiKeyRepository
    from apps.bilgeapi.services.audit import AuditService
    from apps.bilgeapi.services.api_key import ApiKeyService
    from apps.bilgeapi.routers import metrics as metrics_router
    from apps.bilgeapi.routers.deps import get_api_key_repository, get_api_key_service, get_audit_service

    admin_key, operator_key, plaintext_only_key = _configure_env()
    api_key_repo = InMemoryApiKeyRepository()
    audit_service = _NoopAuditService()
    app.dependency_overrides[get_api_key_repository] = lambda: api_key_repo
    app.dependency_overrides[get_audit_service] = lambda: audit_service
    app.dependency_overrides[get_api_key_service] = lambda: ApiKeyService(api_key_repo, audit_service)
    metrics_router._has_admin_db_key = _disabled_db_metrics_key
    ApiKeyService.validate_key_and_record_use = _disabled_db_key_validation
    AuditService.log_event = _disabled_audit_log

    client = TestClient(app)
    results: list[tuple[str, bool, str]] = []

    response = client.get("/v1/catalog", headers={"X-API-Key": plaintext_only_key})
    results.append(("Plaintext static fallback disabled", response.status_code == 401, f"HTTP {response.status_code}"))

    response = client.get("/v1/catalog", headers={"X-API-Key": admin_key})
    results.append(("Hashed static admin accepted", response.status_code == 200, f"HTTP {response.status_code}"))

    response = client.get("/metrics")
    results.append(("Private metrics require auth", response.status_code == 401, f"HTTP {response.status_code}"))

    response = client.get("/metrics", headers={"X-API-Key": operator_key})
    results.append(("Private metrics reject operator", response.status_code == 403, f"HTTP {response.status_code}"))

    response = client.get("/metrics", headers={"X-API-Key": admin_key})
    results.append(("Private metrics accept admin", response.status_code == 200, f"HTTP {response.status_code}"))

    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/v1/catalog",
        "headers": [(b"x-tenant-id", b"spoofed-tenant")],
        "client": ("127.0.0.1", 12345),
    })
    tenant = extract_tenant_id(request)
    results.append(("X-Tenant-ID spoof ignored in production", tenant == "anonymous", f"tenant={tenant}"))

    lines = [
        "# BilgeAPI Phase 16 Production Hardening Smoke",
        "",
        "| Check | Result | Detail |",
        "|---|---:|---|",
    ]
    lines.extend(_line(name, ok, detail) for name, ok, detail in results)
    ok = all(item[1] for item in results)
    lines.extend(["", f"Overall: {'PASS' if ok else 'FAIL'}"])
    return ok, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify BilgeAPI production-mode hardening guardrails.")
    parser.add_argument("--evidence", default="docs/evidence/bilgeapi_phase16_production_hardening.md")
    args = parser.parse_args()

    ok, lines = run()
    output = "\n".join(lines) + "\n"
    print(output)

    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(output, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
