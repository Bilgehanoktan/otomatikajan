"""
Regression tests for libs/auth/rbac.py — Role-Based Access Control.
"""
from libs.auth.rbac import PERMISSIONS, Role, is_authorized


class TestRoles:
    def test_role_values(self):
        assert Role.AUDITOR == "auditor"
        assert Role.OPERATOR == "operator"
        assert Role.MANAGER == "manager"
        assert Role.ADMIN == "admin"

    def test_role_is_string(self):
        assert isinstance(Role.ADMIN, str)
        assert isinstance(Role.AUDITOR, str)


class TestPermissions:
    def test_auditor_can_read(self):
        assert is_authorized(Role.AUDITOR, "workflow:read")

    def test_auditor_cannot_approve(self):
        assert not is_authorized(Role.AUDITOR, "workflow:approve")

    def test_operator_can_approve(self):
        assert is_authorized(Role.OPERATOR, "workflow:approve")

    def test_operator_cannot_replay(self):
        assert not is_authorized(Role.OPERATOR, "workflow:replay")

    def test_manager_can_replay(self):
        assert is_authorized(Role.MANAGER, "workflow:replay")

    def test_manager_can_override(self):
        assert is_authorized(Role.MANAGER, "workflow:override")

    def test_admin_has_full_access(self):
        for action in PERMISSIONS:
            assert is_authorized(Role.ADMIN, action)

    def test_unknown_action_denied_for_non_admin(self):
        assert not is_authorized(Role.OPERATOR, "workflow:delete_all")

    def test_admin_allowed_for_unknown_action(self):
        assert is_authorized(Role.ADMIN, "workflow:unknown_action")
