import os

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
        pytest.skip(f"Live Phase 3.4 smoke skipped: API unavailable at {BASE_URL} ({exc})")
    assert response.status_code == 200, response.text
    payload = response.json()
    token = payload.get("access_token")
    assert token, payload
    return session, {"Authorization": f"Bearer {token}"}


def test_phase34_repair_lab_and_self_heal_surfaces():
    session, headers = _login()

    benchmarks = session.get(f"{BASE_URL}/repair-lab/benchmarks", timeout=20)
    assert benchmarks.status_code == 200, benchmarks.text
    assert isinstance(benchmarks.json(), list), benchmarks.text

    tournaments = session.get(f"{BASE_URL}/repair-lab/tournaments", timeout=20)
    assert tournaments.status_code == 200, tournaments.text
    assert isinstance(tournaments.json(), list), tournaments.text

    matrix = session.get(
        f"{BASE_URL}/repair-lab/verifiers/matrix?tournament_id=t-demo-001",
        timeout=20,
    )
    assert matrix.status_code == 200, matrix.text
    matrix_payload = matrix.json()
    assert "verifiers" in matrix_payload, matrix_payload
    assert "candidates" in matrix_payload, matrix_payload

    run_response = session.post(
        f"{BASE_URL}/repair-lab/run",
        headers=headers,
        timeout=20,
    )
    assert run_response.status_code == 200, run_response.text
    run_payload = run_response.json()
    assert run_payload.get("status") in {"started", "ok"}, run_payload

    improvements = session.get(
        f"{BASE_URL}/improvements?_end=20&_order=desc&_sort=created_at&_start=0",
        timeout=20,
    )
    assert improvements.status_code == 200, improvements.text
    assert isinstance(improvements.json(), list), improvements.text

    health_events = session.get(
        f"{BASE_URL}/health/events/stream?since_seq=0&limit=10",
        timeout=20,
    )
    assert health_events.status_code == 200, health_events.text
    events_payload = health_events.json()
    assert isinstance(events_payload.get("events"), list), events_payload
