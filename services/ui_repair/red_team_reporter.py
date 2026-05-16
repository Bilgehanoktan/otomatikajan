import uuid
from typing import List, Dict, Any, Sequence
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIRedTeamReport, UIRedTeamRun, UIRedTeamScenario, 
    UIRedTeamFinding, UIAdversarialDriftEvent, RedTeamRunStatus
)

class RedTeamReporter:
    """Phase 24: Generates executive Red Team operation reports."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, period_start: datetime, period_end: datetime) -> UIRedTeamReport:
        """Aggregates data for the given period and creates a summary report."""
        
        # 1. Fetch data
        stmt_runs = select(UIRedTeamRun).where(UIRedTeamRun.created_at.between(period_start, period_end))
        res_runs = await self.db.execute(stmt_runs)
        runs = res_runs.scalars().all()
        
        stmt_findings = select(UIRedTeamFinding).where(UIRedTeamFinding.created_at.between(period_start, period_end))
        res_findings = await self.db.execute(stmt_findings)
        findings = res_findings.scalars().all()
        
        stmt_drifts = select(UIAdversarialDriftEvent).where(UIAdversarialDriftEvent.created_at.between(period_start, period_end))
        res_drifts = await self.db.execute(stmt_drifts)
        drifts = res_drifts.scalars().all()
        
        # 2. Calculate metrics
        total_runs = len(runs)
        passed_runs = sum(1 for r in runs if r.status == RedTeamRunStatus.PASSED)
        failed_runs = total_runs - passed_runs
        
        crit_findings = sum(1 for f in findings if f.severity == "CRITICAL")
        high_findings = sum(1 for f in findings if f.severity == "HIGH")
        
        # 3. Build Executive Summary
        summary = f"""
        # Red Team Executive Summary ({period_start.date()} to {period_end.date()})
        
        During this period, the Autonomous Red Team Agent executed {total_runs} security scenarios.
        
        ## Key Metrics:
        - Passed Scenarios: {passed_runs}
        - Failed Scenarios: {failed_runs}
        - Critical Findings: {crit_findings}
        - High-Severity Findings: {high_findings}
        - Adversarial Drift Events: {len(drifts)}
        
        ## Analysis:
        The system demonstrated strong resilience in {passed_runs/total_runs*100 if total_runs > 0 else 0:.1f}% of tests. 
        However, {crit_findings} critical bypasses were detected, primarily in the {self._get_top_affected_domain(list(findings))} domain.
        Adversarial drift scoring remains stable at an average of {self._get_avg_drift(list(drifts)):.2f}.
        """
        
        report = UIRedTeamReport(
            id=uuid.uuid4(),
            report_name=f"Red Team Audit Report - {datetime.now().strftime('%Y-%m-%d')}",
            period_start=period_start,
            period_end=period_end,
            total_scenarios=total_runs,
            passed_scenarios=passed_runs,
            failed_scenarios=failed_runs,
            critical_findings=crit_findings,
            high_findings=high_findings,
            drift_events=len(drifts),
            executive_summary=summary,
            generated_at=datetime.now(timezone.utc),
            report_path=f"reports/red_team/RT_REPORT_{uuid.uuid4().hex[:8]}.md"
        )
        
        self.db.add(report)
        await self.db.commit()
        return report

    def _get_top_affected_domain(self, findings: Sequence[UIRedTeamFinding]) -> str:
        if not findings: return "None"
        domains = [f.affected_domain.value for f in findings]
        return max(set(domains), key=domains.count)

    def _get_avg_drift(self, drifts: Sequence[UIAdversarialDriftEvent]) -> float:
        if not drifts: return 0.0
        return sum(d.drift_score for d in drifts) / len(drifts)
