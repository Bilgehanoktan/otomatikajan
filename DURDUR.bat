@echo off
title Sovereign AGI | Sistem Durdurma
chcp 65001 >nul
echo ----------------------------------------------------
echo    EGEMEN YAZ - Servisler Durduruluyor...
echo ----------------------------------------------------

:: 1. Port bazlı temizlik (PowerShell)
echo [*] Aktif servisler taranıyor ve sonlandırılıyor...

powershell -Command "foreach ($port in @(8000, 3000, 3100)) { $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; if ($connections) { foreach ($conn in $connections) { Write-Host \"[!] Port $port üzerindeki süreç kapatılıyor (PID: $($conn.OwningProcess))\"; Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } } }"

:: 2. Genel Kalıntı Temizliği
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM python.exe /T /FI "COMMANDLINE eq *uvicorn*" >nul 2>&1

echo.
echo ----------------------------------------------------
echo    KONTROL PANELI VE SERVISLER DURDURULDU.
echo ----------------------------------------------------
timeout /t 3
