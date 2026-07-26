@echo off
chcp 65001 >nul
:: Check for administrative privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Yönetici yetkileri doğrulandı. İşlem başlatılıyor...
) else (
    echo.
    echo ====================================================================
    echo HATA: Bu dosyayı SAĞ TIKLAYIP "Yönetici Olarak Çalıştır" demelisiniz!
    echo ====================================================================
    echo.
    pause
    exit /b
)

echo.
echo ----------------------------------------------------
echo 1/4: E:\Windows klasörünün sahipliği alınıyor (takeown)...
echo ----------------------------------------------------
takeown /F "E:\Windows" /R /A /D Y

echo.
echo ----------------------------------------------------
echo 2/4: Dil bağımsız SIDs kullanılarak izinler sıfırlanıyor (icacls)...
echo ----------------------------------------------------
:: *S-1-5-32-544 = Yöneticiler (Administrators)
:: *S-1-1-0      = Herkes (Everyone)
:: *S-1-5-18     = SYSTEM
icacls "E:\Windows" /grant *S-1-5-32-544:F /T /C /Q
icacls "E:\Windows" /grant *S-1-1-0:F /T /C /Q
icacls "E:\Windows" /grant *S-1-5-18:F /T /C /Q

echo.
echo ----------------------------------------------------
echo 3/4: Dosya öznitelikleri sıfırlanıyor (attrib)...
echo ----------------------------------------------------
attrib -r -s -h E:\Windows\* /S /D /L

echo.
echo ----------------------------------------------------
echo 4/4: Klasör kalıcı olarak siliniyor (rmdir)...
echo ----------------------------------------------------
rmdir /S /Q "E:\Windows"

echo.
if exist "E:\Windows" (
    echo ========================================================================
    echo UYARI: Bazı dosyalar silinemedi. 
    echo Dosyalar başka bir işlem tarafından kilitlenmiş olabilir.
    echo Bilgisayarı yeniden başlatıp bu dosyayı tekrar "Yönetici Olarak" çalıştırın.
    echo ========================================================================
) else (
    echo ============================================================
    echo BAŞARILI: E:\Windows klasörü fiziksel olarak tamamen silindi!
    echo ============================================================
)
echo.
pause
