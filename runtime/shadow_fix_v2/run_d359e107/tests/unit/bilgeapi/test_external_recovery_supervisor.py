import os
import json
import pytest
import time
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from scripts.bilgeapi_supervisor import BilgeApiSupervisor, ALLOWED_COMMANDS

def test_supervisor_initialization():
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file="tmp/supervisor_events.jsonl",
        api_key="test-key",
        mode="test"
    )
    assert sup.url == "http://127.0.0.1:8100/health"
    assert sup.service == "bilgeapi"
    assert sup.cooldown == 300
    assert sup.max_attempts == 2
    assert sup.spool_file == "tmp/supervisor_events.jsonl"
    assert sup.api_key == "test-key"
    assert sup.mode == "test"


@patch("urllib.request.urlopen")
def test_supervisor_health_check_ok(mock_urlopen):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"status": "ok", "service": "bilgeapi"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response

    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file="tmp/supervisor_events.jsonl",
        api_key="test-key",
        mode="test"
    )
    assert sup.check_health() is True


@patch("urllib.request.urlopen")
def test_supervisor_health_check_fail(mock_urlopen):
    mock_urlopen.side_effect = URLError("Connection refused")

    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file="tmp/supervisor_events.jsonl",
        api_key="test-key",
        mode="test"
    )
    assert sup.check_health() is False


def test_supervisor_state_management(tmp_path):
    spool_file = str(tmp_path / "supervisor_events.jsonl")
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file=spool_file,
        api_key="test-key",
        mode="test"
    )

    state = sup.get_state()
    assert state["attempts"] == 0
    assert state["last_attempt_time"] == 0.0

    state["attempts"] = 1
    state["last_attempt_time"] = 12345.6
    sup.save_state(state)

    state2 = sup.get_state()
    assert state2["attempts"] == 1
    assert state2["last_attempt_time"] == 12345.6


@patch("urllib.request.urlopen")
def test_supervisor_cooldown_blocking(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = URLError("Connection refused")
    
    spool_file = str(tmp_path / "supervisor_events.jsonl")
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file=spool_file,
        api_key="test-key",
        mode="test"
    )

    state = {
        "attempts": 1,
        "last_attempt_time": time.time() - 50
    }
    sup.save_state(state)

    event = sup.execute_recovery_cycle()
    assert event is None


@patch("urllib.request.urlopen")
def test_supervisor_max_attempts_blocking(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = URLError("Connection refused")
    
    spool_file = str(tmp_path / "supervisor_events.jsonl")
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file=spool_file,
        api_key="test-key",
        mode="test"
    )

    state = {
        "attempts": 2,
        "last_attempt_time": time.time() - 400
    }
    sup.save_state(state)

    event = sup.execute_recovery_cycle()
    assert event is None


@patch("urllib.request.urlopen")
def test_supervisor_successful_recovery_run(mock_urlopen, tmp_path):
    mock_urlopen.side_effect = URLError("Connection refused")
    
    spool_file = str(tmp_path / "supervisor_events.jsonl")
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file=spool_file,
        api_key="test-key",
        mode="test"
    )

    event = sup.execute_recovery_cycle()
    assert event is not None
    assert event["event_type"] == "SUPERVISOR_RECOVERY_COMPLETED"
    assert event["service_name"] == "bilgeapi"
    assert event["attempt_no"] == 1
    assert event["status"] == "success"
    assert "MOCK: Command" in event["output"]

    assert os.path.exists(spool_file)
    with open(spool_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        spooled_event = json.loads(lines[0])
        assert spooled_event["attempt_no"] == 1

    state = sup.get_state()
    assert state["attempts"] == 1
    assert state["last_attempt_time"] > 0.0


@patch("urllib.request.urlopen")
def test_supervisor_spool_flush(mock_urlopen, tmp_path):
    spool_file = str(tmp_path / "supervisor_events.jsonl")
    sup = BilgeApiSupervisor(
        url="http://127.0.0.1:8100/health",
        service="bilgeapi",
        cooldown=300,
        max_attempts=2,
        spool_file=spool_file,
        api_key="test-key",
        mode="test"
    )
    
    event = {
        "event_type": "SUPERVISOR_RECOVERY_FAILED",
        "timestamp": "2026-06-10T19:00:00Z",
        "service_name": "bilgeapi",
        "attempt_no": 1,
        "output": "",
        "error": "Timeout",
        "status": "failed"
    }
    sup.spool_event(event)
    assert os.path.exists(spool_file)

    mock_health_response = MagicMock()
    mock_health_response.status = 200
    mock_health_response.read.return_value = b'{"status": "ok"}'

    mock_report_response = MagicMock()
    mock_report_response.status = 200
    mock_report_response.read.return_value = b'{"status": "success", "processed_events": 1}'

    mock_urlopen.side_effect = [
        MagicMock(__enter__=MagicMock(return_value=mock_health_response)),
        MagicMock(__enter__=MagicMock(return_value=mock_report_response))
    ]

    sup.execute_recovery_cycle()

    assert not os.path.exists(spool_file)
    assert sup.get_state()["attempts"] == 0
