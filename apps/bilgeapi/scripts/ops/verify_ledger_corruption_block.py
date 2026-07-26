#!/usr/bin/env python3
"""
verify_ledger_corruption_block.py — Phase 31F Ledger Corruption human gate block verification
========================================================================================
Checks:
1. Creates an isolated test ledger chain using a unique UUID chain_id.
2. Appends multiple valid events to establish a solid block chain.
3. Verifies that the chain is initially valid.
4. Simulates corruption by modifying database entry hash/sequence.
5. Verifies that BilgeAPIHumanGateVerifier blocks approvals and raises ValueError.
6. Performs complete cleanup of the test ledger entries to leave no trace in DB.
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Optional

# Add project root directory to python path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from libs.db.session import AsyncSessionLocal
from apps.bilgeapi.models.database import ReviewLedgerEntryModel
from services.repair.bilgeapi_human_gate_context import BilgeAPIHumanGateVerifier
from apps.bilgeapi.services.review_ledger import ReviewLedgerService
from apps.bilgeapi.repositories.interface import ReviewLedgerRepository
from sqlalchemy import select, delete

# Simple repository wrapper to use with service
class SimpleReviewLedgerRepository(ReviewLedgerRepository):
    def __init__(self, db_session):
        self.db = db_session
        
    async def append_entry(self, entry: dict) -> dict:
        db_entry = ReviewLedgerEntryModel(**entry)
        self.db.add(db_entry)
        await self.db.commit()
        return entry
        
    async def get_entry(self, entry_id: str) -> Optional[dict]:
        stmt = select(ReviewLedgerEntryModel).where(ReviewLedgerEntryModel.id == entry_id)
        res = await self.db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            return None
        return self._to_dict(entry)
        
    async def get_latest_entry(self, chain_id: str) -> dict:
        stmt = select(ReviewLedgerEntryModel).where(
            ReviewLedgerEntryModel.chain_id == chain_id
        ).order_by(ReviewLedgerEntryModel.sequence_no.desc()).limit(1)
        res = await self.db.execute(stmt)
        entry = res.scalar_one_or_none()
        if not entry:
            return None
        return self._to_dict(entry)
        
    async def list_by_chain(self, chain_id: str) -> list:
        stmt = select(ReviewLedgerEntryModel).where(
            ReviewLedgerEntryModel.chain_id == chain_id
        ).order_by(ReviewLedgerEntryModel.sequence_no.asc())
        res = await self.db.execute(stmt)
        return [self._to_dict(entry) for entry in res.scalars().all()]
        
    async def list_recent(self, limit: int = 50) -> list:
        stmt = select(ReviewLedgerEntryModel).order_by(
            ReviewLedgerEntryModel.created_at.desc()
        ).limit(limit)
        res = await self.db.execute(stmt)
        return [self._to_dict(entry) for entry in res.scalars().all()]
        
    def _to_dict(self, entry: ReviewLedgerEntryModel) -> dict:
        return {
            "id": entry.id,
            "chain_id": entry.chain_id,
            "sequence_no": entry.sequence_no,
            "event_type": entry.event_type,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "actor_id": entry.actor_id,
            "previous_hash": entry.previous_hash,
            "payload_hash": entry.payload_hash,
            "event_hash": entry.event_hash,
            "payload_summary": entry.payload_summary,
            "created_at": entry.created_at
        }

async def run_ledger_corruption_checks() -> bool:
    base_url = os.getenv("BILGEAPI_URL", "http://localhost:8100").rstrip("/")
    api_key = os.getenv("BILGEAPI_API_KEY", "dev-test-key-001")
    
    # Generate completely isolated, unique chain ID
    chain_id = f"test_chain_corrupt_{uuid.uuid4().hex[:12]}"
    print(f"[*] Starting ledger corruption check on isolated chain: {chain_id}")
    
    # ── 1. Create isolated chain entries ──────────────────────────────────────
    print("[*] Creating 3 valid ledger events to build the test chain...")
    async with AsyncSessionLocal() as db:
        repo = SimpleReviewLedgerRepository(db)
        service = ReviewLedgerService(repo)
        
        await service.append_event(
            chain_id=chain_id,
            event_type="TEST_CORRUPT_START",
            entity_type="test_entity",
            entity_id="entity_1",
            actor_id="test_actor",
            payload={"step": "first"}
        )
        
        await service.append_event(
            chain_id=chain_id,
            event_type="TEST_CORRUPT_MIDDLE",
            entity_type="test_entity",
            entity_id="entity_1",
            actor_id="test_actor",
            payload={"step": "second"}
        )
        
        await service.append_event(
            chain_id=chain_id,
            event_type="TEST_CORRUPT_END",
            entity_type="test_entity",
            entity_id="entity_1",
            actor_id="test_actor",
            payload={"step": "third"}
        )

    # ── 2. Verify Initial Integrity ───────────────────────────────────────────
    print("[*] Verifying chain is initially valid...")
    verifier = BilgeAPIHumanGateVerifier(base_url=base_url, api_key=api_key)
    res = await verifier.verify_ledger_integrity(chain_id)
    print(f"[+] Initial verify response: {res}")
    
    if not res.get("valid", False):
        print("[FAIL] Isolated chain is not valid initially.")
        await cleanup_chain(chain_id)
        return False
        
    # Should not raise exception
    try:
        await verifier.assert_approval_allowed(chain_id)
        print("[+] assert_approval_allowed passed on valid ledger.")
    except Exception as e:
        print(f"[FAIL] assert_approval_allowed raised exception on valid chain: {e}")
        await cleanup_chain(chain_id)
        return False

    # ── 3. Corrupt the Chain ──────────────────────────────────────────────────
    print("[*] Corrupting the chain in DB (modifying previous_hash of the second entry)...")
    async with AsyncSessionLocal() as db:
        stmt = select(ReviewLedgerEntryModel).where(
            ReviewLedgerEntryModel.chain_id == chain_id,
            ReviewLedgerEntryModel.sequence_no == 2
        )
        res_db = await db.execute(stmt)
        second_entry = res_db.scalar_one_or_none()
        if not second_entry:
            print("[FAIL] Second entry not found in database.")
            await cleanup_chain(chain_id)
            return False
            
        # Corrupt the previous hash
        second_entry.previous_hash = "corrupted_previous_hash_bogus_12345"
        await db.commit()
        print("[+] Corrupted previous_hash in database.")

    # ── 4. Verify Corruption is Blocked ───────────────────────────────────────
    print("[*] Verifying that corrupted chain is detected and blocked...")
    res_corrupt = await verifier.verify_ledger_integrity(chain_id)
    print(f"[+] Post-corruption verify response: {res_corrupt}")
    
    if res_corrupt.get("valid", True):
        print("[FAIL] Corrupted chain was incorrectly marked as valid.")
        await cleanup_chain(chain_id)
        return False
        
    print("[*] Asserts that assert_approval_allowed raises ValueError on corrupted chain...")
    try:
        await verifier.assert_approval_allowed(chain_id)
        print("[FAIL] assert_approval_allowed did not raise ValueError on corrupted chain.")
        await cleanup_chain(chain_id)
        return False
    except ValueError as e:
        print(f"[+] Success: assert_approval_allowed successfully raised ValueError: {e}")

    # ── 5. Cleanup ────────────────────────────────────────────────────────────
    await cleanup_chain(chain_id)
    print("[SUCCESS] Ledger corruption verification checks passed successfully!")
    return True

async def cleanup_chain(chain_id: str):
    print(f"[*] Cleaning up all database entries for test chain: {chain_id}")
    async with AsyncSessionLocal() as db:
        stmt = delete(ReviewLedgerEntryModel).where(
            ReviewLedgerEntryModel.chain_id == chain_id
        )
        await db.execute(stmt)
        await db.commit()
    print("[+] Database cleanup complete.")

if __name__ == "__main__":
    success = asyncio.run(run_ledger_corruption_checks())
    sys.exit(0 if success else 1)
