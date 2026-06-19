from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import Response
from sqlalchemy import text

from libs.db import session as db_session_module
from libs.db.models.governance_models import (
    GovernanceProofEventRecord,
    GovernanceProofSnapshotRecord,
    GovernorDecisionQuality,
    GovernorDomain,
    GovernorOutcomeRecord,
    GovernorOutcomeType,
    ProofEventType,
    ProofSealStatus,
)
from services.workflow_api import governance_router, governor_router


@pytest.fixture
async def patched_router_sessions(db_session, monkeypatch):
    async_session_local = lambda: db_session
    monkeypatch.setattr(db_session_module, "AsyncSessionLocal", async_session_local)
    monkeypatch.setattr(governance_router, "AsyncSessionLocal", async_session_local)
    monkeypatch.setattr(governor_router, "AsyncSessionLocal", async_session_local)
    yield


@pytest.mark.asyncio
async def test_policy_proposals_endpoint_tolerates_legacy_schema(db_session, patched_router_sessions):
    await db_session.execute(text("DROP TABLE policy_proposals"))
    await db_session.execute(
        text(
            """
            CREATE TABLE policy_proposals (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                policy_code TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'PROPOSED',
                created_at TEXT NOT NULL
            )
            """
        )
    )

    proposal_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    await db_session.execute(
        text(
            """
            INSERT INTO policy_proposals (id, title, description, policy_code, status, created_at)
            VALUES (:id, :title, :description, :policy_code, :status, :created_at)
            """
        ),
        {
            "id": proposal_id,
            "title": "Legacy Proposal",
            "description": "Backfilled from old schema",
            "policy_code": "ALLOW_AUTO_REPAIR=true",
            "status": "PROPOSED",
            "created_at": created_at,
        },
    )
    await db_session.commit()

    response = Response()
    payload = await governance_router.list_policy_proposals(response)

    assert len(payload) == 1
    assert payload[0].id == proposal_id
    assert payload[0].scope == "AUTONOMOUS_LEARNING"
    assert payload[0].parameter == "Legacy Proposal"
    assert payload[0].proposed_value == "ALLOW_AUTO_REPAIR=true"


@pytest.mark.asyncio
async def test_governor_scorecard_counts_correct_decisions(db_session, patched_router_sessions):
    now = datetime.now(UTC)
    db_session.add(
        GovernorOutcomeRecord(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            action_id=uuid.uuid4(),
            decision="AUTO_REPLAY_CANDIDATE",
            final_outcome=GovernorOutcomeType.SUCCESS,
            quality=GovernorDecisionQuality.CORRECT,
            was_successful=1,
            operator_overrode=0,
            operator_agreed=1,
            resolution_latency_seconds=12,
            reason_codes=["MATCHED_EXPECTATION"],
            created_at=now,
        )
    )
    await db_session.commit()

    payload = await governor_router.get_scorecard(
        window_days=7,
        identity={"id": uuid.uuid4(), "type": "operator", "role": "OPERATOR"},
    )

    assert payload.total_decisions == 1
    assert payload.correct_decisions == 1
    assert payload.accuracy == 100.0
    assert payload.replay_success_rate == 100.0


@pytest.mark.asyncio
async def test_proof_snapshot_detail_returns_persisted_snapshot(db_session, patched_router_sessions):
    snapshot_id = uuid.uuid4()
    db_session.add(
        GovernanceProofSnapshotRecord(
            id=snapshot_id,
            snapshot_name="TEST_SNAPSHOT",
            start_chain_index=10,
            end_chain_index=19,
            event_count=10,
            merkle_root="a" * 64,
            snapshot_hash="b" * 64,
            seal_status=ProofSealStatus.SEALED,
            created_at=datetime.now(UTC),
            sealed_by="TEST_OPERATOR",
        )
    )
    await db_session.commit()

    payload = await governor_router.get_proof_snapshot_detail(
        snapshot_id=str(snapshot_id),
        identity={"id": uuid.uuid4(), "type": "operator", "role": "OPERATOR"},
    )

    assert payload.id == str(snapshot_id)
    assert payload.start_chain_index == 10
    assert payload.end_chain_index == 19
    assert payload.sealed_by == "TEST_OPERATOR"


@pytest.mark.asyncio
async def test_proof_snapshot_detail_returns_derived_snapshot(db_session, patched_router_sessions):
    db_session.add_all(
        [
            GovernanceProofEventRecord(
                id=uuid.uuid4(),
                event_type=ProofEventType.GOVERNOR_DECISION,
                domain=GovernorDomain.WORKFLOW,
                entity_id="wf-1",
                payload_hash="c" * 64,
                payload_canonical='{"decision":"approve"}',
                prev_event_hash=None,
                event_hash="d" * 64,
                chain_index=1,
                created_at=datetime.now(UTC),
                created_by="SYSTEM",
            ),
            GovernanceProofEventRecord(
                id=uuid.uuid4(),
                event_type=ProofEventType.POLICY_EVOLUTION,
                domain=GovernorDomain.POLICY,
                entity_id="policy-1",
                payload_hash="e" * 64,
                payload_canonical='{"rule":"tighten"}',
                prev_event_hash="d" * 64,
                event_hash="f" * 64,
                chain_index=2,
                created_at=datetime.now(UTC),
                created_by="SYSTEM",
            ),
        ]
    )
    await db_session.commit()

    payload = await governor_router.get_proof_snapshot_detail(
        snapshot_id="derived-local-proof-snapshot",
        identity={"id": uuid.uuid4(), "type": "operator", "role": "OPERATOR"},
    )

    assert payload.id == "derived-local-proof-snapshot"
    assert payload.event_count == 2
    assert payload.start_chain_index == 1
    assert payload.end_chain_index == 2
    assert payload.seal_status == "SEALED"
