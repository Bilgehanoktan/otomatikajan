@echo off
echo [*] Mevcut surecler temizleniyor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3100.*LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo [*] Loglar temizleniyor...
echo. > live_backend.log
echo. > live_worker.log
echo. > live_frontend.log

echo [*] Backend baslatiliyor...
set RUNTIME_PROFILE=local-dev
start "AGI-Backend" /b python -m uvicorn apps.public_api.main:app --host 0.0.0.0 --port 8000 > live_backend.log 2>&1

ping -n 6 127.0.0.1 >nul

echo [*] Worker baslatiliyor...
start "AGI-Worker" /b python -m celery -A workers.workflow_worker.tasks.celery_app worker --loglevel=info --queues=critical,default,background --concurrency=2 > live_worker.log 2>&1

ping -n 3 127.0.0.1 >nul

echo [*] Frontend baslatiliyor...
cd apps\refine_control_plane
start "AGI-Frontend" /b npm run dev -- -p 3100 > ..\..\live_frontend.log 2>&1

echo [OK] Sistem baslatildi.
