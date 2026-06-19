import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '.')

from libs.db.session import AsyncSessionLocal
from libs.db.models.governance_models import ProductionSignoff, SignoffStatus, ValidationResult, ValidationType, ValidationStatus
from libs.db.models.auth_models import Operator
from sqlalchemy import select, delete, text

async def seed_signoffs():
    print("Seeding premium Production Signoffs & Rollout logs...")
    async with AsyncSessionLocal() as db:
        # Detect database dialect
        dialect_name = db.bind.dialect.name
        if dialect_name == "sqlite":
            await db.execute(text("PRAGMA foreign_keys = OFF;"))
        elif dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'replica';"))

        # Clean existing signoffs and related validation results
        await db.execute(delete(ValidationResult))
        await db.execute(delete(ProductionSignoff))
        await db.flush()

        # Find our admin operator
        res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
        op = res.scalar_one_or_none()
        op_id = op.id if op else None

        now = datetime.now(timezone.utc)

        # 1. Signoff 1: SIF-01-Identity (Signed, Tier-2, 100% Progress)
        s1_id = uuid.uuid4()
        s1 = ProductionSignoff(
            id=s1_id,
            component_name="SIF-01-Identity",
            version="v2.1.0",
            status=SignoffStatus.SIGNED,
            approver_id=op_id,
            approver_note="Pre-deployment verification checks passed cleanly on standard Playwright matrix. Signed off for production pilot rollout.",
            evidence_summary={
                "purpose": "OPERATIONAL",
                "scope": "Sovereign AGI Core",
                "tests_passed": 49,
                "coverage": "87.5%",
                "audit_integrity": "SHA256:VERIFIED"
            },
            created_at=now - timedelta(hours=4)
        )

        # 2. Signoff 2: TaskPlanner (Signed, Tier-2, 100% Progress)
        s2_id = uuid.uuid4()
        s2 = ProductionSignoff(
            id=s2_id,
            component_name="TaskPlanner",
            version="v1.14.0",
            status=SignoffStatus.SIGNED,
            approver_id=op_id,
            approver_note="Continuous validation metrics have remained nominal over the 24 hour soak test. Rollout authorized.",
            evidence_summary={
                "purpose": "UPGRADE",
                "scope": "Cognitive Stack",
                "soak_test_hours": 24,
                "anomalies_detected": 0
            },
            created_at=now - timedelta(hours=2)
        )

        # 3. Signoff 3: TaskScheduler (Pending, Advisory, 45% Progress)
        s3_id = uuid.uuid4()
        s3 = ProductionSignoff(
            id=s3_id,
            component_name="TaskScheduler",
            version="v1.15.0-rc2",
            status=SignoffStatus.PENDING,
            approver_id=None,
            approver_note=None,
            evidence_summary={
                "purpose": "OPTIMIZATION",
                "scope": "Queue Scheduler",
                "risk_class": "MEDIUM",
                "verification_pending": ["Security Vulnerability Scan"]
            },
            created_at=now - timedelta(minutes=45)
        )

        db.add_all([s1, s2, s3])
        await db.flush()

        # 4. Seed Validation Results associated with these Signoffs
        v1 = ValidationResult(
            id=uuid.uuid4(),
            component_name="SIF-01-Identity",
            test_suite="Playwright E2E UI Suite",
            validation_type=ValidationType.PRE_DEPLOY,
            status=ValidationStatus.PASS,
            metrics={"scenarios": 12, "passed": 12, "flaky": 0},
            raw_logs="All E2E scenarios ran successfully with zero exceptions.",
            duration_ms=12000,
            signoff_id=s1_id,
            created_at=now - timedelta(hours=4, minutes=10)
        )

        v2 = ValidationResult(
            id=uuid.uuid4(),
            component_name="TaskPlanner",
            test_suite="Pytest Framework",
            validation_type=ValidationType.CONTINUOUS,
            status=ValidationStatus.PASS,
            metrics={"tests_total": 49, "tests_passed": 49},
            raw_logs="All unit and integration tests passed cleanly.",
            duration_ms=5400,
            signoff_id=s2_id,
            created_at=now - timedelta(hours=2, minutes=5)
        )

        v3 = ValidationResult(
            id=uuid.uuid4(),
            component_name="TaskScheduler",
            test_suite="Linter & Code Quality",
            validation_type=ValidationType.PRE_DEPLOY,
            status=ValidationStatus.PASS,
            metrics={"warnings": 0, "errors": 0},
            raw_logs="TypeScript and Python static analysis complete. Clean.",
            duration_ms=2100,
            signoff_id=s3_id,
            created_at=now - timedelta(minutes=40)
        )

        db.add_all([v1, v2, v3])

        # Restore replication role back to origin for postgres
        if dialect_name == "postgresql":
            await db.execute(text("SET session_replication_role = 'origin';"))

        await db.commit()
        print("Successfully seeded Production Signoffs and associated Validation Results!")

if __name__ == "__main__":
    asyncio.run(seed_signoffs())
