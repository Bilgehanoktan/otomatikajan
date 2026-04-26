"""
Security Test: RBAC & Auth Unit Verification (Phase 9.4)
Verifies that admin gates and user authentication logic are robust.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT)

from services.auth.jwt_auth import get_current_user, AuthService, AccessControlService
from libs.db.models import Operator

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
    print("\n[SECURITY] Testing get_current_user with no token...")
    
    # Mock Request with no auth headers
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.cookies = {}
    mock_db = AsyncMock()

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request=mock_request, db=mock_db)
    
    assert exc.value.status_code == 401
    print("  - Missing token BLOCKED with 401 (Correct)")

@pytest.mark.asyncio
async def test_auth_service_token_validation():
    print("\n[SECURITY] Testing AuthService token validation...")
    
    auth_service = AuthService()
    mock_db = AsyncMock()
    
    # Simulate invalid token
    with pytest.raises(HTTPException) as exc:
        await auth_service.get_identity_from_token(mock_db, "invalid.token.here")
    
    assert exc.value.status_code == 401
    assert "Geçersiz token" in exc.value.detail
    print("  - Invalid token signature BLOCKED with 401 (Correct)")

if __name__ == "__main__":
    # Note: Running this via pytest is preferred
    print("Run this test using: pytest tests/security/test_rbac_unit.py")
