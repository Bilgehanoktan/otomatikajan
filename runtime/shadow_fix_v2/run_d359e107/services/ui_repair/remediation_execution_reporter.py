import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import UIAutoPatchExecution

class RemediationExecutionReporter:
    """
    Phase 27: Reporting for autonomous remediation executions.
    """
    def __init__(self, db: Session):
        self.db = db

    def generate_execution_summary(self, execution_id: uuid.UUID) -> Dict[str, Any]:
        execution = self.db.query(UIAutoPatchExecution).filter(UIAutoPatchExecution.id == execution_id).first()
        if not execution:
            return {"error": "Execution not found"}

        return {
            "execution_key": execution.execution_key,
            "status": execution.status.value,
            "source": execution.source_type.value,
            "risk_level": execution.risk_level.value,
            "patch_path": execution.patch_path,
            "pr_url": execution.pr_url,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "success": execution.status.value in ["VERIFIED", "APPLIED"]
        }
