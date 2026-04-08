"""
Telegram Bot Watchdog Script
Amaç: telegram_app.polling betiğini çalıştırır ve herhangi bir çökme 
(crash) veya kapanma durumunda 5 saniye bekleyip otomatik olarak yeniden başlatır. 
Bu sayede bot kesintisiz çalışarak hızlı tepki vermeye devam eder.

Kullanım:
python scripts/telegram_watchdog.py
"""

import subprocess
import time
import sys
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def run_watchdog():
    logging.info("Telegram Watchdog Başlatıldı. Bot süreçleri izleniyor...")
    
    while True:
        try:
            logging.info("Telegram Botu (telegram_app.polling) başlatılıyor...")
            # subprocess.run engeller (blocklar), süreç bitene kadar bekler.
            process = subprocess.Popen(
                [sys.executable, "-m", "telegram_app.polling"],
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            process.wait() # Sürecin bitmesini bekle
            
            exit_code = process.returncode
            if exit_code == 0:
                logging.info("Telegram Botu normal (exit 0) olarak kapandı.")
                # Eğer bilerek kapatıldıysa tekrar başlatmak istemeyebiliriz ama
                # watchdog mantığında genelde zorla tekrar başlatılır.
            else:
                logging.error(f"Telegram Botu hata ile kapandı (Exit Code: {exit_code}).")
                
        except KeyboardInterrupt:
            logging.info("Watchdog manuel olarak durduruldu (Ctrl+C). Çıkış yapılıyor...")
            break
        except Exception as e:
            logging.error(f"Watchdog çalıştırılırken beklenmeyen hata oluştu: {e}")
            
        logging.info("Sistem 5 saniye içinde yeniden başlatılacak...")
        time.sleep(5)

if __name__ == "__main__":
    run_watchdog()
