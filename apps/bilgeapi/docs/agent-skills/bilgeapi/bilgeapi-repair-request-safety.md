# BilgeAPI Repair Request Safety Policy

Bu politika, otonom kod onarım (repair request) önerilerinin güvenliğini yöneten kuralları tanımlar.

## Kurallar ve Kısıtlamalar

1. **Manuel Onay Zorunluluğu:** Otonom olarak üretilen hiçbir kod yaması (patch) doğrudan `main` dala otomatik olarak birleştirilemez (`auto_merge=blocked`).
2. **Korumalı Dosya Gates:** `auth.py`, `config.py`, `database.py` gibi güvenlik-kritik dosyalar üzerinde yapılan değişiklikler her durumda insan denetimi (`requires_human_gate=true`) gerektirir.
3. **Sandbox Doğrulama Puanı:** Yamanın sandbox doğrulama puanı (verification score) 85'in altında ise otomatik olarak `REVIEW_REQUIRED` veya `BLOCKED` konumuna düşer.
4. **Yasaklı Eylemler:** Force push, production deployment tetikleme veya veritabanı şema silme işlemleri kesinlikle yasaktır.
