@echo off
chcp 65001 >nul
title AI Yazilim Sirketi - Durdur

cd /d "%~dp0"

echo [1/2] Proje durduruluyor ve siliniyor...
docker compose down

echo [2/2] Tum ghost containerlar temizleniyor...
for /f "tokens=*" %%i in ('docker ps -aq 2^>nul') do (
    docker stop %%i >nul 2>&1
    docker rm -f %%i >nul 2>&1
)

echo SISTEM DURDURULDU VE TEMIZLENDI.
pause
