import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from libs.db.base import Base
from apps.bilgeapi.models.database import BilgeAPIBridgeMappingModel
from services.integrations.bilgeapi_bridge import BilgeAPIBridge
from services.repair.bilgeapi_human_gate_context import BilgeAPIHumanGateVerifier

@pytest.mark.asyncio
async def test_bilgeapi_platform_bridge_and_human_gate_context():
    # 1. Setup in-memory SQLite DB
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        bridge = BilgeAPIBridge(db_session=session)
        
        # 2. Test forward_finding_intake (Mocking HTTP call)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "finding_id": "fnd_test_999",
            "created": True,
            "deduped": False
        }
        mock_response.raise_for_status = MagicMock()

        # Patch httpx.AsyncClient.post
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # Forward finding first time
            res = await bridge.forward_finding_intake(
                source_type="TASKFLOW_RUN",
                source_id="run_abc123",
                title="Stuck taskflow",
                description="Taskflow remained in running state",
                severity="HIGH"
            )
            
            assert res["status"] == "success"
            assert res["finding_id"] == "fnd_test_999"
            assert res["created"] is True
            assert res["deduped"] is False
            
            mock_post.assert_called_once()
            
            # Verify mapping exists in DB
            stmt = select(BilgeAPIBridgeMappingModel).where(
                BilgeAPIBridgeMappingModel.source_type == "TASKFLOW_RUN",
                BilgeAPIBridgeMappingModel.source_id == "run_abc123"
            )
            mapping = (await session.execute(stmt)).scalar_one_or_none()
            assert mapping is not None
            assert mapping.bilgeapi_finding_id == "fnd_test_999"
            assert mapping.status == "FORWARDED"

            # Reset mock and call a second time (should trigger idempotency/db cache bypass)
            mock_post.reset_mock()
            
            res_cached = await bridge.forward_finding_intake(
                source_type="TASKFLOW_RUN",
                source_id="run_abc123",
                title="Stuck taskflow",
                description="Taskflow remained in running state",
                severity="HIGH"
            )
            
            assert res_cached["status"] == "success"
            assert res_cached["finding_id"] == "fnd_test_999"
            assert res_cached["created"] is False
            assert res_cached["deduped"] is True
            
            # Since it was cached, mock_post should NOT have been called again!
            mock_post.assert_not_called()

        # 3. Test associate_improvement_flow
        await bridge.associate_improvement_flow(
            source_type="TASKFLOW_RUN",
            source_id="run_abc123",
            research_id="res_abc",
            proposal_id="prop_abc",
            pr_draft_id="pr_abc",
            verification_id="ver_abc",
            ledger_chain_id="chain_abc"
        )
        
        # Verify mapping updated
        await session.refresh(mapping)
        assert mapping.bilgeapi_research_id == "res_abc"
        assert mapping.bilgeapi_proposal_id == "prop_abc"
        assert mapping.bilgeapi_pr_draft_id == "pr_abc"
        assert mapping.bilgeapi_verification_id == "ver_abc"
        assert mapping.bilgeapi_ledger_chain_id == "chain_abc"

        # 4. Test Human Gate Verifier
        verifier = BilgeAPIHumanGateVerifier()
        
        # Test valid ledger chain
        mock_valid_response = MagicMock()
        mock_valid_response.status_code = 200
        mock_valid_response.json.return_value = {
            "valid": True,
            "entry_count": 3,
            "issues": []
        }
        mock_valid_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_valid_response
            
            # Should run successfully without raising
            await verifier.assert_approval_allowed("chain_abc")
            mock_get.assert_called_once_with(
                "http://localhost:8100/v1/review-ledger/chains/chain_abc/verify",
                headers={"X-API-Key": "dev-test-key-001"}
            )
            
        # Test invalid ledger chain
        mock_invalid_response = MagicMock()
        mock_invalid_response.status_code = 200
        mock_invalid_response.json.return_value = {
            "valid": False,
            "entry_count": 3,
            "issues": [{"type": "INVALID_PREVIOUS_HASH", "sequence_no": 2}]
        }
        mock_invalid_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_invalid_response
            
            # Should raise ValueError indicating ledger chain integrity failure
            with pytest.raises(ValueError) as excinfo:
                await verifier.assert_approval_allowed("chain_abc")
            
            assert "integrity verification failed" in str(excinfo.value)
            assert "INVALID_PREVIOUS_HASH" in str(excinfo.value)

    await engine.dispose()
