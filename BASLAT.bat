@echo off
setlocal disabledelayedexpansion
chcp 65001 >nul
title AI Yazilim Sirketi - Baslat (v4.0.0-RC1.4 - Headless)

echo ----------------------------------------------------
echo    AI Yazilim Sirketi (DeerFlow) - Baslatiliyor
echo    Surum: 4.0.0-RC1.4 (Automated Recovery Mode)
echo ----------------------------------------------------

:: 0. On Kontrol: Sistem Butunlugu (Quality Guard)
echo [*] Sistem butunlugu kontrol ediliyor (Quality Guard)...
python tools\verify\verify_system_integrity.py
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

:: 2. Eski Bot Sureclerini Temizle
echo [*] Eski bot surecleri temizleniyor...
powershell -Command "Get-CimInstance Win32_Process -Filter \"name='python.exe' and (commandline like '%%apps.telegram_bot.polling%%' or commandline like '%%telegram_watchdog%%')\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1

:: 3. Docker Compose Islemleri
cd /d "%~dp0"
echo [1/3] Mevcut konteynerlar durduruluyor...
docker compose down --remove-orphans >nul 2>&1

echo [2/3] Servisler insa ediliyor (Build)...
docker compose build --quiet
if %errorlevel% neq 0 (
    echo [!] Build hatasi olustu.
    exit /b 1
)

echo [3/3] Konteynerlar baslatiliyor...
docker compose up -d
if %errorlevel% neq 0 (
    echo [!] Konteynerlar baslatilamadi. 
    exit /b 1
)

:: 4. Servislerin Hazir Olmasini Bekle
echo [*] Servisler uyaniyor. Log akisi baslatiliyor...
echo ====================================================
echo    Sistem Basariyla Baslatildi! (Headless)
echo    Dashboard: http://localhost:8000
echo    Repair API: http://localhost:8000/docs
echo ====================================================
echo.
