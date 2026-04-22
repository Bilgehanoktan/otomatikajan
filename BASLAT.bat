@echo off
chcp 65001 >nul 2>&1
title Sovereign AGI - Gorev Kontrol Merkezi

echo ====================================================
echo    EGEMEN YAZ - Sovereign AGI Baslatiliyor...
echo ====================================================
echo.

:: ---- Degiskenler ----
set "PROJECT_ROOT=%~dp0"
set "PY_CMD=C:\Python314\python.exe"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3100"

:: ---- 1. Altyapi Temizligi ----
echo [1/3] Altyapi cerrahi kontrolu yapiliyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    "%PY_CMD%" "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, atlaniyor...
)

:: Kisa bekleme - portlarin serbest kalmasi icin
timeout /t 2 /nobreak >nul

:: ---- 2. Backend Baslatma ----
echo [2/3] Mission Control API (%BACKEND_PORT%) baslatiliyor...
set "BACKEND_CMD=cd /d %PROJECT_ROOT% && %PY_CMD% -m uvicorn services.workflow_api.main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload"
start "Backend-%BACKEND_PORT%" cmd /k "%BACKEND_CMD%"

:: Backend'in ayaga kalkmasi icin bekleme
echo      Backend baslatildi, ayaga kalkma bekleniyor...
timeout /t 4 /nobreak >nul

:: ---- 3. Frontend Baslatma ----
echo [3/3] Sovereign Cockpit UI (%FRONTEND_PORT%) baslatiliyor...
set "FRONTEND_CMD=cd /d %PROJECT_ROOT%apps\refine_control_plane && npm run dev -- -p %FRONTEND_PORT%"
start "Frontend-%FRONTEND_PORT%" cmd /k "%FRONTEND_CMD%"

echo.
echo ====================================================
echo    KONTROL PANELLERI ACILDI.
echo.
echo    Backend  : http://localhost:%BACKEND_PORT%
echo    Frontend : http://localhost:%FRONTEND_PORT%
echo.
echo    Hata durumunda acilan pencerelerdeki mesajlari
echo    kontrol edin.
echo    Durdurmak icin DURDUR.bat kullanin.
echo ====================================================
timeout /t 5
