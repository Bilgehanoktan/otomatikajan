import uuid

import pytest

from libs.db.models.ui_repair_models import (
    UIAutoPatchExecution,
    UIVerificationRunV2,
    AutoPatchExecutionStatus,
)
from services.ui_repair.service import UIRepairService


@pytest.mark.asyncio
async def test_autopatch_apply_requires_governance_state(db_session):
    execution = UIAutoPatchExecution(
        execution_key="EXEC-BLOCKED",
        source_type="MANUAL_TRIGGER",
        source_id=uuid.uuid4(),
        status=AutoPatchExecutionStatus.PATCH_GENERATED,
        risk_level="MEDIUM",
    )
    db_session.add(execution)
    await db_session.commit()

    service = UIRepairService(db_session)

    with pytest.raises(ValueError):
        await service.run_autopatch_apply(execution.id, "apply patch now", "operator")


@pytest.mark.asyncio
async def test_autopatch_apply_requires_passed_verification(db_session):
    execution = UIAutoPatchExecution(
        execution_key="EXEC-VERIFY",
        source_type="MANUAL_TRIGGER",
        source_id=uuid.uuid4(),
        status=AutoPatchExecutionStatus.GOVERNANCE_REQUESTED,
        risk_level="MEDIUM",
    )
    db_session.add(execution)
    await db_session.commit()

    service = UIRepairService(db_session)

    with pytest.raises(ValueError):
        await service.run_autopatch_apply(execution.id, "apply patch now", "operator")


@pytest.mark.asyncio
async def test_autopatch_apply_records_governance_approval(db_session):
    execution = UIAutoPatchExecution(
        execution_key="EXEC-APPROVE",
        source_type="MANUAL_TRIGGER",
        source_id=uuid.uuid4(),
        status=AutoPatchExecutionStatus.GOVERNANCE_REQUESTED,
        risk_level="MEDIUM",
    )
    db_session.add(execution)
    await db_session.commit()
    await db_session.refresh(execution)

    verification = UIVerificationRunV2(
        execution_id=execution.id,
        status="PASSED",
        lint_status="PASSED",
        typecheck_status="PASSED",
        unit_test_status="PASSED",
        build_status="PASSED",
        playwright_status="PASSED",
        affected_route_status="PASSED",
        security_posture_status="PASSED",
        cognitive_integrity_status="PASSED",
        result_summary_json={"summary": "all gates passed"},
    )
    db_session.add(verification)
    await db_session.commit()

    service = UIRepairService(db_session)
    validation = await service.run_autopatch_apply(execution.id, "manual governance approval", "operator")

    await db_session.refresh(execution)
    assert validation.status == "PASSED"
    assert execution.governance_approval_id is not None
    assert execution.status == AutoPatchExecutionStatus.VERIFIED
