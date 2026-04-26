@echo off
chcp 65001 >nul 2>&1
title Sovereign AGI - Sistem Durdurma

echo.
echo ====================================================
echo    EGEMEN YAZ - Servisler Durduruluyor...
echo ====================================================
echo.

set "PROJECT_ROOT=%~dp0"

:: Python komutunu belirle
set "PY_CMD=python"
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    set "PY_CMD=C:\Python314\python.exe"
)

:: ---- Docker Durdurma ----
where docker >nul 2>&1
if %ERRORLEVEL% equ 0 (
    docker info >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo [DOCKER] Konteynerler durduruluyor...
        docker compose -f "%PROJECT_ROOT%docker-compose.yml" down
    )
)

:: ---- Lokal Temizlik ----
echo [TEMIZLIK] Aktif servisler ve hayalet portlar temizleniyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    "%PY_CMD%" "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, manuel temizlik yapiliyor...
    taskkill /F /IM node.exe /T >nul 2>&1
    taskkill /F /IM uvicorn.exe /T >nul 2>&1
    taskkill /F /IM python.exe /T >nul 2>&1
)

echo.
echo ====================================================
echo    KONTROL PANELI VE SERVISLER DURDURULDU.
echo ====================================================
timeout /t 3
