# Alerting Matrix

| Alert Name | Trigger Condition | Delivery Channel | Owner |
| :--- | :--- | :--- | :--- |
| **Workflow Failure Spike** | > 10% failure rate in 10 mins | Telegram, SigNoz | Operator |
| **Repeated Replay** | > 5 replays for the same step | Dashboard, Telegram | Operator |
| **Audit Chain Failure** | Signature mismatch or hash break | Pager, Telegram Admin | Architect |
| **Suspicious Admin Action** | Multiple failed admin login attempts | Security Dashboard | Security Team |
| **LLM Cost Spike** | > $20 total in 1 hour | SMS, Telegram Admin | Architect |
| **Stuck Workflow** | No event in 30 mins for 'RUNNING' state| Dashboard | Operator |

---

# Escalation Policy

If an alert is not acknowledged within the timeframe below, it is escalated to the next level.

## Level 1: Operator (First Responder)
- Responsibilities: Containment, status update, basic runbook execution.
- Respond within: 15 mins (P0/P1), 2 hours (others).

## Level 2: Lead Architect / SRE
- Escalated if L1 cannot resolve or root cause is infrastructural.
- Responsibilities: Deep dive, hotpatching, capacity scaling.
- Respond within: 30 mins (P0), 4 hours (others).

## Level 3: CTO / Security Officer
- Escalated if data breach suspected or massive financial risk.
- Responsibilities: External communication, legal compliance, final decision.
