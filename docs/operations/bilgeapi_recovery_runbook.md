# BilgeAPI External Recovery Supervisor Runbook (Phase 31CDE)

Bu doküman, BilgeAPI servislerinin veya worker'larının tamamen ulaşılamaz veya çökmüş olduğu durumlar için kurulan **External Recovery Supervisor** mimarisinin operasyonel prensiplerini ve kurtarma (disaster recovery) adımlarını açıklar.

---

## 1. Mimari Genel Bakış

BilgeAPI kendi process'i down olduğunda kendi kendini ayağa kaldıramaz. Bu nedenle out-of-process çalışan bir supervisor (`scripts/bilgeapi_supervisor.py`) tasarlanmıştır.

```
+-----------------------------------+
|     bilgeapi_supervisor.py        |
+-----------------+-----------------+
                  |
         [Checks GET /health]
                  |
                  v
         Is BilgeAPI healthy?
        /                  \
     [Yes]                 [No]
      /                      \
Flush Local Spool      Enforce Cooldown / Attempts Limit
to Ledger API                \
                              v
                        Run Allowlisted subprocess
                        ["docker", "compose", "restart", ...]
                              \
                               v
                        Spool to supervisor_events.jsonl
```

---

## 2. Supervisor Yapılandırma Parametreleri

Supervisor çalıştırılırken aşağıdaki argümanlar sağlanabilir:
* `--url`: Sağlık kontrolü yapılacak endpoint (Varsayılan: `http://127.0.0.1:8100/health`).
* `--service`: Yeniden başlatılacak servis adı. Yalnızca şu allowlist değerlerini alabilir: `bilgeapi`, `worker`, `app`.
* `--cooldown`: İki kurtarma denemesi arasında geçmesi gereken asgari süre (Varsayılan: `300` saniye).
* `--max-attempts`: Manuel eskalasyondan önceki azami otonom deneme sayısı (Varsayılan: `2`).
* `--spool-file`: API ulaşılamazken logların yazılacağı yerel spool dosyası (Varsayılan: `runtime/recovery/supervisor_events.jsonl`).
* `--api-key`: BilgeAPI tekrar ayağa kalktığında spool flusher'ın ledger raporlaması için kullanacağı yetkili API Key (Varsayılan: `dev-test-key-001`).
* `--mode`: Testlerde docker compose bağımlılığı olmadan doğrulama yapılabilmesi için `prod` veya `test` (Varsayılan: `prod`).
* `--loop`: Komutun 30 saniyede bir çalışan sürekli bir daemon olarak yürütülmesi için kullanılır.

---

## 3. Güvenlik & Kısıtlar (Safety Guardrails)

Dış supervisor sistemin durdurulamaz bir döngüye girmesini önlemek için şu güvenlik kurallarına tabidir:

1. **subprocess.run(shell=True) Kesinlikle Yasaktır**:
   Tüm komutlar bir string parametresi yerine argüman listesi şeklinde (`["docker", "compose", "restart", "bilgeapi"]`) çağrılır. Bu sayede shell-injection veya araya komut sıkıştırma açıkları tamamen önlenmiştir.
2. **Yalnızca Allowlisted Servisler**:
   Geliştirici veya operatör ucu açık parametreler gönderemez. Yalnızca `bilgeapi`, `worker`, `app` servisleri restart edilebilir. Diğer tüm girdiler otomatik olarak engellenir.
3. **Local Spool Caching**:
   BilgeAPI down iken API ulaşılamaz olduğu için, supervisor tüm kurtarma loglarını `runtime/recovery/supervisor_events.jsonl` dosyasına append-only olarak spool eder. BilgeAPI ayağa kalktığında ilk başarılı sağlık kontrolünde bu spool redacted olarak `/v1/watchdog/external-recovery/report` API'sine flush edilir ve review ledger'da immutable olarak kayıt altına alınır.
4. **Cooldown & Attempt Limit**:
   Her deneme yerel bir `.state` dosyasında izlenir. 5 dakika cooldown dolmadan veya 2 deneme aşılmışsa sistem durur ve operatör müdahalesi bekler.

---

## 4. Manuel Çalıştırma ve Yönetim

### Sürekli daemon modunda çalıştırma:
```bash
python scripts/bilgeapi_supervisor.py --loop --service bilgeapi
```

### Acil durum tek seferlik kontrol ve tetikleme:
```bash
python scripts/bilgeapi_supervisor.py --service bilgeapi --cooldown 0
```

### Spool durumunu inceleme:
Spool dosyası JSON Lines formatındadır:
```bash
tail -n 10 runtime/recovery/supervisor_events.jsonl
```
Her satırda kurtarma denemesinin sonucu, stdout ve stderr çıktıları yer alır.
