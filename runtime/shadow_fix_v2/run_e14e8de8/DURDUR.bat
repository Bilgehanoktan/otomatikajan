@echo off
title Sovereign AGI - Stop System
echo [*] Sistem durduruluyor... Lutfen bekleyin.

:: 1) Docker sureclerini durdur
echo [*] Docker konteynerleri durduruluyor...
docker compose -f docker-compose.yml --profile full-stack down --remove-orphans >nul 2>&1

:: 2) Lokal surecleri temizle
echo [*] Lokal servis portlari temizleniyor...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$pids = netstat -ano | Select-String 'LISTENING' | ForEach-Object { $parts = $_.ToString().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries); $addr = $parts[1]; if ($addr -like '*:8000' -or $addr -like '*:3100') { $parts[-1] } } | Select-Object -Unique; if ($pids) { Stop-Process -Id $pids -Force -ErrorAction SilentlyContinue }"

echo.
echo ==========================================
echo    SISTEM DURDURULDU
echo ==========================================
echo.
pause
exit
