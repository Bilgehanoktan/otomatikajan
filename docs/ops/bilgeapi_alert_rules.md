# BilgeAPI v1.2.0 — Production Alert Rules

This document specifies the alerting rules, threshold metrics, and routing configurations to notify operations teams of critical runtime incidents.

---

## 1. Alert Rules & Thresholds

| Rule ID | Alarm Name | Severity | Condition | Action / Notification |
| :--- | :--- | :--- | :--- | :--- |
| **API-001** | `ServiceDown` | CRITICAL | `/health` fails or times out for 3 consecutive checks (15s interval) | Telegram Bot alert to Admins + PagerDuty |
| **API-002** | `HighErrorRate` | HIGH | HTTP 5xx error rate exceeds **1%** of total traffic over a 5-minute rolling window | Slack `#ops-alerts` channel |
| **API-003** | `LatencyDegraded` | WARNING | P95 latency exceeds **500 ms** for a 10-minute window | Slack `#ops-alerts` channel |
| **API-004** | `SecurityThreatScan` | HIGH | Auth rejection rate (HTTP 401/403) exceeds **10%** of total traffic or 50 attempts/minute | IP Throttle + Admin email notification |
| **GOV-001** | `SelfHealingPolicyDrift` | CRITICAL | `BILGEAPI_SELF_HEALING_ENABLED` evaluates to `true` on production runtime | Immediate container halt + Operator SMS |

---

## 2. Notification Integrations

Alerts are routed dynamically based on severity:

### Critical Alerts (Telegram / SMS)
* Routed via the Telegram bot integration to `TELEGRAM_ADMIN_IDS` defined in `.env.production`.
* Payload format:
  ```json
  {
    "event": "ALERT_TRIGGERED",
    "rule_id": "API-001",
    "name": "ServiceDown",
    "severity": "CRITICAL",
    "timestamp": "2026-06-12T19:05:00Z",
    "message": "BilgeAPI service at http://prod-host:8100/health is unresponsive."
  }
  ```

### High / Warning Alerts (Slack / Logs)
* Posted to the designated operations webhook URL (`DISCORD_WEBHOOK_URL` / Slack hook).
* Stored in the local syslog audit trail with prefix `[SYSTEM_ALERT]`.
