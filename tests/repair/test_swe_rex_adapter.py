from services.repair.swe_rex_adapter import describe_swe_rex_backend, resolve_sandbox_backend


def test_swe_rex_adapter_describes_optional_backend():
    data = describe_swe_rex_backend()

    assert data["backend"] == "swe_rex"
    assert data["status"] in {"READY", "DEFERRED"}


def test_unknown_sandbox_backend_falls_back(monkeypatch):
    monkeypatch.setenv("SANDBOX_BACKEND", "unknown")

    data = resolve_sandbox_backend()

    assert data["backend"] == "local_temp"
    assert data["status"] == "FALLBACK"

