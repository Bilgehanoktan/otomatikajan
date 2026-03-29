from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


def test_lifespan_zombie_cleanup_block_should_be_top_level_after_db_init():
    """
    Zombie cleanup bloğu, DB init başarı/başarısızlık akışından sonra
    lifespan içinde top-level çalışmalı.
    """
    # Modülerleştirme sonrası lifespan mantığı startup/lifespan.py'de
    lifespan_file = PROJECT_ROOT / "startup" / "lifespan.py"
    if not lifespan_file.exists():
        lifespan_file = PROJECT_ROOT / "main.py"  # Eski yapı fallback
    src = lifespan_file.read_text(encoding="utf-8")
    line = next(
        ln for ln in src.splitlines()
        if "Zombi Görev Kurtarma" in ln or "_recover_zombie_tasks" in ln
    )

    indent = len(line) - len(line.lstrip(" "))
    assert indent <= 8, (
        "Zombie cleanup bloğu lifespan içinde top-level olmalı. "
        f"Bulunan indent={indent}. Büyük ihtimalle except bloğunun içine gömülmüş."
    )


def test_dashboard_index_should_use_static_prefixed_assets():
    """
    Dashboard asset path'leri /static prefix ile gitmeli.
    """
    html = _read("dashboard/index.html")

    # Dashboard v2 dosya isimlerini kontrol et
    assert 'src="/static/core_app_v2.js"' in html or 'src="/static/core_app.js"' in html
    assert 'src="/static/feature_app_v2.js"' in html or 'src="/static/feature_app.js"' in html


def test_monitoring_router_should_not_import_main_directly():
    """
    monitoring_router circular import riski yaratmamalı.
    """
    src = _read("api/monitoring_router.py")

    assert "from main import" not in src
    assert "from core.context import" in src


def test_api_router_files_should_not_import_main_directly():
    """
    Router katmanında doğrudan main import edilmesi yasak.
    """
    api_dir = PROJECT_ROOT / "api"
    offenders = []

    for path in api_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "from main import" in text:
            offenders.append(path.name)

    assert offenders == [], f"Doğrudan main import eden router dosyaları bulundu: {offenders}"


def test_main_should_contain_ping_pong_websocket_contract():
    """
    WebSocket keepalive davranışı kaynak kodda görünür olmalı.
    """
    src = _read("main.py")

    assert '@app.websocket("/ws/logs")' in src
    assert 'if data == "ping":' in src
    assert '"event": "pong"' in src
    assert "ws_manager.disconnect(ws)" in src
