Set WshShell = CreateObject("WScript.Shell")
' GIT_OTO_COMMIT.bat dosyasını gizli (penceresiz) modda çalıştırır
' INTERVAL çevre değişkeni set edilmemişse batch içinde hata verebilir, 
' bu yüzden direkt wscript içinden de kontrol edilebilir ama batch'i düzeltmek daha sağlıklı.
WshShell.Run "cmd.exe /c set INTERVAL=300 && GIT_OTO_COMMIT.bat", 0
Set WshShell = Nothing
