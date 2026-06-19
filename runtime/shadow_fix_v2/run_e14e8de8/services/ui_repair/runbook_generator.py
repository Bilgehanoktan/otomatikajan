import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIEnterpriseRunbook

class RunbookGenerator:
    """Generates an enterprise operating guide (runbook)."""
    
    @staticmethod
    async def generate_runbook(db: AsyncSession, title: str, version: str) -> UIEnterpriseRunbook:
        content = f"""
# {title} - v{version}
## Enterprise UI Repair Operating Model

### 1. System Overview
The Egemen YAZ Autonomous UI Repair System is an enterprise-grade self-healing platform...

### 2. Roles & Responsibilities
- **Operator**: Daily monitoring, patch approval, crisis management.
- **Project Owner**: Route scope definition, policy configuration.
- **Governance Lead**: Audit trail review, compliance verification.

### 3. Monitoring Operations
- Project-based route scanning every 5-15 minutes.
- Automated failure classification and severity assessment.

### 4. Repair Workflow
1. Detection -> 2. Diagnostic -> 3. Patch Generation -> 4. Governance Gate -> 5. Apply

### 5. Governance Approval Flow
- Mandatory human-in-the-loop for HIGH/CRITICAL risks.
- Rationale requirement for all operator actions.

### 6. Crisis Control Procedure
- FREEZE_ALL: Immediate stop of all monitoring and repair actions.
- SHADOW_ONLY: Downgrade to non-destructive observation.

### 7. Rollback Procedure
- Automatic snapshot creation before any patch application.
- One-click restoration via the dashboard.

### 8. SLO/SLA Definitions
- Uptime: 99%+
- Critical Route Coverage: 100%

### 9. Daily Operator Checklist
- [ ] Review all UNRESOLVED cases.
- [ ] Check Governance Waiting queue.
- [ ] Verify Monitoring Run stability.

### 10. Known Limitations
- DB migrations are manual.
- Third-party auth flows require specific bypasses.
        """
        
        evidence_hash = hashlib.sha256(content.encode()).hexdigest()
        
        runbook = UIEnterpriseRunbook(
            id=uuid.uuid4(),
            title=title,
            version=version,
            scope="ENTERPRISE_WIDE",
            content=content,
            evidence_hash=evidence_hash,
            generated_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        db.add(runbook)
        await db.commit()
        await db.refresh(runbook)
        return runbook

    @staticmethod
    async def get_latest_runbook(db: AsyncSession):
        stmt = select(UIEnterpriseRunbook).order_by(UIEnterpriseRunbook.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
