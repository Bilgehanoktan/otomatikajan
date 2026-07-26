import sys
from types import ModuleType


def test_release_gate_cli_loads_canonical_bilgeapi_module(monkeypatch):
    from apps.bilgeapi.scripts import run_release_gate

    canonical_module = ModuleType("bilgeapi.main")
    canonical_app = object()
    canonical_module.app = canonical_app
    monkeypatch.setitem(sys.modules, "bilgeapi.main", canonical_module)

    assert run_release_gate.get_application() is canonical_app

