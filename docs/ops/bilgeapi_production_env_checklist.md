# BilgeAPI v1.2.0 — Production Environment Audit Checklist

This checklist defines the security, performance, and reliability validation rules for any environment configuration file (e.g. `.env.production`) targeting production deployments.

---

## 1. General & Mode Variables
- [ ] **`APP_ENV`**: Must be set to `production` or `staging`.
- [ ] **`ENVIRONMENT`**: Must be set to `production` or `staging`.
- [ ] **`RUNTIME_PROFILE`**: Must be set to `production`.
- [ ] **`DEBUG`**: Must be set to `false`.
- [ ] **`LOG_LEVEL`**: Must be set to `INFO`, `WARNING`, or `ERROR` (never `DEBUG` in production).

---

## 2. Secrets & Encryption Key Verification
- [ ] **`JWT_SECRET`**: Must be a cryptographically secure value (minimum 64 characters hex) and must **not** contain the template default `CHANGE_ME`.
- [ ] **`ADMIN_SECRET`**: Must be a cryptographically secure value (minimum 64 characters hex) and must **not** contain the template default `CHANGE_ME`.
- [ ] **`BILGEAPI_JWT_SECRET`**: Must be a cryptographically secure value (minimum 64 characters hex) and must **not** contain the template default `CHANGE_ME`.
- [ ] **`BILGEAPI_WEBHOOK_SECRET`**: Must be at least 16 characters long and must **not** contain the template default `CHANGE_ME`.

---

## 3. Database Security
- [ ] **`DATABASE_URL`**: Must not point to `localhost` or `127.0.0.1`. Must point to a production cluster or container service name (e.g. `db`).
- [ ] **`BILGEAPI_DATABASE_URL`**: Must not point to `localhost` or `127.0.0.1`.
- [ ] **Password Strength**: Connection strings must not contain default passwords like `CHANGE_ME` or `postgres`.

---

## 4. API Authentication & Hardening
- [ ] **`BILGEAPI_AUTH_MODE`**: Must be set to `api_key`.
- [ ] **`BILGEAPI_STATIC_KEYS`**: Must be empty or not set. Plaintext static API keys are **strictly forbidden** in production.
- [ ] **`BILGEAPI_STATIC_KEY_HASHES`**: Must be configured with hashed static API keys (`sha256_hash:role` pairs).
- [ ] **`BILGEAPI_ALLOW_PRIVATE_WEBHOOKS`**: Must be set to `false` (blocks webhooks targeting loopback/private IP spaces).
- [ ] **`BILGEAPI_RATE_LIMIT_RPS`**: Must be enabled and set to a reasonable limit (e.g., `10`).

---

## 5. Agent Capability Registry Security
- [ ] **`BILGEAPI_SELF_HEALING_ENABLED`**: Must be set to `false` to prevent autonomous self-repair actions in production without human operator validation.
- [ ] **`BILGEAPI_EXTERNAL_AGENTS_ENABLED`**: Must be set to `false` or strictly disabled by default to restrict unauthorized execution.
