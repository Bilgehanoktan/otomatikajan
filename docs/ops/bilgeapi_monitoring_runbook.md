# BilgeAPI v1.2.0 — Production Monitoring Runbook

This runbook describes the key health metrics, log monitoring patterns, and runtime telemetry variables required to maintain the stability and performance of BilgeAPI v1.2.0 in production.

---

## 1. Core Health Indicators (KPIs)

The following metrics must be actively collected and monitored:

| Metric Name | Source / Endpoint | Target Threshold | Critical Threshold |
| :--- | :--- | :--- | :--- |
| **API Latency (p95)** | Traefik access log / Prometheus | `< 200 ms` | `> 1000 ms` |
| **HTTP 5xx Rate** | Traefik access log / Prometheus | `0.0%` | `> 1.0%` (15m window) |
| **Auth Rejection Rate** | `/v1/audit-events` (401/403 status) | `< 2%` | `> 5%` (unauthorized scan warning) |
| **Engine Health Status** | `/health` / `/v1/ops/health` | `HTTP 200` | `Non-200 / Timeout` |
| **Self-Healing State** | Watchdog service logs | `SAFE_DISABLED` | `UNAUTHORIZED_EXECUTION` |

---

## 2. Telemetry & Log Auditing Patterns

Use structured logs to audit system health:

### Log Locations
* **Docker Logs:** `docker compose logs -f bilgeapi`
* **Audit Database:** `/v1/audit-events` or `repair_audit_events` table.

### Key Search Patterns
* **Database Errors:** Look for `sqlalchemy.exc` or `ConnectionRefusedError`.
* **Security Alarms:** Look for `API key validation failed` or `X-Tenant-ID spoof rejected`.
* **Rate Limiting:** Look for `Rate limit exceeded` (HTTP 429).

---

## 3. Meta-Governor & Self-Healing Telemetry

Since **`BILGEAPI_SELF_HEALING_ENABLED`** is set to `false` in production for safety, any log entry indicating that an autonomous recovery was triggered represents a critical security policy drift:
* **Warning Pattern:** `Self-healing execution requested but disabled by policy.` (This is expected and confirms the safety gate works).
* **Alert Pattern:** `Self-healing action executed on host.` (Requires immediate audit of environment variables).

---

## 4. Runbook Maintenance & Escalation

1. **Daily Check:** Verify that `/health` returns `{"status":"healthy"}`.
2. **Weekly Check:** Audit the audit event log for any abnormal spikes in 401/403 rejections.
3. **Escalation Path:** If Latency exceeds 1000ms or 5xx Rate exceeds 1%, notify the DevOps lead and prepare the Rollback Playbook if needed.
