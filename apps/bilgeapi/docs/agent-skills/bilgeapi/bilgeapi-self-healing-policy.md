# BilgeAPI Self-Healing Policy

Bu politika, otonom kendi kendini iyileştirme (self-healing) sisteminin hangi koşullarda ve hangi limitlerle çalışabileceğini belirler.

## Kurallar ve Kısıtlamalar

1. **İzin Verilen Eylemler (Allowlisted Remediation):** Sadece risksiz veya stateless eylemler otomatik yürütülebilir (örn: `restart_worker`, `clear_local_cache`).
2. **Yasaklı Eylemler (Forbidden Actions):** Veritabanı manipülasyonu, config değiştirme, auto deployment tetikleme veya force push gibi yıkıcı eylemler policy seviyesinde engellenir.
3. **Cooldown & Max Attempts:** Her runbook'un cooldown (soğuma) süresi ve maksimum deneme limiti (max attempts) veritabanı denetimleriyle korunur. Aşılması durumunda işlem otomatik `BLOCKED` konumuna düşürülür.
