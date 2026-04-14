# Incident Response Matrix

## Severity Levels

| Severity | Description | Target Response | Notification |
| :--- | :--- | :--- | :--- |
| **P0 (Critical)** | System down, data corruption, root access leak, cost spike > $50/hr. | < 15 mins | Pager, SMS, Telegram Admin |
| **P1 (High)** | Workflow engine stuck, integration failed, telemetry down. | < 1 hour | Telegram Admin, Email |
| **P2 (Medium)** | Dashboard UI issues, non-critical tool failure, minor budget breach. | < 8 hours | Slack/Teams, Dashboard |
| **P3 (Low)** | Log verbosity issues, documentation mismatch. | Next business day | Dashboard |

## Response Procedure for P0
1. **Detect**: Alert from SigNoz (LLM Cost Spike or Worker Down).
2. **Contain**: Set `SOVEREIGN_MODE=safe` or stop the specific container.
3. **Analyze**: Check OTel Traces in SigNoz to find the offending prompt/workflow.
4. **Remediate**: Apply patch, revert config, or blackhole the user.
5. **Post-Mortem**: Document in `docs/reports/incident_YYYYMMDD.md`.
