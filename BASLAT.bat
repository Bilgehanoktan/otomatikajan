@echo off
setlocal disabledelayedexpansion
chcp 65001 >nul
title Sovereign AGI - Baslat (v4.1.0 - Phase 17 Sovereign Pilot)

echo ----------------------------------------------------
echo    Sovereign AGI (DeerFlow) - Baslatiliyor
echo    Bilesen: Fleet Operations Cockpit (Phase 17)
echo ----------------------------------------------------

:: 0. On Kontrol: Sistem Butunlugu (Quality Guard)
echo [*] Sistem butunlugu kontrol ediliyor (Quality Guard)...
python scripts\verify_system_integrity.py
if %errorlevel% neq 0 (
    echo [!] UYARI: Sistem butunluk kontrolu tamamlanamadi.
    echo [!] Nedeni: Veritabani henuz baslatilmamis olabilir. Devam ediliyor...
)

:: 1. Docker Kontrol
echo [*] Docker kontrol ediliyor...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] HATA: Docker calismiyor. Lutfen Docker Desktop'i baslatin.
    exit /b 1
)

:: 2. Eski Surecleri Temizle
echo [*] Artık surecler temizleniyor...
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe' and (commandline like '%%hub_interaction.telegram_bot%%')\" | Stop-Process -Force" >nul 2>&1

:: 3. Docker Compose Islemleri
cd /d "%~dp0"
echo [1/3] Mevcut konteynerlar durduruluyor...
docker compose down --remove-orphans >nul 2>&1

echo [2/3] Bilesenler insa ediliyor (Build)...
docker compose build --quiet
if %errorlevel% neq 0 (
    echo [!] Build hatasi olustu.
    exit /b 1
)

echo [3/3] Sovereign Mesh baslatiliyor...
docker compose up -d
if %errorlevel% neq 0 (
    echo [!] Servisler baslatilamadi. 
    exit /b 1
)

:: 4. Servislerin Hazir Olmasini Bekle
echo [*] Sovereign AGI uyaniyor...
echo ====================================================
echo    Sovereign AGI Kontrol Paneli Hazir!
echo.
echo    Dashboard (Cockpit): http://localhost:8000
echo    Operator Action API: http://localhost:8000/docs
echo    Mesh Status (API):   http://localhost:8000/api/v1/mesh/status
echo    Fleet Hub (API):     http://localhost:8000/api/v1/fleet/projects
echo ====================================================
echo.
