import os
import time
import uuid

import pytest
import requests


BASE_URL = os.getenv("PHASE3_BASE_URL", "http://127.0.0.1:8000/api/v1")
ADMIN_EMAIL = os.getenv("PHASE3_ADMIN_EMAIL", "admin@sovereign.agi")
ADMIN_PASSWORD = os.getenv("PHASE3_ADMIN_PASSWORD", "admin1234")


def _login() -> tuple[requests.Session, dict[str, str]]:
    session = requests.Session()
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=20,
        )
    except requests.RequestException as exc:
        pytest.skip(f"Live Phase 3 smoke skipped: API unavailable at {BASE_URL} ({exc})")
    assert response.status_code == 200, response.text
    payload = response.json()
    token = payload.get("access_token")
    assert token, payload
    return session, {"Authorization": f"Bearer {token}"}


def _poll_workflow_detail(
    session: requests.Session,
    headers: dict[str, str],
    workflow_id: str,
    timeout_s: int = 20,
) -> dict:
    deadline = time.time() + timeout_s
    last_payload: dict = {}
    while time.time() < deadline:
        response = session.get(
            f"{BASE_URL}/workflows/{workflow_id}",
            headers=headers,
            timeout=20,
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        last_payload = payload
        has_signal = bool(payload.get("steps")) or bool(payload.get("history"))
        if has_signal or payload.get("status") not in ("queued", "pending"):
            return payload
        time.sleep(2)
    return last_payload


def test_phase3_live_workflow_and_governance_smoke():
    session, headers = _login()

    title = f"phase3-smoke-{uuid.uuid4().hex[:8]}"
    create_response = session.post(
        f"{BASE_URL}/workflows",
        json={
            "title": title,
            "description": "Phase 3.3 live smoke validation",
            "workflow_template": "default",
            "quality_profile": "standard",
            "priority": "medium",
        },
        headers=headers,
        timeout=20,
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    workflow_id = created.get("id")
    assert workflow_id, created
    assert created.get("status") == "queued", created

    list_response = session.get(
        f"{BASE_URL}/workflows?limit=10&offset=0",
        headers=headers,
        timeout=20,
    )
    assert list_response.status_code == 200, list_response.text
    workflows = list_response.json()
    assert any(item.get("id") == workflow_id for item in workflows), workflows[:3]

    detail = _poll_workflow_detail(session, headers, workflow_id)
    assert detail.get("id") == workflow_id, detail
    assert detail.get("name") == title, detail
    assert "status" in detail, detail

    stats_response = session.get(
        f"{BASE_URL}/workflows/stats/summary",
        headers=headers,
        timeout=20,
    )
    assert stats_response.status_code == 200, stats_response.text
    stats = stats_response.json()
    assert stats.get("total", 0) >= 1, stats
    assert "pending" in stats, stats
    assert "success_rate_pct" in stats, stats

    events_response = session.get(
        f"{BASE_URL}/health/events/stream?since_seq=0&limit=10",
        timeout=20,
    )
    assert events_response.status_code == 200, events_response.text
    events = events_response.json()
    assert isinstance(events.get("events"), list), events

    incidents_response = session.get(
        f"{BASE_URL}/governance/incidents?_end=10&_order=desc&_sort=created_at&_start=0",
        headers=headers,
        timeout=20,
    )
    assert incidents_response.status_code == 200, incidents_response.text
    assert isinstance(incidents_response.json(), list), incidents_response.text

    approvals_response = session.get(
        f"{BASE_URL}/governance/approvals?_end=10&_start=0&status=pending",
        headers=headers,
        timeout=20,
    )
    assert approvals_response.status_code == 200, approvals_response.text
    assert isinstance(approvals_response.json(), list), approvals_response.text

    proof_response = session.get(
        f"{BASE_URL}/governance/governor/proof/snapshots",
        headers=headers,
        timeout=20,
    )
    assert proof_response.status_code == 200, proof_response.text
    assert isinstance(proof_response.json(), list), proof_response.text
