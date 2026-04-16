from enum import Enum
from typing import List, Dict

class Role(str, Enum):
    AUDITOR = "auditor"     # Read-only access to logs
    OPERATOR = "operator"   # Can approve and retry, but not replay with deep overrides
    MANAGER = "manager"     # Can do everything including replay with overrides
    ADMIN = "admin"         # System owner

# Define which roles are allowed for critical workflow operations
PERMISSIONS = {
    "workflow:read": [Role.AUDITOR, Role.OPERATOR, Role.MANAGER, Role.ADMIN],
    "workflow:approve": [Role.OPERATOR, Role.MANAGER, Role.ADMIN],
    "workflow:replay": [Role.MANAGER, Role.ADMIN],
    "workflow:override": [Role.MANAGER, Role.ADMIN],
}

def is_authorized(user_role: str, action: str) -> bool:
    """Check if the given role has permission for an action."""
    allowed_roles = PERMISSIONS.get(action, [])
    return user_role in allowed_roles or user_role == Role.ADMIN
