import hashlib
import json

from sqlalchemy import select

from libs.db.models.core_models import WorkflowEvent
from libs.db.session import AsyncSessionLocal
from services.observability.logging import get_logger

logger = get_logger("workflow.audit_verifier")

class AuditChainVerifier:
    """
    Verifies the cryptographic integrity of the WorkflowEvent audit trail.
    Detects tampering by recalculating hash chains.
    """

    @staticmethod
    def calculate_hash(event: WorkflowEvent, prev_hash: str) -> str:
        """Reproduces the hash logic from persistence.py"""
        payload_str = json.dumps(event.payload, sort_keys=True)
        data = f"{event.event_type}:{payload_str}:{event.timestamp}:{prev_hash}:{event.operator_id or ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def verify_full_chain(self) -> tuple[bool, list[str]]:
        """
        Iterates through all events and verifies the signature chain.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(WorkflowEvent).order_by(WorkflowEvent.timestamp.asc()))
            events = result.scalars().all()

            if not events:
                logger.info("Audit chain is empty. Nothing to verify.")
                return True, []

            prev_hash = "GENESIS"
            for i, event in enumerate(events):
                calculated = self.calculate_hash(event, prev_hash)

                if event.signature != calculated:
                    err = (f"🔥 TAMPER DETECTED at Event ID {event.id} (Index {i}). "
                           f"Expected: {calculated[:12]}..., Found: {event.signature[:12]}...")
                    logger.error(err)
                    errors.append(err)
                    # We continue to find all breaks, but the chain is broken

                prev_hash = event.signature

        if not errors:
            logger.info(f"✅ Audit chain integrity verified for {len(events)} events.")
            return True, []

        return False, errors

async def run_audit_verification():
    verifier = AuditChainVerifier()
    success, errors = await verifier.verify_full_chain()
    if not success:
        print(f"FAILED: {len(errors)} integrity errors found!")
        for e in errors:
            print(e)
    else:
        print("SUCCESS: Audit chain is intact.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_audit_verification())
