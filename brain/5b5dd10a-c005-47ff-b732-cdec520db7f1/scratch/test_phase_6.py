"""
Soft CEO — Phase 6 Verification Script
Tests Calibration Engine and dynamic threshold loading.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db_ctx
from libs.db.models.governance_models import GovernorOutcomeRecord, GovernorOutcomeType
from services.governance.approval_governor_calibration import ApprovalGovernorCalibration
from services.governance.approval_governor_config import ApprovalGovernorConfig
from libs.db.repositories.governor_calibration_repository import GovernorCalibrationRepo

async def verify_phase_6():
    print("--- Phase 6 Verification ---")
    
    async with get_db_ctx() as db:
        # 1. Check Default Config
        auto_approve_risk = await ApprovalGovernorConfig.get_auto_approve_max_risk(db)
        print(f"Default Auto-Approve Risk: {auto_approve_risk}")
        
        # 2. Seed some "BAD" outcomes to trigger a DECREASE proposal
        print("Seeding bad outcomes...")
        from libs.db.models.governance_models import GovernorDecisionQuality
        for _ in range(25):
            outcome = GovernorOutcomeRecord(
                case_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                action_id=uuid.uuid4(),
                decision="AUTO_APPROVE",
                final_outcome="FAILED",
                quality=GovernorDecisionQuality.FALSE_POSITIVE, # Threshold was too high, autonomy was too high
                was_successful=False,
                operator_agreed=False,
                created_at=datetime.now(timezone.utc)
            )
            db.add(outcome)
        await db.commit()
        
        # 3. Run Calibration Engine
        print("Running Calibration Engine...")
        engine = ApprovalGovernorCalibration(db)
        proposals = await engine.generate_calibration_proposals(window_days=1)
        print(f"Generated {len(proposals)} proposals.")
        
        if proposals:
            prop_id = proposals[0]
            repo = GovernorCalibrationRepo()
            prop = await repo.get_by_id(db, prop_id)
            print(f"Proposal: {prop.parameter_name} {prop.old_value} -> {prop.proposed_value}")
            print(f"Reason: {prop.change_reason}")
            
            # 4. Apply Calibration
            print("Applying Calibration...")
            success = await repo.apply_calibration(db, prop_id, "test_admin")
            await db.commit()
            print(f"Apply Success: {success}")
            
            # 5. Verify New Threshold
            new_val = await ApprovalGovernorConfig.get_auto_approve_max_risk(db)
            print(f"New Auto-Approve Risk: {new_val}")
            
            # 6. Test Freeze Mode
            print("Setting FREEZE_MODE...")
            from libs.db.models.governance_models import GovernorCalibrationRecord
            freeze_prop = await repo.create_proposal(db, {
                "parameter_name": "FREEZE_MODE",
                "old_value": 0.0,
                "proposed_value": 1.0,
                "change_reason": "Testing freeze",
                "confidence_score": 1.0,
                "window_days": 1,
                "sample_size": 1
            })
            await repo.apply_calibration(db, freeze_prop.id, "test_admin")
            await db.commit()
            
            is_frozen = await ApprovalGovernorConfig.is_frozen(db)
            print(f"Is Frozen: {is_frozen}")

if __name__ == "__main__":
    asyncio.run(verify_phase_6())
