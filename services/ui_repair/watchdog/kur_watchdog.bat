@echo off
setlocal

:: Yönetici izni kontrolü
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Yonetici izinleri dogrulandi. Kurulum basliyor...
) else (
    echo Bu betik Yonetici (Administrator) olarak calistirilmalidir.
    echo Lutfen dosyaya sag tiklayip "Yonetici olarak calistir" secenegini secin.
    pause
    exit /b 1
)

:: PowerShell scriptini Scheduled Task olarak ekle
echo Watchdog Gorev Zamanlayiciya Ekleniyor...
powershell -Command "$action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File E:\ai_company_faz12.1\services\ui_repair\watchdog\watchdog.ps1'; $trigger1 = New-ScheduledTaskTrigger -AtLogOn; $trigger2 = New-ScheduledTaskTrigger -AtStartup; Register-ScheduledTask -TaskName 'SovereignAGI-Watchdog' -Trigger @($trigger1, $trigger2) -Action $action -RunLevel Highest -Force"

echo.
echo Kurulum Tamamlandi! Bilgisayariniz acildiginda veya yeniden baslatildiginda Watchdog otomatik olarak arka planda baslayacaktir.
pause
