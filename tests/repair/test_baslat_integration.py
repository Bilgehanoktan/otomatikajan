from pathlib import Path


def test_baslat_exposes_safe_self_repair_demo_option() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    assert "SELF-REPAIR DEMO / HEALTH CHECK" in launcher
    assert "py -3.13 --version" in launcher
    assert 'if exist "C:\\Python314\\python.exe"' in launcher
    assert 'set "PY_CMD=C:\\Python314\\python.exe"' in launcher
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


def test_baslat_accepts_documented_noninteractive_mode_aliases() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    assert 'set "mode=%~1"' in launcher
    assert 'if not "%mode%"=="" goto normalize_mode' in launcher
    assert ":normalize_mode" in launcher
    assert 'if /I "%mode%"=="minimal" set "mode=1"' in launcher
    assert 'if /I "%mode%"=="local" set "mode=1"' in launcher
    assert 'if /I "%mode%"=="fullstack" set "mode=2"' in launcher
    assert 'if /I "%mode%"=="docker" set "mode=2"' in launcher
    assert 'if /I "%mode%"=="self-repair" set "mode=4"' in launcher


def test_local_mode_uses_inprocess_queue_without_requiring_redis() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    local_mode = launcher.split(":local_mode", 1)[1].split(":docker_mode", 1)[0]
    assert "call :try_stop_docker_stack" in local_mode
    assert 'powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%cleanup_ports.ps1" -Mode local' in local_mode
    assert "SOVEREIGN_DOTENV_OVERRIDE=false" in local_mode
    assert "QUEUE_BACKEND=inprocess" in local_mode
    assert "INPROCESS_JOB_WORKERS_ENABLED=true" in local_mode
    assert "CELERY_ENABLED=false" in local_mode
    assert "REDIS_ENABLED=false" in local_mode
    assert "BILGEAPI_AUTH_MODE=api_key" in local_mode
    assert "BILGEAPI_STATIC_KEYS=dev-test-key-001:ADMIN" in local_mode
    assert "celery -A workers.workflow_worker.tasks.celery_app worker" not in local_mode


def test_docker_compose_respects_launcher_startup_flags() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8", errors="ignore")

    assert "SOVEREIGN_LIGHTWEIGHT_STARTUP: ${SOVEREIGN_LIGHTWEIGHT_STARTUP:-true}" in compose
    assert "INPROCESS_JOB_WORKERS_ENABLED: ${INPROCESS_JOB_WORKERS_ENABLED:-false}" in compose
    assert "BILGEAPI_ORIGIN: http://bilgeapi:8100" in compose


def test_docker_mode_starts_infrastructure_before_app_layer() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    infra_start = "docker compose -f docker-compose.yml --profile full-stack up -d --build --wait db redis deerflow-bridge"
    app_start = "docker compose -f docker-compose.yml --profile full-stack up -d --build app cms bilgeapi worker deerflow-worker beat telegram-bot"
    assert infra_start in launcher
    assert app_start in launcher
    assert launcher.index(infra_start) < launcher.index(app_start)


def test_docker_mode_forces_stack_reset_and_port_cleanup_before_startup() -> None:
    launcher = Path("BASLAT.bat").read_text(encoding="utf-8", errors="ignore")

    docker_mode = launcher.split(":docker_mode", 1)[1].split(":wait_http", 1)[0]
    assert "docker compose -f docker-compose.yml --profile full-stack down --remove-orphans" in docker_mode
    assert 'powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%cleanup_ports.ps1" -Mode docker' in docker_mode
    assert "Docker mode oncesi gerekli portlar temizlenemedi." in docker_mode
    assert docker_mode.index("docker compose -f docker-compose.yml --profile full-stack down --remove-orphans") < docker_mode.index("docker compose -f docker-compose.yml --profile full-stack up -d --build --wait db redis deerflow-bridge")


def test_cleanup_script_rechecks_ports_and_avoids_killing_docker_relay_processes() -> None:
    cleanup = Path("cleanup_ports.ps1").read_text(encoding="utf-8", errors="ignore")

    assert "[ValidateSet('local', 'docker', 'auto')]" in cleanup
    assert "$protectedProcessNames" in cleanup
    assert "com.docker.backend" in cleanup
    assert "wslrelay" in cleanup
    assert "for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++)" in cleanup
    assert "taskkill /PID" in cleanup
    assert "Port $port is still busy after cleanup attempts." in cleanup


def test_durdur_uses_scoped_shutdown_without_global_process_kill() -> None:
    stopper = Path("DURDUR.bat").read_text(encoding="utf-8", errors="ignore")

    assert "docker compose -f docker-compose.yml --profile full-stack down --remove-orphans" in stopper
    assert "Get-Process -Name python,node,uvicorn" not in stopper
    assert "*:8000" in stopper
    assert "*:3100" in stopper
    assert "*:6379" not in stopper
    assert "Stop-Process -Id" in stopper
