from apps.bilgeapi.adapters.interface import DiagnosticAdapter
from apps.bilgeapi.schemas.incident import IncidentResponse

class MockAgentAdapter(DiagnosticAdapter):
    @property
    def name(self) -> str:
        return "mock_agent"

    async def run_diagnostic(self, incident: IncidentResponse) -> dict:
        err = incident.error_message.lower()
        if "timeout" in err or "5432" in err or "postgres" in err:
            return {
                "summary": "Database connection timeout detected.",
                "root_cause_hypothesis": "PostgreSQL connection pool exhaustion or network port blockage on 5432.",
                "confidence": 0.85,
                "risk_score": 0.35,
                "findings": [
                    {"description": "Backend API failed to acquire DB connection within 3000ms."},
                    {"description": "PostgreSQL port 5432 is rejecting connection attempts."}
                ],
                "recommendations": [
                    {"description": "Increase max_connections settings in postgresql.conf."},
                    {"description": "Restart PostgreSQL service to release stuck idle connections."}
                ]
            }
        else:
            return {
                "summary": f"Generic log diagnosis completed for incident '{incident.id}'.",
                "root_cause_hypothesis": "Unspecified application error.",
                "confidence": 0.50,
                "risk_score": 0.10,
                "findings": [
                    {"description": f"Incident captured with message: {incident.error_message}"}
                ],
                "recommendations": [
                    {"description": "Check application traceback logs for further details."}
                ]
            }

    async def health_check(self) -> bool:
        return True
