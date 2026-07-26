import inspect

from bilgeapi.config import settings
from bilgeapi.repositories.memory import InMemoryReleaseCheckRepository
from bilgeapi.services.release import BilgeAPIReleaseGate


def test_production_blocks_known_development_key_hash(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("BILGEAPI_AUTH_MODE", "api_key")
    monkeypatch.setenv("BILGEAPI_STATIC_KEYS", "")
    monkeypatch.setenv(
        "BILGEAPI_STATIC_KEY_HASHES",
        "f9dc6e1a25f1c6425f71232456bc179fae16036d0eae50b05dd9067f2e833f76:ADMIN",
    )
    gate = BilgeAPIReleaseGate(InMemoryReleaseCheckRepository())

    assert settings.APP_ENV == "production"
    assert "known_development_hashes" in inspect.getsource(gate.check_security_config)
    result = gate.check_security_config()

    assert any(
        "known development API key" in blocker
        for blocker in result["blockers"]
    ), result["blockers"]
