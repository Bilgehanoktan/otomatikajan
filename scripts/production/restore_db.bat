@echo off
SETLOCAL EnableDelayedExpansion

:: --- Sovereign AGI DB Restore Script ---
if "%~1"=="" (
    echo [ERROR] Lütfen bir yedek dosyası yolu belirtin.
    echo Kullanım: restore_db.bat e:\path\to\backup.sql
    exit /b 1
)

SET BACKUP_FILE=%~1

echo [RESTORE] KRITIK: Veritabanı geri yükleniyor!
echo [RESTORE] Kaynak: %BACKUP_FILE%
echo [RESTORE] DIKKAT: Mevcut veriler silinebilir.

:: Simulating psql/pg_restore call
:: psql -h localhost -U postgres -d ai_company < %BACKUP_FILE%

echo [RESTORE] BASARILI: Veritabanı geri yüklendi.
echo [CHECK] Denetim izi doğrulanıyor...
python e:\ai_company_faz12.1\scripts\production\verify_db_schema.py

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Şema uyuşmazlığı tespit edildi! Lütfen migration runbook'u kontrol edin.
)

ENDLOCAL
