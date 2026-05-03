@echo off
title Sovereign AGI - Debug Launcher
echo [*] Baslatiliyor... Lutfen bekleyin.

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

:: Python Kontrolu
echo [*] Python kontrol ediliyor...
set "PY_CMD=python"
where python >nul 2>&1
if errorlevel 1 (
    echo [!] Python bulunamadi! C:\Python314\python.exe deneniyor...
    set "PY_CMD=C:\Python314\python.exe"
)

:: Backend Port Temizligi
echo [*] Eski surecler temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3100.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo.
echo ==========================================
echo    SOVEREIGN AGI - GUVENLI BASLATICI
echo ==========================================
echo.
echo [1] LOKAL MOD (En hizli ve sorunsuz)
echo [2] DOCKER MOD (Docker Desktop acik olmalidir)
echo.

set /p mode="Seciminizi yapin (1 veya 2): "

if "%mode%"=="2" goto docker_mode

:local_mode
echo [*] Lokal mod baslatiliyor...
start "Backend API" cmd /k "set RUNTIME_PROFILE=local-dev&& %PY_CMD% -m uvicorn apps.public_api.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 >nul
start "Frontend UI" /d "apps\refine_control_plane" cmd /k "npm run dev -- -p 3100"
timeout /t 3 >nul
start "" "http://localhost:3100"
echo [OK] Sistem acildi. Bu pencereyi kapatabilirsiniz.
pause
exit

:docker_mode
echo [*] Docker mod baslatiliyor...
docker compose -f docker-compose.yml --profile full-stack up -d --build
if errorlevel 1 (
    echo [HATA] Docker baslatilamadi! Docker Desktop'in acik oldugundan emin olun.
    pause
    goto local_mode
)
start "" "http://localhost:3100"
pause
exit
