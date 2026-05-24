@echo off
title Sovereign AGI - Debug Launcher
echo [*] Baslatiliyor... Lutfen bekleyin.

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

set "INTERACTIVE=1"
if not "%~1"=="" set "INTERACTIVE=0"

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
echo [*] Calistirilabiliyor: check_system_health.py ...
%PY_CMD% check_system_health.py
echo.
echo [*] Self-Repair demo calistiriliyor...
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
if "%INTERACTIVE%"=="1" pause
exit /b 0

:local_mode
:: Backend Port Temizligi
echo [*] Eski surecler temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3100 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
call :assert_port_free 8000 "Backend API"
if errorlevel 1 (
    echo [HATA] 8000 portu hala kullanimda. Docker Desktop veya eski backend surecini kapatin.
    echo [IPUCU] Docker kaynakliysa once BASLAT.bat repair calistirin veya Docker Desktop'i kapatin.
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
call :assert_port_free 3100 "Frontend UI"
if errorlevel 1 (
    echo [HATA] 3100 portu hala kullanimda. Eski frontend surecini kapatin.
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)

echo [*] Lokal mod baslatiliyor...
start "Backend API" cmd /c "set SOVEREIGN_DOTENV_OVERRIDE=false&& set RUNTIME_PROFILE=local-dev&& set REDIS_ENABLED=false&& set CELERY_ENABLED=false&& set QUEUE_BACKEND=inprocess&& set INPROCESS_JOB_WORKERS_ENABLED=true&& set PLAYWRIGHT_BROWSERS_PATH=C:\Users\BLGEHA~1\.gemini\antigravity\.playwright-browsers&& %PY_CMD% -m uvicorn services.workflow_api.main:app --host 0.0.0.0 --port 8000"
call :wait_http "Backend API" "http://127.0.0.1:8000/health" 24
if errorlevel 1 (
    echo [HATA] Backend API hazir olmadi. Backend API penceresindeki loglari kontrol edin.
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
start "Frontend UI" /d "%PROJECT_ROOT%apps\refine_control_plane" cmd /k "npm.cmd run dev -- -p 3100"
call :wait_http "Frontend UI" "http://127.0.0.1:3100" 24
if errorlevel 1 (
    echo [HATA] Frontend UI hazir olmadi. Frontend UI penceresindeki loglari kontrol edin.
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)
if "%INTERACTIVE%"=="1" start "" "http://localhost:3100"
echo [OK] Sistem acildi. Bu pencereyi kapatabilirsiniz.
if "%INTERACTIVE%"=="1" pause
exit /b 0

:docker_mode
setlocal enabledelayedexpansion

:: Port Temizligi (Cakismalari onlemek icin)
echo [*] Eski surecler temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3100 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

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
call :wait_http "Backend API" "http://127.0.0.1:8000/health" 24
if errorlevel 1 (
    echo [HATA] Docker Backend API hazir olmadi! Loglari kontrol edin.
    pause
    goto local_mode
)
call :wait_http "Frontend UI" "http://127.0.0.1:3100" 24
if errorlevel 1 (
    echo [HATA] Docker Frontend UI hazir olmadi! Loglari kontrol edin.
    pause
    goto local_mode
)
if "%INTERACTIVE%"=="1" start "" "http://localhost:3100"
if "%INTERACTIVE%"=="1" pause
exit /b 0

:wait_http
set "WAIT_NAME=%~1"
set "WAIT_URL=%~2"
set /a WAIT_MAX=%~3
set /a WAIT_COUNT=0
echo [*] %WAIT_NAME% hazirlik kontrolu: %WAIT_URL%
:wait_http_loop
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%WAIT_URL%' -TimeoutSec 3; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } } catch { exit 1 }; exit 1" >nul 2>&1
if not errorlevel 1 (
    echo [OK] %WAIT_NAME% hazir.
    exit /b 0
)
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GEQ %WAIT_MAX% (
    echo [HATA] %WAIT_NAME% zaman asimina ugradi.
    exit /b 1
)
timeout /t 2 >nul
goto wait_http_loop

:assert_port_free
set "PORT_TO_CHECK=%~1"
set "PORT_LABEL=%~2"
netstat -aon | findstr /R /C:":%PORT_TO_CHECK% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [HATA] %PORT_LABEL% portu bos degil: %PORT_TO_CHECK%
    netstat -aon | findstr /R /C:":%PORT_TO_CHECK% .*LISTENING"
    exit /b 1
)
exit /b 0
