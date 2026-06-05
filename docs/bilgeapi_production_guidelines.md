# BilgeAPI Production Deployment & Security Guidelines

This document details critical configurations, architectural limitations, and operational security requirements for running `BilgeAPI` in production environments.

---

## 1. Authentication & API Security (SIF-01 / SIF-03)

- **OpenAPI Scheme**: Route permissions are enforced globally on all non-public endpoints. The OpenAPI schema (`docs/openapi/bilgeapi_openapi.json`) explicitly exposes the security schemes under `ApiKeyHeader` (`X-API-Key`) and `BearerAuth` (`Authorization: Bearer <JWT>`).
- **Public Endpoints**: `/health`, `/docs`, `/redoc`, and `/openapi.json` are public endpoints and bypass authorization requirements.

---

## 2. Rate Limiting Multi-replica Warning

> [!WARNING]
> The current sliding-window Rate Limiter registered in `apps/bilgeapi/main.py` is implemented **in-memory** within the application process.
> - **Single-instance / Local development**: The in-memory limiter is sufficient and robust.
>   - **Multi-replica / Multi-worker production**: Since replica containers do not share memory space, the rate limits will be applied per-replica rather than globally. This can allow clients to exceed the configured limits when requests are distributed via load balancers.
>   - **Recommendation**: For production environments using multi-instance clusters, transition the rate limiter backend from python's in-memory storage to a shared **Redis-backed sliding window limiter**.

---

## 3. Webhook Signed Payload & SSRF Guard (Phase 5 Hardening)

### Webhook Secret Verification
- In production (`APP_ENV == "production"`), `BILGEAPI_WEBHOOK_SECRET` must be set to a secure, custom key.
- If it is missing, empty, or left as the default `"webhook_secret"`, the service will fail to start (`RuntimeError`) during initialization to prevent insecure webhook signatures.

### Private Subnet Bypass Restriction
- The parameter `BILGEAPI_ALLOW_PRIVATE_WEBHOOKS` resolves target domains to IP addresses and allows/disallows localhost or private subnet dispatches.
- In production, this bypass **cannot** be enabled. The SSRF guard will strictly block all requests targeting loopback (`127.0.0.0/8`, `::1`), private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`), link-local, multicast, and Cloud Metadata service IP (`169.254.169.254`) regardless of the configuration setting.

---

## 4. Configuration & Runtime Mutation

- **Dynamic Setters**: The configuration properties implemented in `apps/bilgeapi/config.py` modify `os.environ` dynamically.
- **Guidance**: These setters are designed exclusively as **testability helpers** to enable clean unit testing and mock configurations via monkeypatching. They must not be invoked for runtime mutation of settings in production code. All production settings must be read-only at runtime.
