#!/usr/bin/env python3
"""
verify_governor_e2e.py — Phase 31F E2E Smoke & Bridge Idempotency Verification
=============================================================================
Checks:
1. Intake API endpoint (POST /v1/watchdog/findings/intake) creates system finding.
2. Bridge Mapping table records the source -> bilgeapi_finding_id association.
3. Second submission returns cached/idempotent status.
4. Database verification:
   - Exactly 1 mapping in bilgeapi_bridge_mappings for the source.
   - Exactly 1 finding in bilgeapi_system_findings.
   - SYSTEM_FINDING_CREATED and SYSTEM_FINDING_DEDUPED entries exist in review ledger.
"""

import os
import sys
import asyncio
import httpx
import uuid
from pathlib import Path

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
from apps.bilgeapi.models.database import BilgeAPIBridgeMappingModel, SystemFindingModel, ReviewLedgerEntryModel
from sqlalchemy import select

async def run_e2e_checks() -> bool:
    base_url = os.getenv("BILGEAPI_URL", "http://localhost:8100").rstrip("/")
    api_key = os.getenv("BILGEAPI_API_KEY", "dev-test-key-001")
    
    source_type = "TASKFLOW_RUN_HARDENING"
    source_id = f"run_hardening_{uuid.uuid4().hex[:8]}"
    title = f"Hardening E2E Test Signal - {source_id}"
    
    print(f"[*] Starting E2E smoke checks for source: {source_type}:{source_id}")
    print(f"[*] BilgeAPI URL: {base_url}")
    
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "source_type": source_type,
        "source_id": source_id,
        "title": title,
        "description": "Hardening phase verify_governor_e2e.py run signal.",
        "severity": "HIGH",
        "evidence_summary": {"scope": "phase31f_hardening"},
        "recommended_action": "isolate_node",
        "tenant_id": "hardening_tenant"
    }
    
    # ── 1. First Intake Call via Bridge ───────────────────────────────────────
    print("[*] Submitting first intake signal via BilgeAPIBridge...")
    from services.integrations.bilgeapi_bridge import BilgeAPIBridge
    
    async with AsyncSessionLocal() as db:
        bridge = BilgeAPIBridge(db_session=db, base_url=base_url, api_key=api_key)
        try:
            res = await bridge.forward_finding_intake(
                source_type=source_type,
                source_id=source_id,
                title=title,
                description="Hardening phase verify_governor_e2e.py run signal.",
                severity="HIGH",
                evidence_summary={"scope": "phase31f_hardening"},
                recommended_action="isolate_node",
                tenant_id="hardening_tenant"
            )
            data = res
        except Exception as e:
            print(f"[FAIL] BilgeAPIBridge call failed: {e}")
            return False
            
    print(f"[+] First intake response: {data}")
    finding_id = data.get("finding_id")
    if not finding_id:
        print("[FAIL] Response did not contain finding_id.")
        return False
        
    if not data.get("created", False):
        print("[FAIL] Expected 'created' to be True on first intake.")
        return False

    # ── 2. Second Intake Call (Server-side Idempotency check) ──────────────────
    print("[*] Submitting second intake signal (raw HTTP to trigger server deduplication)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(f"{base_url}/v1/watchdog/findings/intake", headers=headers, json=payload)
        if response.status_code != 200:
            print(f"[FAIL] Second intake request failed with status {response.status_code}: {response.text}")
            return False
        data_cached = response.json()
        
    print(f"[+] Second response (server deduplicated): {data_cached}")
    if data_cached.get("finding_id") != finding_id:
        print(f"[FAIL] Finding ID mismatch on second call. Expected {finding_id}, got {data_cached.get('finding_id')}")
        return False
        
    if not data_cached.get("deduped", False):
        print("[FAIL] Expected 'deduped' to be True on second intake.")
        return False

    # ── 3. Database Integrity Verifications ────────────────────────────────────
    print("[*] Connecting to database for verifying records...")
    async with AsyncSessionLocal() as db:
        # Check mapping count
        stmt_mapping = select(BilgeAPIBridgeMappingModel).where(
            BilgeAPIBridgeMappingModel.source_type == source_type,
            BilgeAPIBridgeMappingModel.source_id == source_id
        )
        mappings = (await db.execute(stmt_mapping)).scalars().all()
        print(f"[+] Found {len(mappings)} mapping record(s) in database.")
        if len(mappings) != 1:
            print(f"[FAIL] Mapping count is not exactly 1 (found {len(mappings)}).")
            return False
        
        # Verify bridge mapping values
        map_record = mappings[0]
        if map_record.bilgeapi_finding_id != finding_id:
            print(f"[FAIL] Database mapping finding_id mismatch. Expected {finding_id}, got {map_record.bilgeapi_finding_id}")
            return False
            
        # Check finding count
        stmt_finding = select(SystemFindingModel).where(
            SystemFindingModel.source_type == source_type,
            SystemFindingModel.source_id == source_id
        )
        findings = (await db.execute(stmt_finding)).scalars().all()
        print(f"[+] Found {len(findings)} finding record(s) in database.")
        if len(findings) != 1:
            print(f"[FAIL] Finding count is not exactly 1 (found {len(findings)}).")
            return False
            
        # Check ledger events
        stmt_ledger = select(ReviewLedgerEntryModel).where(
            ReviewLedgerEntryModel.chain_id == "bilgeapi-watchdog",
            ReviewLedgerEntryModel.entity_id == finding_id
        ).order_by(ReviewLedgerEntryModel.sequence_no.asc())
        ledger_entries = (await db.execute(stmt_ledger)).scalars().all()
        
        print(f"[+] Found {len(ledger_entries)} review ledger entries for finding {finding_id}.")
        event_types = [entry.event_type for entry in ledger_entries]
        print(f"[+] Ledger events in order: {event_types}")
        
        if "SYSTEM_FINDING_CREATED" not in event_types:
            print("[FAIL] Ledger is missing SYSTEM_FINDING_CREATED event.")
            return False
            
        if "SYSTEM_FINDING_DEDUPED" not in event_types:
            print("[FAIL] Ledger is missing SYSTEM_FINDING_DEDUPED event.")
            return False

    print("[SUCCESS] All E2E smoke and idempotency checks passed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_e2e_checks())
    sys.exit(0 if success else 1)
