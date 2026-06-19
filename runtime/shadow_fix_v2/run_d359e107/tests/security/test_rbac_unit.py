"""
Security Test: RBAC & Auth Unit Verification (Phase 9.4)
Verifies that admin gates and user authentication logic are robust.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from services.auth.jwt_auth import AccessControlService, AuthService, get_current_user


@pytest.mark.asyncio
async def test_prime_role_permission_short_circuit():
    allowed, reason = await AccessControlService.is_allowed(
        db=AsyncMock(),
        identity_id=MagicMock(),
        identity_type="operator",
        permission="identity.manage",
        role="SOVEREIGN_PRIME",
    )

    assert allowed is True
    assert "PRIME" in reason


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.cookies = {}
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=mock_request, db=mock_db)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_token_validation():
    auth_service = AuthService()
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await auth_service.get_identity_from_token(mock_db, "invalid.token.here")

    assert exc.value.status_code == 401
    assert "Geçersiz token" in exc.value.detail


def test_permission_alias_candidates():
    candidates = AccessControlService._permission_candidates("approval.decide")
    assert "approval.decide" in candidates
    assert "approveall.decide" in candidates


def test_baseline_role_policy_operator():
    assert AccessControlService._has_baseline_permission("operator", "workflow.approve") is True
    assert AccessControlService._has_baseline_permission("operator", "approval.decide") is True
    assert AccessControlService._has_baseline_permission("operator", "incident.view") is True


def test_baseline_role_policy_observer():
    assert AccessControlService._has_baseline_permission("AUDIT_OBSERVER", "incident.view") is True
    assert AccessControlService._has_baseline_permission("AUDIT_OBSERVER", "workflow.approve") is False

