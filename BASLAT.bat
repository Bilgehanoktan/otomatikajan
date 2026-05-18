@echo off
title Sovereign AGI - Debug Launcher
echo [*] Baslatiliyor... Lutfen bekleyin.

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: Python Kontrolu
echo [*] Python kontrol ediliyor...
set "PY_CMD=python"
py -3.13 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.13"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [!] Python bulunamadi! C:\Python314\python.exe deneniyor...
        set "PY_CMD=C:\Python314\python.exe"
    )
)

set "mode=%~1"
if not "%mode%"=="" goto normalize_mode

echo.
echo ==========================================
echo    SOVEREIGN AGI - GUVENLI BASLATICI
echo ==========================================
echo.
echo [1] LOKAL MOD (En hizli ve sorunsuz - TAVSIYE EDILEN)
echo [2] DOCKER MOD (Docker Desktop acik olmalidir)
echo [3] DOCKER/WSL TAMIR ET (Hata aliyorsaniz once bunu calistirin)
echo [4] SELF-REPAIR DEMO / HEALTH CHECK
echo.

set /p mode="Seciminizi yapin (1, 2, 3 veya 4): "

:normalize_mode
if /I "%mode%"=="minimal" set "mode=1"
if /I "%mode%"=="local" set "mode=1"
if /I "%mode%"=="fullstack" set "mode=2"
if /I "%mode%"=="docker" set "mode=2"
if /I "%mode%"=="repair" set "mode=3"
if /I "%mode%"=="self-repair" set "mode=4"
if /I "%mode%"=="health" set "mode=4"

if "%mode%"=="3" (
    call "%PROJECT_ROOT%DOCKER_TAMIR.bat"
    exit /b
)
if "%mode%"=="4" goto self_repair_demo
if "%mode%"=="2" goto docker_mode
if "%mode%"=="1" goto local_mode
echo [!] Gecersiz secim. Lokal mod baslatiliyor.
goto local_mode

:self_repair_demo
echo [*] Self-Repair demo / health check calistiriliyor...
set "MINI_SWE_MODE=mock"
set "REPAIR_AGENT_BACKEND=mini_swe"
set "SANDBOX_BACKEND=local_temp"
%PY_CMD% -m services.taskflow.taskflow_runner --workflow self_repair_v1 --input examples\repair\sample_failed_test.json
if errorlevel 1 (
    echo [HATA] Self-Repair demo basarisiz oldu. repair_outputs\INC-001 ve konsol loglarini kontrol edin.
    pause
    exit /b 1
)
echo [OK] Self-Repair demo tamamlandi.
echo [OK] Beklenen ciktilar:
echo   - repair_outputs\INC-001\repair_case.json
echo   - repair_outputs\INC-001\taskflow\{run_id}\artifact_manifest.json
echo   - repair_outputs\INC-001\taskflow\{run_id}\tournament_result.json
echo   - repair_outputs\INC-001\taskflow\{run_id}\human_gate_decision.json
echo   - repair_outputs\INC-001\taskflow\{run_id}\draft_pr_metadata.json
pause
exit

:local_mode
:: Backend Port Temizligi
echo [*] Eski surecler temizleniyor...
powershell -Command "$pids = netstat -ano | Select-String 'LISTENING' | ForEach-Object { $parts = $_.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); $addr = $parts[1]; if ($addr -like '*:8000' -or $addr -like '*:3100') { $parts[-1] } } | Select-Object -Unique; if ($pids) { Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }"

echo [*] Lokal mod baslatiliyor...
start "Backend API" cmd /k "set SOVEREIGN_DOTENV_OVERRIDE=false&& set RUNTIME_PROFILE=local-dev&& set REDIS_ENABLED=false&& set CELERY_ENABLED=false&& set QUEUE_BACKEND=inprocess&& set INPROCESS_JOB_WORKERS_ENABLED=true&& %PY_CMD% -m uvicorn services.workflow_api.main:app --host 0.0.0.0 --port 8000"
timeout /t 10 >nul
start "Frontend UI" /d "apps\refine_control_plane" cmd /k "npm run dev -- -p 3100"
timeout /t 5 >nul
start "" "http://localhost:3100"
echo [OK] Sistem acildi. Bu pencereyi kapatabilirsiniz.
pause
exit

:docker_mode
setlocal enabledelayedexpansion

:: Port Temizligi (Cakismalari onlemek icin)
echo [*] Eski surecler temizleniyor...
powershell -Command "$pids = netstat -ano | Select-String 'LISTENING' | ForEach-Object { $parts = $_.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); $addr = $parts[1]; if ($addr -like '*:8000' -or $addr -like '*:3100') { $parts[-1] } } | Select-Object -Unique; if ($pids) { Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }"

echo [*] Docker mod baslatiliyor...

:: 1) Oncelikle pipe'i kontrol et
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

:: 2) Pipe yoksa TCP fallback dene
echo [*] Docker pipe bulunamadi, TCP baglantisi deneniyor...
set DOCKER_HOST=tcp://localhost:2375
docker info >nul 2>&1
if not errorlevel 1 (
    echo [OK] Docker TCP uzerinden baglandi!
    goto docker_ready
)
set DOCKER_HOST=

:: 3) Kisa bekleme (maks 20 saniye)
echo [*] Docker Engine bekleniyor...
set /a retries=0
:docker_wait
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

set /a retries+=1
if !retries! GEQ 4 (
    echo.
    echo [HATA] Docker Engine baglantisi kurulamadi!
    echo.
    echo   COZUM: Docker Desktop -^> Settings -^> General -^>
    echo          "Expose daemon on tcp://localhost:2375" secenegini ACIN
    echo          ve Docker Desktop'i yeniden baslatin.
    echo.
    endlocal
    pause
    goto local_mode
)
echo [*] Bekleniyor... ^(!retries!/4^)
timeout /t 5 >nul
goto docker_wait

:docker_ready
echo [OK] Docker Engine hazir!
endlocal
set RUNTIME_PROFILE=full-stack-local
set REDIS_ENABLED=true
set CELERY_ENABLED=true
set DEERFLOW_ENABLED=true
set TELEGRAM_ENABLED=true
set SCHEDULER_ENABLED=true
set QUEUE_BACKEND=celery
set APP_UI_MODE=api-only
set LOCAL_DEV_DB_STRATEGY=primary
set SIF_REGISTER_DEFAULT_ROLE=OPERATOR
set SOVEREIGN_LIGHTWEIGHT_STARTUP=false
set INPROCESS_JOB_WORKERS_ENABLED=false
echo [*] Docker altyapi servisleri baslatiliyor...
docker compose -f docker-compose.yml --profile full-stack up -d --build --wait db redis deerflow-bridge
if errorlevel 1 (
    echo [HATA] Docker altyapi servisleri hazirlanamadi! Loglari kontrol edin.
    pause
    goto local_mode
)
echo [*] Uygulama servisleri baslatiliyor...
docker compose -f docker-compose.yml --profile full-stack up -d --build app cms worker deerflow-worker beat telegram-bot
if errorlevel 1 (
    echo [HATA] docker-compose baslatilamadi! Loglari kontrol edin.
    pause
    goto local_mode
)
start "" "http://localhost:3100"
pause
exit
