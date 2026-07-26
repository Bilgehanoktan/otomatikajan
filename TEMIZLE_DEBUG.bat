@echo off
chcp 65001 >nul
:: Change directory to the folder where the script is running (critical for Run as Administrator)
cd /d "%~dp0"

set LOG_FILE=%~dp0\temizle_debug_log.txt
echo === TEMIZLE DEBUG BAŞLADI === > "%LOG_FILE%"
echo Zaman: %date% %time% >> "%LOG_FILE%"
echo Çalışma Dizini: %cd% >> "%LOG_FILE%"

:: Check admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Yönetici yetkileri doğrulandı. >> "%LOG_FILE%"
) else (
    echo [HATA] Yönetici yetkileri YOK! >> "%LOG_FILE%"
    echo.
    echo ====================================================================
    echo HATA: Bu dosyayı SAĞ TIKLAYIP "Yönetici Olarak Çalıştır" demelisiniz!
    echo ====================================================================
    echo.
    pause
    exit /b
)

echo ------------------------------------------ >> "%LOG_FILE%"
echo E:\Windows klasörünün sahipliği alınıyor... >> "%LOG_FILE%"
takeown /F "E:\Windows" /R /A /D Y >> "%LOG_FILE%" 2>&1
echo [takeown bitti, Exit Code: %errorlevel%] >> "%LOG_FILE%"

echo ------------------------------------------ >> "%LOG_FILE%"
echo İzinler atanıyor... >> "%LOG_FILE%"
icacls "E:\Windows" /grant *S-1-5-32-544:F /T /C /Q >> "%LOG_FILE%" 2>&1
icacls "E:\Windows" /grant *S-1-1-0:F /T /C /Q >> "%LOG_FILE%" 2>&1
icacls "E:\Windows" /grant *S-1-5-18:F /T /C /Q >> "%LOG_FILE%" 2>&1
echo [icacls bitti, Exit Code: %errorlevel%] >> "%LOG_FILE%"

echo ------------------------------------------ >> "%LOG_FILE%"
echo Öznitelikler kaldırılıyor... >> "%LOG_FILE%"
attrib -r -s -h E:\Windows\* /S /D /L >> "%LOG_FILE%" 2>&1
echo [attrib bitti, Exit Code: %errorlevel%] >> "%LOG_FILE%"

echo ------------------------------------------ >> "%LOG_FILE%"
echo Silme işlemi deneniyor (rmdir)... >> "%LOG_FILE%"
rmdir /S /Q "E:\Windows" >> "%LOG_FILE%" 2>&1
echo [rmdir bitti, Exit Code: %errorlevel%] >> "%LOG_FILE%"

if exist "E:\Windows" (
    echo [UYARI] Klasör hala mevcut. >> "%LOG_FILE%"
) else (
    echo [BAŞARI] Klasör tamamen silindi! >> "%LOG_FILE%"
)

echo === DEBUG BİTTİ === >> "%LOG_FILE%"
echo İşlem tamamlandı. Log dosyası bu klasörde 'temizle_debug_log.txt' olarak oluşturuldu.
pause
