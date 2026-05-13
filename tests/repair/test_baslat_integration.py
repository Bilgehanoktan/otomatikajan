from pathlib import Path


def test_baslat_exposes_safe_self_repair_demo_option() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    assert "SELF-REPAIR DEMO / HEALTH CHECK" in launcher
    assert "py -3.13 --version" in launcher
    assert 'set "PY_CMD=py -3.13"' in launcher
    assert 'if "%mode%"=="4" goto self_repair_demo' in launcher
    assert ":self_repair_demo" in launcher
    assert 'set "MINI_SWE_MODE=mock"' in launcher
    assert 'set "REPAIR_AGENT_BACKEND=mini_swe"' in launcher
    assert 'set "SANDBOX_BACKEND=local_temp"' in launcher
    assert "services.taskflow.taskflow_runner" in launcher
    assert "self_repair_v1" in launcher
    assert "examples\\repair\\sample_failed_test.json" in launcher
    assert "git push" not in launcher.lower()
    assert "git merge" not in launcher.lower()


def test_baslat_routes_menu_options_to_their_declared_modes() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    assert 'if "%mode%"=="1" goto local_mode' in launcher
    assert 'if "%mode%"=="2" goto docker_mode' in launcher
    assert 'if "%mode%"=="4" goto self_repair_demo' in launcher
    assert launcher.index('if "%mode%"=="1" goto local_mode') < launcher.index(":self_repair_demo")


def test_local_mode_uses_inprocess_queue_without_requiring_redis() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    local_mode = launcher.split(":local_mode", 1)[1].split(":docker_mode", 1)[0]
    assert "QUEUE_BACKEND=inprocess" in local_mode
    assert "CELERY_ENABLED=false" in local_mode
    assert "REDIS_ENABLED=false" in local_mode
    assert "celery -A workers.workflow_worker.tasks.celery_app worker" not in local_mode


def test_docker_compose_respects_launcher_startup_flags() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8", errors="ignore")

    assert "SOVEREIGN_LIGHTWEIGHT_STARTUP: ${SOVEREIGN_LIGHTWEIGHT_STARTUP:-true}" in compose
    assert "INPROCESS_JOB_WORKERS_ENABLED: ${INPROCESS_JOB_WORKERS_ENABLED:-false}" in compose


def test_docker_mode_starts_infrastructure_before_app_layer() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    infra_start = "docker compose -f docker-compose.yml --profile full-stack up -d --build --wait db redis deerflow-bridge"
    app_start = "docker compose -f docker-compose.yml --profile full-stack up -d --build app cms worker deerflow-worker beat telegram-bot"
    assert infra_start in launcher
    assert app_start in launcher
    assert launcher.index(infra_start) < launcher.index(app_start)
