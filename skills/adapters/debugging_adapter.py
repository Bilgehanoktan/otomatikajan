from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class DebuggingSkillAdapter(BaseSkillAdapter):
    skill_id = "debugging"

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["bug", "error", "incident", "fix", "traceback", "failure", "hata"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        try:
            from core.repair_orchestrator import get_repair_orchestrator
            from repair.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity

            incident = IncidentRecord(
                incident_id=f"inc-{req.project_id or 'adhoc'}",
                source=IncidentSource.MANUAL,
                severity=IncidentSeverity.MEDIUM,
                service="skill-layer",
                module="debugging-adapter",
                symptom=req.description[:500],
                context=req.context or {},
            )

            orch = get_repair_orchestrator()
            job = await orch.start_repair(incident)

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary="Repair pipeline başlatıldı",
                data={
                    "repair_job_id": job.job_id,
                    "status": str(job.status),
                    "incident_id": incident.incident_id,
                },
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Debugging başlatılamadı: {e}",
            )
