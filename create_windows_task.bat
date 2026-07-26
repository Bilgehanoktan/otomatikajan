@echo off
REM Windows Task Scheduler Registration Batch Script for @ai_gucum_ Autonomous Publisher

echo =======================================================================
echo 🕒 WINDOWS GÖREV ZAMANLAYICI KAYIT SİHRBAZI (@ai_gucum_)
echo =======================================================================

schtasks /create /tn "AiGucum_Publisher_1230" /tr "py -3.14 -m workspace.carousel_engine.inspect_and_publish_selected" /sc daily /st 12:30 /f
schtasks /create /tn "AiGucum_Publisher_2030" /tr "py -3.14 -m workspace.carousel_engine.inspect_and_publish_selected" /sc daily /st 20:30 /f

echo =======================================================================
echo ✅ Windows Görev Zamanlayıcı Görevleri (12:30 ve 20:30 TSI) Başarıyla Oluşturuldu!
echo =======================================================================
