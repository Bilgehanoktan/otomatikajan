@echo off
title "Sovereign AGI | Görev Kontrol Merkezi (DEBUG MODU)"
chcp 65001 >nul
echo ----------------------------------------------------
echo    EGEMEN YAZ - Sovereign AGI Başlatılıyor...
echo ----------------------------------------------------

:: 1. Bağımlılık Kontrolü
echo [*] Bağımlılıklar kontrol ediliyor...
set "PY_CMD=python"
where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] HATA: Python bulunamadı.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] HATA: npm bulunamadı.
    pause
    exit /b 1
)

:: 2. Port Temizliği
echo [*] Portlar temizleniyor...
powershell -NoProfile -Command "foreach ($port in @(8000, 3000, 3100)) { $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; if ($p) { Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue } }"

:: 3. Başlatma
echo [1/2] Mission Control API (8000) başlatılıyor...
:: /k parametresi hata durumunda pencerenin açık kalmasını sağlar
start "Backend (8000)" cmd /k "title Backend (8000) && %PY_CMD% -m uvicorn services.workflow_api.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Sovereign Cockpit UI (3100) başlatılıyor...
start "Frontend (3100)" cmd /k "title Frontend (3100) && cd /d %~dp0apps\refine_control_plane && npm run dev -- -p 3100"

echo.
echo ----------------------------------------------------
echo    KONTROL PANELLERİ AÇILDI.
echo.
echo    Hata durumunda açılan pencerelerdeki mesajları kontrol edin.
echo    Durdurmak için pencereleri kapatabilir veya DURDUR.bat kullanabilirsiniz.
echo ----------------------------------------------------
timeout /t 5
