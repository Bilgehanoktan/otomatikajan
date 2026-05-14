import os
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import UIOperatorHandoverReport

class HandoverReportGenerator:
    """Generates documentation for human handover of autonomous systems."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.output_dir = "artifacts/ui_repair/handover"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_handover(self, title: str) -> UIOperatorHandoverReport:
        """Generates the handover documentation."""
        report_filename = f"handover_{int(datetime.now(timezone.utc).timestamp())}.md"
        report_path = os.path.join(self.output_dir, report_filename)
        
        with open(report_path, "w") as f:
            f.write(f"# Operator Handover Report: {title}\n")
            f.write("## Architecture Summary\nPhase 3-9 Integrated Resilience Mesh.\n")
            f.write("## Operational Guide\n1. Monitor Dashboard\n2. Review Governance Requests\n")
            f.write("## Emergency Protocols\nUse Crisis Control Panel to freeze all healing.\n")

        report = UIOperatorHandoverReport(
            title=title,
            architecture_summary="Phase 3-9 Integrated Resilience Mesh.",
            operational_guide="1. Monitor Dashboard\n2. Review Governance Requests",
            emergency_protocols="Use Crisis Control Panel to freeze all healing.",
            residual_risks_json=["UI visual regressions undetected by DOM diffing"],
            limitations_json=["Complex multi-step stateful UI transitions"],
            report_path=report_path
        )
        
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
