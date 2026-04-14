# Production Database Migration Runbook

Bu el kitabı, Sovereign AGI platformunun üretim ortamındaki veritabanı geçişlerini (migration) güvenli bir şekilde yönetmek için standart prosedürleri tanımlar.

## Hazırlık (Prep)

1.  **Yedekleme:** Herhangi bir geçiş işleminden önce `backup_db.sh` scriptini çalıştırarak tam bir yedek alın.
2.  **Sessizlik Süresi:** Mümkünse geçişi sistem yükünün en düşük olduğu saatlerde yapın.
3.  **Versiyon Kontrol:** `verify_db_schema.py` ile mevcut durumu kontrol edin.

## Geçiş Adımları (Execution)

1.  **Migration Dosyalarını Kontrol Et:**
    `alembic history` komutuyla beklenen revizyonları doğrulayın.
2.  **Dry Run (İsteğe Bağlı):**
    `alembic upgrade <rev> --sql` ile yapılacak SQL işlemlerini gözden geçirin.
3.  **Upgrade:**
    ```bash
    alembic upgrade head
    ```
4.  **Doğrulama:**
    ```bash
    python scripts/production/verify_db_schema.py
    ```

## Geri Dönüş (Rollback)

Eğer geçiş başarısız olursa veya sistemde tutarsızlık tespit edilirse:

1.  **Alembic Downgrade:**
    ```bash
    alembic downgrade -1
    ```
2.  **Restore (Kritik Hata):**
    Eğer downgrade çalışmazsa, `restore_db.sh` ile hazırlık aşamasındaki yedeğe dönün.

## SRE Güvenlik Notu
Production ortamında asla `--autogenerate` kullanmayın. Migration dosyaları development ortamında oluşturulmalı ve production'da sadece `upgrade head` yapılmalıdır.
