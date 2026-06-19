from __future__ import annotations

import importlib.util
import os


def swe_rex_available() -> bool:
    return importlib.util.find_spec("swerex") is not None or importlib.util.find_spec("swe_rex") is not None


def selected_sandbox_backend() -> str:
    return os.getenv("SANDBOX_BACKEND", "local_temp").strip().lower() or "local_temp"


def resolve_sandbox_backend() -> dict:
    selected = selected_sandbox_backend()
    if selected == "swe_rex" and not swe_rex_available():
        return {
            "backend": "local_temp",
            "requested_backend": "swe_rex",
            "available": False,
            "status": "FALLBACK",
            "reason": "SWE-ReX paketi kurulu degil; local_temp sandbox kullanilmali.",
        }
    if selected not in {"local_temp", "docker", "swe_rex"}:
        return {
            "backend": "local_temp",
            "requested_backend": selected,
            "available": False,
            "status": "FALLBACK",
            "reason": "Bilinmeyen SANDBOX_BACKEND; local_temp sandbox kullanilmali.",
        }
    return {
        "backend": selected,
        "requested_backend": selected,
        "available": selected != "swe_rex" or swe_rex_available(),
        "status": "READY",
        "reason": "Sandbox backend cozumlendi.",
    }


def describe_swe_rex_backend() -> dict:
    return {
        "backend": "swe_rex",
        "available": swe_rex_available(),
        "status": "READY" if swe_rex_available() else "DEFERRED",
        "reason": "SWE-ReX gercek backend entegrasyonu paket kurulumuna baglidir.",
    }

