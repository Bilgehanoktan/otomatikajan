@echo off
setlocal disabledelayedexpansion
chcp 65001 >nul
title AI Yazilim Sirketi - Baslat (v4.0.0-RC1.4)


echo ----------------------------------------------------
echo    AI Yazılım Şirketi (DeerFlow) - Başlatılıyor
echo    Sürüm: 4.0.0-RC1.4
echo ----------------------------------------------------

:: 1. Docker Kontrol
echo [*] Docker kontrol ediliyor...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker calismiyor veya yanit vermiyor. 
    echo Lutfen Docker Desktop'i baslatin.
    pause
    exit /b 1
)

:: 2. Eski Bot Sureclerini Temizle (PowerShell ile Garantili)
echo [*] Eski bot surecleri temizleniyor...
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe' and (commandline like '%%telegram_app.polling%%' or commandline like '%%telegram_watchdog%%')\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

:: 3. Docker Compose Islemleri
cd /d "%~dp0"
echo [1/4] Mevcut konteynerlar durduruluyor...
docker compose down --remove-orphans >nul 2>&1

echo [2/4] Servisler insa ediliyor (Build)...
docker compose build
if %errorlevel% neq 0 (
    echo [!] Build hatasi olustu. Loglari kontrol edin.
    pause
    exit /b 1
)

echo [3/4] Konteynerlar baslatiliyor...
docker compose up -d
if %errorlevel% neq 0 (
    echo [!] Konteynerlar baslatilamadi. 
    pause
    exit /b 1
)

:: 4. Servislerin Hazir Olmasini Bekle
echo [*] Servislerin hazir olmasi bekleniyor (10s)...
timeout /t 10 /nobreak >nul

:: 5. Telegram Watchdog
if exist "scripts\telegram_watchdog.py" (
    echo [4/4] Telegram Watchdog baslatiliyor...
    start "Telegram Watchdog" cmd /k "python scripts\telegram_watchdog.py"
)

echo.
echo ====================================================
echo    Sistem Basariyla Baslatildi!
echo    Dashboard: http://localhost:8000
echo    Repair API: http://localhost:8000/docs
echo ====================================================
echo.
pause