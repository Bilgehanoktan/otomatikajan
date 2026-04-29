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

set "PY_CMD=py -3.13"
py -3.13 -c "print('ok')" >nul 2>&1
if errorlevel 1 (
    set "PY_CMD=python"
    where python >nul 2>&1
    if errorlevel 1 (
        set "PY_CMD=C:\Python314\python.exe"
    )
)

echo [0/3] Ortam kontrol ediliyor...
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

echo.

if "%DOCKER_MODE%"=="1" goto docker_mode
goto local_mode

:docker_mode
echo [DOCKER] Container ortami aktif.
echo.
echo [1/3] Eski konteynerler durduruluyor...
docker compose -f "%PROJECT_ROOT%docker-compose.yml" down --remove-orphans >nul 2>&1

echo [2/3] Konteynerler insa ediliyor ve baslatiliyor...
docker compose -f "%PROJECT_ROOT%docker-compose.yml" up -d --build
if errorlevel 1 (
    echo.
    echo [HATA] Docker Compose baslatma basarisiz!
    echo        docker-compose.yml veya .env dosyasini kontrol edin.
    pause
    exit /b 1
)

echo [3/3] Servisler ayaga kalkiyor (10 saniye bekleniyor)...
timeout /t 10 /nobreak >nul

echo.
echo ====================================================
echo    KONTEYNERLER CALISIYOR
echo.
echo    Backend API  : http://localhost:%BACKEND_PORT%
echo    API Dokuman  : http://localhost:%BACKEND_PORT%/docs
echo    Frontend UI  : http://localhost:%FRONTEND_PORT%
echo.
echo    Loglar icin  : docker compose logs -f app
echo    Durdurmak    : DURDUR.bat veya docker compose down
echo ====================================================

timeout /t 2 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"
goto end

:local_mode
echo [LOKAL] Dogrudan Windows ortaminda baslatiliyor.
echo.

echo [1/3] Altyapi cerrahi kontrolu yapiliyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    %PY_CMD% "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, atlaniyor...
)

timeout /t 2 /nobreak >nul

echo [2/3] Port %BACKEND_PORT% serbest mi kontrol ediliyor...
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
        echo      Port %BACKEND_PORT% hala mesgul (%PORT_RETRY_COUNT%/5), bekleniyor...
        timeout /t 2 /nobreak >nul
        goto check_port
    )
)
echo      Port %BACKEND_PORT% serbest. Backend baslatiliyor...

echo [2/3] Mission Control API (%BACKEND_PORT%) baslatiliyor...
start "Backend-%BACKEND_PORT%" /d "%PROJECT_ROOT%" cmd /k "%PY_CMD% -m uvicorn apps.public_api.main:app --host 0.0.0.0 --port %BACKEND_PORT%"

echo      Backend baslatildi, ayaga kalkma bekleniyor...
timeout /t 4 /nobreak >nul

echo [3/3] Sovereign Cockpit UI (%FRONTEND_PORT%) baslatiliyor...
start "Frontend-%FRONTEND_PORT%" /d "%PROJECT_ROOT%apps\refine_control_plane" cmd /k "npm run dev -- -p %FRONTEND_PORT%"

echo.
echo ====================================================
echo    KONTROL PANELLERI ACILDI  [LOKAL MOD]
echo.
echo    Backend  : http://localhost:%BACKEND_PORT%
echo    API Docs : http://localhost:%BACKEND_PORT%/docs
echo    Frontend : http://localhost:%FRONTEND_PORT%
echo.
echo    Hata durumunda acilan pencerelerdeki mesajlari
echo    kontrol edin.
echo    Durdurmak icin DURDUR.bat kullanin.
echo ====================================================

timeout /t 2 /nobreak >nul
start "" "http://localhost:%FRONTEND_PORT%"

:end
timeout /t 5 >nul
