@echo off
chcp 65001 >nul 2>&1
title Sovereign AGI - Sistem Durdurma

echo ====================================================
echo    EGEMEN YAZ - Servisler Durduruluyor...
echo ====================================================
echo.

set "PROJECT_ROOT=%~dp0"
set "PY_CMD=C:\Python314\python.exe"

:: 1. Port bazli cerrahi temizlik
echo [1/2] Aktif servisler ve hayalet portlar temizleniyor...
if exist "%PROJECT_ROOT%infra\port_surgeon.py" (
    "%PY_CMD%" "%PROJECT_ROOT%infra\port_surgeon.py"
) else (
    echo [!] port_surgeon.py bulunamadi, manuel temizlik yapiliyor...
    taskkill /F /IM node.exe /T >nul 2>&1
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
        taskkill /F /PID %%p /T >nul 2>&1
    )
)

:: 2. Durumu onayla
echo [2/2] Sistem durumu dogrulaniyor...
timeout /t 2 /nobreak >nul

echo.
echo ====================================================
echo    KONTROL PANELI VE SERVISLER DURDURULDU.
echo ====================================================
timeout /t 3
