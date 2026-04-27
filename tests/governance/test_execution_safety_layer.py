import pytest
from datetime import datetime, timedelta, timezone
from services.governance.approval_governor_execution_policy import execution_policy

class MockCase:
    def __init__(self, **kwargs):
        self.risk_class = kwargs.get("risk_class", "LOW")
        self.pending_reason = kwargs.get("pending_reason", "PENDING_APPROVAL")
        self.requires_prime = kwargs.get("requires_prime", False)
        self.requires_quorum = kwargs.get("requires_quorum", False)
        self.has_safety_lock = kwargs.get("has_safety_lock", False)
        self.stale_seconds = kwargs.get("stale_seconds", 0)

def test_auto_approve_policy():
    # Should allow
    case_low = MockCase(risk_class="LOW", pending_reason="PENDING_APPROVAL")
    allowed, _ = execution_policy.can_auto_approve(case_low)
    assert allowed == True

    # Should block
    case_high = MockCase(risk_class="HIGH")
    allowed, msg = execution_policy.can_auto_approve(case_high)
    assert allowed == False
    assert "Yüksek riskli" in msg

    case_locked = MockCase(risk_class="LOW", pending_reason="SAFETY_LOCK")
    allowed, msg = execution_policy.can_auto_approve(case_locked)
    assert allowed == False

def test_auto_replay_policy():
    case_medium = MockCase(risk_class="MEDIUM")
    allowed, _ = execution_policy.can_auto_replay(case_medium)
    assert allowed == True

    case_critical = MockCase(risk_class="CRITICAL")
    allowed, msg = execution_policy.can_auto_replay(case_critical)
    assert allowed == False

def test_archive_policy():
    case_stale = MockCase(requires_prime=True, stale_seconds=86400 * 4)
    allowed, _ = execution_policy.can_archive(case_stale)
    assert allowed == True

    case_fresh_escalation = MockCase(requires_prime=True, stale_seconds=86400 * 1)
    allowed, msg = execution_policy.can_archive(case_fresh_escalation)
    assert allowed == False

def test_override_policy():
    case = MockCase(risk_class="HIGH")
    
    # Missing role
    allowed, _ = execution_policy.can_override(case, "", "approve", "Justification length is over twenty characters")
    assert allowed == False
    
    # Short justification
    allowed, _ = execution_policy.can_override(case, "SOVEREIGN_PRIME", "approve", "Short")
    assert allowed == False
    
    # Critical requires prime/quorum
    case_critical = MockCase(risk_class="CRITICAL")
    allowed, _ = execution_policy.can_override(case_critical, "HUMAN_OPERATOR", "approve", "This is a valid long justification text here")
    assert allowed == False
    
    # Valid override
    allowed, _ = execution_policy.can_override(case_critical, "SOVEREIGN_PRIME", "approve", "This is a valid long justification text here")
    assert allowed == True

def test_restore_policy():
    case = MockCase(has_safety_lock=False)
    
    # Expired window
    archived_at = datetime.now(timezone.utc) - timedelta(hours=25)
    allowed, _ = execution_policy.can_restore(case, "HUMAN_OPERATOR", archived_at)
    assert allowed == False
    
    # Valid window
    archived_at_valid = datetime.now(timezone.utc) - timedelta(hours=5)
    allowed, _ = execution_policy.can_restore(case, "HUMAN_OPERATOR", archived_at_valid)
    assert allowed == True
    
    # Safety lock needs prime
    case_locked = MockCase(has_safety_lock=True)
    allowed, _ = execution_policy.can_restore(case_locked, "HUMAN_OPERATOR", archived_at_valid)
    assert allowed == False
    
    allowed, _ = execution_policy.can_restore(case_locked, "SOVEREIGN_PRIME", archived_at_valid)
    assert allowed == True
