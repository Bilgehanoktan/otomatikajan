@echo off
chcp 65001 >nul 2>&1
title Sovereign AGI - Gorev Kontrol Merkezi

echo.
echo ====================================================
echo    EGEMEN YAZ - Sovereign AGI Baslatiliyor...
echo ====================================================
echo.

:: ---- Degiskenler ----
set "PROJECT_ROOT=%~dp0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3100"

:: Python komutunu belirle
set "PY_CMD=python"
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set "PY_CMD=C:\Python314\python.exe"
)

:: ---- Docker kontrolü ----
where docker >nul 2>&1
if %ERRORLEVEL% equ 0 (
    docker info >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "DOCKER_MODE=1"
    ) else (
        set "DOCKER_MODE=0"
        echo [!] Docker kurulu ama daemon calismıyor. Lokal moda geciliyor...
    )
) else (
    set "DOCKER_MODE=0"
    echo [!] Docker bulunamadi. Lokal moda geciliyor...
)

echo.

:: ====================================================
:: DOCKER MODU
:: ====================================================
if "%DOCKER_MODE%"=="1" (
    echo [DOCKER] Container ortami aktif.
    echo.

    :: Onceki konteynerleri temizle
    echo [1/3] Eski konteynerler durduruluyor...
    docker compose -f "%PROJECT_ROOT%docker-compose.yml" down --remove-orphans >nul 2>&1

    :: Build + Up
    echo [2/3] Konteynerler insa ediliyor ve baslatiliyor...
    docker compose -f "%PROJECT_ROOT%docker-compose.yml" up -d --build
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [HATA] Docker Compose baslatma basarisiz!
        echo        docker-compose.yml veya .env dosyasini kontrol edin.
        pause
        exit /b 1
    )

    :: Saglık kontrolü bekle
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

    :: Frontend'i browser'da ac
    timeout /t 2 /nobreak >nul
    start "" "http://localhost:%FRONTEND_PORT%"
    goto :end
)

:: ====================================================
:: LOKAL MOD (Docker yoksa)
:: ====================================================
echo [LOKAL] Dogrudan Windows ortaminda baslatiliyor.
echo.

:: ---- 1. Altyapi Temizligi ----
echo [1/3] Altyapi cerrahi kontrolu yapiliyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    "%PY_CMD%" "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, atlaniyor...
)

timeout /t 2 /nobreak >nul

:: ---- 2. Backend Baslatma ----
echo [2/3] Mission Control API (%BACKEND_PORT%) baslatiliyor...
set "BACKEND_CMD=cd /d "%PROJECT_ROOT%" && "%PY_CMD%" -m uvicorn apps.public_api.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
start "Backend-%BACKEND_PORT%" cmd /k "%BACKEND_CMD%"

echo      Backend baslatildi, ayaga kalkma bekleniyor...
timeout /t 4 /nobreak >nul

:: ---- 3. Frontend Baslatma ----
echo [3/3] Sovereign Cockpit UI (%FRONTEND_PORT%) baslatiliyor...
set "FRONTEND_CMD=cd /d "%PROJECT_ROOT%apps\refine_control_plane" && npm run dev -- -p %FRONTEND_PORT%"
start "Frontend-%FRONTEND_PORT%" cmd /k "%FRONTEND_CMD%"

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

:end
timeout /t 5
