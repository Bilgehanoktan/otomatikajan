import pytest

from services.taskflow.taskflow_state_machine import can_transition_step, transition_step


def test_valid_step_transitions():
    assert can_transition_step("PENDING", "READY")
    assert can_transition_step("READY", "RUNNING")
    assert can_transition_step("RUNNING", "SUCCEEDED")
    assert can_transition_step("RUNNING", "FAILED")
    assert can_transition_step("FAILED", "RETRYING")


def test_failed_step_cannot_succeed_directly():
    assert not can_transition_step("FAILED", "SUCCEEDED")
    with pytest.raises(ValueError):
        transition_step("FAILED", "SUCCEEDED")


def test_blocked_step_cannot_become_ready():
    assert not can_transition_step("BLOCKED", "READY")

