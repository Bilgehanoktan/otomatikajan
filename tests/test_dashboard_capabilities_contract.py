from pathlib import Path


def test_dashboard_should_not_default_capabilities_to_true_without_backend_confirmation() -> None:
    src = Path("dashboard/core_app_v2.js").read_text(encoding="utf-8")

    assert "let CAPS =" in src
    # Başlangıç değeri false olmalı (hardening)
    assert "supports_cancel: false" in src
    assert "supports_pause: false" in src
    assert "supports_resume: false" in src


def test_dashboard_should_use_explicit_capabilities_endpoint() -> None:
    src = Path("dashboard/core_app_v2.js").read_text(encoding="utf-8")

    assert "/tasks/capabilities" in src, (
        "Dashboard queue capability bilgisini explicit endpoint'ten çekmeli."
    )
