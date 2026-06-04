# BilgeAPI Known Limitations

This document outlines the known functional boundaries, performance constraints, and architectural limits of **BilgeAPI** as of Faz 8.

## 1. Dry-Run Smoke Test Isolation
- **Limitation**: The E2E dry-run smoke test (run during release readiness check) executes completely in-memory using mock dispatchers and does not mutate database tables.
- **Impact**: It verifies syntax and wiring, but cannot detect live database schema changes or constraint violations. Live integration tests must be used for full database verification.

## 2. SSRF Guard Constraints
- **Limitation**: The SSRF prevention guard relies on DNS resolution of the hostnames.
- **Impact**: Hosts that do not resolve on the local DNS server will fail early. In local development environments, accessing hosts like `localhost` or custom local domain names might fail unless `BILGEAPI_ALLOW_PRIVATE_WEBHOOKS` is explicitly enabled.

## 3. In-Memory Rate Limiting
- **Limitation**: The rate limiting for release readiness checks (currently set to 1 request per minute) is managed in-memory per worker process.
- **Impact**: In a multi-worker production environment (e.g., behind a load balancer with multiple containers), requests may not be strictly limited across workers unless sticky sessions or a centralized Redis cache are introduced.

## 4. Default Secret Warnings in Development
- **Limitation**: When `APP_ENV` is set to `development` or `test`, using the default secrets (e.g., `dev-test-key-001`) triggers warnings.
- **Impact**: This is by design to prevent default keys in production, but development console logs will contain warnings. In production, these triggers act as blocking gates.
