@echo off
chcp 65001 >nul 2>&1
title Sovereign AGI - Gorev Kontrol Merkezi

echo.
echo ====================================================
echo    EGEMEN YAZ - Sovereign AGI Baslatiliyor...
echo ====================================================
echo.

set "PROJECT_ROOT=%~dp0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3100"
set "DOCKER_MODE=0"
set "START_MODE=%~1"
if "%START_MODE%"=="" set "START_MODE=auto"

set "PY_CMD=py -3.13"
py -3.13 -c "print('ok')" >nul 2>&1
if errorlevel 1 (
    set "PY_CMD=python"
    where python >nul 2>&1
    if errorlevel 1 (
        set "PY_CMD=C:\Python314\python.exe"
    )
)

echo [0/4] Ortam kontrol ediliyor...
where docker >nul 2>&1
if errorlevel 1 (
    echo [!] Docker bulunamadi. Lokal moda geciliyor...
) else (
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo [!] Docker kurulu ama daemon calismiyor. Lokal moda geciliyor...
    ) else (
        set "DOCKER_MODE=1"
    )
)

if /I "%START_MODE%"=="local" goto local_mode
if /I "%START_MODE%"=="minimal" goto docker_minimal
if /I "%START_MODE%"=="fullstack" goto docker_fullstack
if /I "%START_MODE%"=="full" goto docker_fullstack
if /I "%START_MODE%"=="auto" (
    if "%DOCKER_MODE%"=="1" goto docker_minimal
    goto local_mode
)

echo [!] Bilinmeyen mod: %START_MODE%
echo     Gecerli modlar: auto, local, minimal, fullstack
exit /b 1

:docker_prepare
echo.
echo [DOCKER] Konteyner ortami aktif.
echo [1/4] Eski konteynerler durduruluyor...
docker compose -f "%PROJECT_ROOT%docker-compose.yml" --profile full-stack down --remove-orphans >nul 2>&1
if errorlevel 1 (
    echo [!] Onceki compose projesi durdurulurken uyarilar alindi; devam ediliyor...
)
goto :eof

:docker_minimal
call :docker_prepare
set "RUNTIME_PROFILE=local-dev"
set "QUEUE_BACKEND=inprocess"
set "APP_UI_MODE=api-only"
set "LOCAL_DEV_DB_STRATEGY=sqlite-fallback"
set "REDIS_ENABLED=false"
set "CELERY_ENABLED=false"
set "DEERFLOW_ENABLED=false"
set "TELEGRAM_ENABLED=false"
set "SCHEDULER_ENABLED=false"

echo [2/4] Minimal local topology baslatiliyor...
docker compose -f "%PROJECT_ROOT%docker-compose.yml" up -d --build
if errorlevel 1 (
    echo.
    echo [HATA] Minimal Docker compose baslatma basarisiz!
    pause
    exit /b 1
)

echo [3/4] Servisler ayaga kalkiyor (10 saniye bekleniyor)...
timeout /t 10 /nobreak >nul

echo [4/4] Minimal local topology hazir.
echo.
echo ====================================================
echo    MINIMAL LOCAL TOPOLOGY
echo.
echo    Runtime profile : local-dev
echo    Queue backend   : inprocess
echo    Backend API     : http://localhost:%BACKEND_PORT%
echo    API Dokuman     : http://localhost:%BACKEND_PORT%/docs
echo    Frontend UI     : http://localhost:%FRONTEND_PORT%
echo.
echo    Docker logs     : docker compose logs -f app cms
echo    Full stack icin : BASLAT.bat fullstack
echo    Durdurmak icin  : DURDUR.bat
echo ====================================================

timeout /t 2 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
goto end

:docker_fullstack
call :docker_prepare
set "RUNTIME_PROFILE=full-stack-local"
set "QUEUE_BACKEND=celery"
set "APP_UI_MODE=api-only"
set "LOCAL_DEV_DB_STRATEGY=primary"
set "REDIS_ENABLED=true"
set "CELERY_ENABLED=true"
set "DEERFLOW_ENABLED=true"
set "TELEGRAM_ENABLED=false"
set "SCHEDULER_ENABLED=false"

echo [2/4] Full-stack local topology baslatiliyor...
docker compose -f "%PROJECT_ROOT%docker-compose.yml" --profile full-stack up -d --build
if errorlevel 1 (
    echo.
    echo [HATA] Full-stack Docker compose baslatma basarisiz!
    pause
    exit /b 1
)

echo [3/4] Servisler ayaga kalkiyor (15 saniye bekleniyor)...
timeout /t 15 /nobreak >nul

echo [4/4] Full-stack local topology hazir.
echo.
echo ====================================================
echo    FULL-STACK LOCAL TOPOLOGY
echo.
echo    Runtime profile : full-stack-local
echo    Queue backend   : celery
echo    Backend API     : http://localhost:%BACKEND_PORT%
echo    API Dokuman     : http://localhost:%BACKEND_PORT%/docs
echo    Frontend UI     : http://localhost:%FRONTEND_PORT%
echo    Redis Port      : 127.0.0.1:6380
echo    Postgres Port   : 127.0.0.1:5433
echo    DeerFlow        : http://localhost:8010
echo.
echo    Docker logs     : docker compose --profile full-stack logs -f app worker deerflow-worker
echo    Minimal mod icin: BASLAT.bat minimal
echo    Durdurmak icin  : DURDUR.bat
echo ====================================================

timeout /t 2 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
goto end

:local_mode
echo.
echo [LOKAL] Dogrudan Windows ortaminda baslatiliyor.
echo [1/4] Altyapi cerrahi kontrolu yapiliyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    %PY_CMD% "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, atlaniyor...
)

timeout /t 2 /nobreak >nul

echo [2/4] Port %BACKEND_PORT% serbest mi kontrol ediliyor...
set "PORT_RETRY_COUNT=0"
:check_port
netstat -ano | findstr ":%BACKEND_PORT%.*LISTENING" >nul 2>&1
if not errorlevel 1 (
    set /a PORT_RETRY_COUNT+=1
    if %PORT_RETRY_COUNT% GEQ 5 (
        echo      [!] Port %BACKEND_PORT% hala mesgul! Zorla temizleme baslatiliyor...
        for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%BACKEND_PORT%.*LISTENING"') do (
            echo          PID %%a sonlandiriliyor...
            taskkill /f /pid %%a >nul 2>&1
        )
        timeout /t 2 /nobreak >nul
    ) else (
        echo      Port %BACKEND_PORT% hala mesgul - Deneme %PORT_RETRY_COUNT%/5 - Bekleniyor...
        timeout /t 2 /nobreak >nul
        goto check_port
    )
)
echo      Port %BACKEND_PORT% serbest. Backend baslatiliyor...

set "RUNTIME_PROFILE=local-dev"
set "QUEUE_BACKEND=inprocess"
set "APP_UI_MODE=api-only"
set "LOCAL_DEV_DB_STRATEGY=sqlite-fallback"
set "REDIS_ENABLED=false"
set "CELERY_ENABLED=false"
set "DEERFLOW_ENABLED=false"
set "TELEGRAM_ENABLED=false"
set "SCHEDULER_ENABLED=false"

echo [3/4] Mission Control API (%BACKEND_PORT%) baslatiliyor...
start "Backend-%BACKEND_PORT%" /d "%PROJECT_ROOT%" cmd /k "set RUNTIME_PROFILE=%RUNTIME_PROFILE% && set QUEUE_BACKEND=%QUEUE_BACKEND% && set APP_UI_MODE=%APP_UI_MODE% && set LOCAL_DEV_DB_STRATEGY=%LOCAL_DEV_DB_STRATEGY% && set REDIS_ENABLED=%REDIS_ENABLED% && set CELERY_ENABLED=%CELERY_ENABLED% && set DEERFLOW_ENABLED=%DEERFLOW_ENABLED% && set TELEGRAM_ENABLED=%TELEGRAM_ENABLED% && set SCHEDULER_ENABLED=%SCHEDULER_ENABLED% && %PY_CMD% -m uvicorn apps.public_api.main:app --host 0.0.0.0 --port %BACKEND_PORT%"

echo      Backend baslatildi, ayaga kalkma bekleniyor...
timeout /t 4 /nobreak >nul

echo [4/4] Sovereign Cockpit UI (%FRONTEND_PORT%) baslatiliyor...
start "Frontend-%FRONTEND_PORT%" /d "%PROJECT_ROOT%apps\refine_control_plane" cmd /k "npm run dev -- -p %FRONTEND_PORT%"

echo.
echo ====================================================
echo    KONTROL PANELLERI ACILDI  [WINDOWS LOCAL]
echo.
echo    Runtime profile : local-dev
echo    Queue backend   : inprocess
echo    Backend         : http://localhost:%BACKEND_PORT%
echo    API Docs        : http://localhost:%BACKEND_PORT%/docs
echo    Frontend        : http://localhost:%FRONTEND_PORT%
echo.
echo    Hata durumunda acilan pencerelerdeki mesajlari kontrol edin.
echo    Durdurmak icin DURDUR.bat kullanin.
echo ====================================================

timeout /t 2 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

:end
timeout /t 5 >nul
