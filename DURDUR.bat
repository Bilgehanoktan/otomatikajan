@echo off
title "Sovereign AGI | Sistem Durdurma"
chcp 65001 >nul
echo ----------------------------------------------------
echo    EGEMEN YAZ - Servisler Durduruluyor...
echo ----------------------------------------------------

:: 1. Altyapı Cerrahi Temizlik
echo [*] Aktif servisler ve hayalet portlar temizleniyor...
python infra\port_surgeon.py


echo.
echo ----------------------------------------------------
echo    KONTROL PANELI VE SERVISLER DURDURULDU.
echo ----------------------------------------------------
timeout /t 3
