@echo off
title AI_COMPANY_GIT_AUTO_COMMIT
chcp 65001 >nul 2>&1

if "%INTERVAL%"=="" set INTERVAL=300
echo [AI Company] Git Oto-Commit Servisi Baslatildi...
echo Her %INTERVAL% saniyede bir (5 dakika) degisiklik kontrolu yapilacak.
echo Durdurmak icin bu pencereyi kapatin veya Ctrl+C yapin.
echo.

:loop
echo [%date% %time%] Degisiklikler kontrol ediliyor...

:: Degisiklik var mi bak (unstaged veya uncommitted)
git status --short | findstr /R "^" >nul
if %errorlevel% == 0 (
    echo [%date% %time%] Degisiklikler bulundu, kaydediliyor...
    git add .
    git commit -m "Oto-kayit: %date% %time%"
    echo [%date% %time%] Basariyla muhurlendi.
) else (
    echo [%date% %time%] Degisiklik yok, bekleniyor...
)

timeout /t %INTERVAL% /nobreak
goto loop
