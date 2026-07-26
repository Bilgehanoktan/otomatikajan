from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SESSION_MODULES = (
    ROOT / "libs" / "db" / "session.py",
    ROOT / "apps" / "bilgeapi" / "libs" / "db" / "session.py",
)


def test_ui_repair_baseline_seed_uses_runtime_service_namespace():
    for module_path in SESSION_MODULES:
        source = module_path.read_text(encoding="utf-8")
        assert "from services.ui_repair.baseline_bootstrap import UIRepairBaselineBootstrapper" in source
        assert "from bilgeapi.services.ui_repair.baseline_bootstrap" not in source
