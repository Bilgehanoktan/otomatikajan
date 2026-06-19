@echo off
title Sovereign AGI - Docker ^& WSL Repair Tool
echo ==========================================
echo    DOCKER ^& WSL TAMIR ARACI (REPAIR)
echo ==========================================
echo.
echo [!] Bu arac Docker Desktop ve WSL sureclerini zorla kapatip temizleyecektir.
echo [!] Kaydedilmemis verileriniz varsa Docker konteynerlarinda kaybolabilir.
echo.
pause

echo [*] 1. Docker surecleri sonlandiriliyor...
taskkill /F /IM "Docker Desktop.exe" /T >nul 2>&1
taskkill /F /IM "Docker*" /T >nul 2>&1
taskkill /F /IM "com.docker.*" /T >nul 2>&1
taskkill /F /IM "vpnkit.exe" /T >nul 2>&1

echo [*] 2. WSL (Windows Subsystem for Linux) kapatiliyor...
wsl --shutdown >nul 2>&1

echo [*] 3. Portlar temizleniyor (8000, 3100, 5432, 6379, 5433, 6380)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3100.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5432.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6379.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5433.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":6380.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [*] 4. Docker Servisi yeniden baslatiliyor...
net stop com.docker.service >nul 2>&1
net start com.docker.service >nul 2>&1

echo [*] 5. Gecici dosyalar temizleniyor...
del /q backend_startup.log >nul 2>&1
del /q live_system.log >nul 2>&1

echo.
echo [OK] Tamir islemi tamamlandi. 
echo [!] Simdi Docker Desktop'i manuel olarak acin ve 'Engine' hazir olunca BASLAT.bat'i calistirin.
echo.
pause
