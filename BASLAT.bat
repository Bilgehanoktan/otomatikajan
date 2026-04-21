@echo off
title "Sovereign AGI | Görev Kontrol Merkezi"
chcp 65001 >nul
echo ----------------------------------------------------
echo    EGEMEN YAZ - Sovereign AGI Başlatılıyor...
echo ----------------------------------------------------

:: 1. Altyapı Temizliği (Zombie Port ve Süreç Kontrolü)
echo [*] Altyapı cerrahi kontrolü yapılıyor...
python infra\port_surgeon.py


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
