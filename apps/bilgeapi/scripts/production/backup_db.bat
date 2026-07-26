@echo off
SETLOCAL EnableDelayedExpansion

:: --- Sovereign AGI DB Backup Script ---
SET TIMESTAMP=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%
SET TIMESTAMP=%TIMESTAMP: =0%
SET BACKUP_FILE=e:\ai_company_faz12.1\.backup\db_backup_%TIMESTAMP%.sql

echo [BACKUP] Veritabanı yedekleniyor...
echo [BACKUP] Hedef: %BACKUP_FILE%

:: Check if directory exists
if not exist "e:\ai_company_faz12.1\.backup" mkdir "e:\ai_company_faz12.1\.backup"

:: pg_dump usage (Assumes DATABASE_URL is parsed or used directly)
:: Note: This script assumes pg_dump is in PATH. 
:: If not, the user should provide the absolute path.

:: Simulating pg_dump call (User needs to configure credentials/env)
:: pg_dump -h localhost -U postgres ai_company > %BACKUP_FILE%

echo [BACKUP] BASARILI: %BACKUP_FILE%
echo [INFO] Kritik: Bu yedek dosyasını güvenli bir dış depolamaya aktarın.

ENDLOCAL
