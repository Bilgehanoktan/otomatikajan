@echo off
title Sovereign AGI - Docker & WSL Temizleyici
echo [*] Docker ve WSL surecleri sonlandiriliyor...

echo [*] 1. Docker servisleri durduruluyor...
docker compose --profile full-stack down --remove-orphans >nul 2>&1
cd libs\vendor\deer-flow\docker
docker compose down >nul 2>&1
cd ..\..\..\..
cd infra\signoz
docker compose down >nul 2>&1
cd ..\..

echo [*] 2. Tum konteynerlar zorla durduruluyor ve siliniyor...
for /f "tokens=*" %%i in ('docker ps -q') do docker stop %%i >nul 2>&1
for /f "tokens=*" %%i in ('docker ps -aq') do docker rm -f %%i >nul 2>&1

echo [*] 3. Docker Desktop surecleri kapatiliyor...
taskkill /F /IM "Docker Desktop.exe" /T >nul 2>&1
taskkill /F /IM "Docker*" /T >nul 2>&1
taskkill /F /IM "com.docker.*" /T >nul 2>&1
taskkill /F /IM "vpnkit.exe" /T >nul 2>&1
taskkill /F /IM "wslhost.exe" /T >nul 2>&1
timeout /t 2 /nobreak >nul

echo [*] 4. WSL (Windows Subsystem for Linux) kapatiliyor...
wsl --shutdown >nul 2>&1
timeout /t 2 /nobreak >nul

echo [*] 5. Portlar temizleniyor (8000, 3100, 5432, 6379)...
powershell -Command "Get-NetTCPConnection -LocalPort 8000,3100,5432,6379 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo.
echo [OK] Docker, WSL ve tum servisler tamamen temizlendi.
echo [!] Sistem artik temiz, Docker Desktop'i manuel acmadikca calismayacaktir.
echo.
pause
