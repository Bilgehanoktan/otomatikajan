@echo off
title Sovereign AGI - Stop System
echo [*] Sistem durduruluyor... Lutfen bekleyin.

:: 1) Docker sureclerini durdur
echo [*] Docker konteynerleri durduruluyor...
docker compose --profile full-stack down >nul 2>&1

:: 2) Lokal surecleri temizle
echo [*] Lokal Python ve Node surecleri temizleniyor...
powershell -Command "Get-Process -Name python,node,uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"

:: 3) Portlari zorla serbest birak
powershell -Command "$pids = netstat -ano | Select-String 'LISTENING' | ForEach-Object { $parts = $_.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); $addr = $parts[1]; if ($addr -like '*:8000' -or $addr -like '*:3100' -or $addr -like '*:6379') { $parts[-1] } } | Select-Object -Unique; if ($pids) { Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }"

echo.
echo ==========================================
echo    SISTEM DURDURULDU
echo ==========================================
echo.
pause
exit
