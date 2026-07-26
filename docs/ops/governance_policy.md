# Autonomous Governance Policy

Bu doküman OtomatikAjan sisteminin otonom karar alma sınırlarını tanımlar.

## Temel İlke

Sistem staging'e kadar otomatik ilerleyebilir. Production ortamında kullanıcı verisi, secret, deployment, rollback, migration veya yetki etkisi olan hiçbir aksiyon insan onayı olmadan uygulanamaz.

## Otonomi Seviyeleri

| Seviye | Tanım | İzin |
|---|---|---|
| L1 | Ajan analiz ve öneri üretir | Güvenli |
| L2 | Ajan dosya değişiklik önerisi üretir | Güvenli |
| L3 | Ajan branch ve PR hazırlar | Kontrollü |
| L4 | Ajan staging'e kadar test/deploy akışını tetikler | Kontrollü |
| L4.5 | Production önerir, insan onayı bekler | Hedef seviye |
| L5 | Production'a tamamen otomatik çıkar | Bu projede hedeflenmez |

## Agent Permission Matrix

| Aksiyon | Ajan Yapabilir mi? | İnsan Onayı |
|---|---:|---:|
| Log okuma | Evet | Hayır |
| Health kontrolü | Evet | Hayır |
| Issue açma | Evet | Hayır |
| Issue sınıflandırma | Evet | Hayır |
| Branch oluşturma | Evet | Hayır |
| PR oluşturma | Evet | Risk seviyesine göre |
| Test çalıştırma | Evet | Hayır |
| Staging smoke test | Evet | Hayır |
| Staging deploy | Evet | Orta/yüksek riskte evet |
| Production deploy | Hayır | Evet |
| Production rollback | Hayır | Evet |
| Secret değiştirme | Hayır | Evet |
| DB migration uygulama | Hayır | Evet |
| Kullanıcı verisi silme | Hayır | Evet |
| Yetki yükseltme | Hayır | Evet |
| PR merge | Hayır | Evet |

## Risk Seviyesi Kararları

### Low Risk

Örnekler:

- Doküman güncelleme.
- Test ekleme.
- Lokal script düzeltme.
- README düzenleme.

İzin:

- Ajan PR açabilir.
- CI başarılıysa insan review ile merge edilebilir.

### Medium Risk

Örnekler:

- API endpoint davranışı değişikliği.
- Worker queue davranışı değişikliği.
- UI build davranışı değişikliği.

İzin:

- Ajan PR açabilir.
- İnsan review zorunludur.
- Staging smoke test gerekir.

### High Risk

Örnekler:

- Auth, RBAC, token, approval sistemi.
- Migration dosyası.
- Deployment workflow.
- Self-healing davranışı.

İzin:

- Ajan sadece öneri PR'ı açabilir.
- İnsan onayı zorunludur.
- Rollback planı zorunludur.

### Critical Risk

Örnekler:

- Secret değerleri.
- Production deploy.
- Production rollback.
- Kullanıcı verisi etkisi.
- Kalıcı veri silme.
- Yetki yükseltme.

İzin:

- Otomasyon durur.
- Incident veya approval issue açılır.
- İnsan onayı olmadan hiçbir işlem yapılmaz.

## Kill-Switch

Kill-switch aktif olduğunda sistem aşağıdaki moda geçer:

```text
AUTONOMY_MODE=read_only
```

Bu modda izin verilenler:

- Log okuma.
- Health kontrolü.
- Issue oluşturma.
- Risk analizi.
- PR önerisi hazırlama.

Bu modda yasaklananlar:

- Branch push.
- PR auto-update.
- Staging deploy.
- Production etkili tüm aksiyonlar.
- Migration.
- Secret işlemleri.

## Safe Mode

Safe mode, sistemde belirsizlik veya yüksek hata oranı olduğunda kullanılır.

Tetikleyiciler:

- CI üst üste 3 kez başarısız.
- Health check kritik hata üretir.
- Ajan çıktısı schema dışına çıkar.
- ReviewerAgent risk seviyesini belirleyemez.
- Secret sızıntısı şüphesi oluşur.

Safe mode davranışı:

- Yeni otomatik aksiyon durdurulur.
- Mevcut PR'lar insan review bekler.
- Incident issue açılır.
- Sistem sadece analiz ve raporlama yapar.

## Audit Zorunluluğu

Aşağıdaki olaylar audit log'a yazılmalıdır:

- Ajan görevi aldı.
- Ajan çıktı üretti.
- Risk seviyesi belirlendi.
- İnsan onayı istendi.
- Branch oluşturuldu.
- PR oluşturuldu.
- Test sonucu alındı.
- Deployment önerildi.
- Self-healing aksiyonu önerildi veya uygulandı.

## Production Onay Kapısı

Production için minimum onay şartları:

- CI başarılı.
- Staging smoke test başarılı.
- Rollback planı mevcut.
- Evidence kaydı mevcut veya workflow çıktısı linklenmiş.
- En az bir insan review.
- Risk seviyesi high/critical ise manuel release onayı.
