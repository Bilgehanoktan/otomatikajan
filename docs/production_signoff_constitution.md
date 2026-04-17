# Production Sign-off & Handover Constitution (Üretim Onay ve Devir Anayasası)
**Version**: 1.0 (Phase 29 Implementation)
**Status**: ACTIVE

## 1. Amaç (Purpose)
Bu doküman, Sovereign AGI platformu üzerindeki kritik bileşenlerin üretim (production) ortamına geçiş kriterlerini, otonom yönetim sınırlarını ve sorumluluk devri protokollerini tanımlar. Amaç, sistemin kendi kendini güncellerken anayasal finansal ve güvenlik sınırlarını aşmamasını sağlamaktır.

## 2. Onay Otoriteleri (Authority Matrix)
| Bileşen Grubu | Onay Tipi | Otorite |
| :--- | :--- | :--- |
| **Çekirdek (Kernel/Auth)** | Manuel | Human Operator (Root) |
| **Tamir Operasyonları (Repair)** | Otonom/Hibrit | Governance Mesh + Confidence Score > 0.95 |
| **Bütçe ve Ekonomi (Economic)** | Manuel | Financial Auditor (HITL) |
| **Kullanıcı Deneyimi (Frontend)** | Otonom | UI/UX Verifier |

## 3. Üretim Hazırlık Kriterleri (Sign-off Criteria)
Bir bileşen "SIGNED" (Onaylı) statüsü alabilmesi için şu testlerden geçmelidir:
1. **Regresyon Testi**: Mevcut fonksiyonlar bozulmamalıdır.
2. **Ekonomik Denetim**: İşlem maliyeti tahsis edilen bütçe sınırları içinde kalmalıdır.
3. **Güvenlik Taraması**: Yeni eklenen kod veya politika, güvenlik açıklarını tetiklememelidir.
4. **Politika Uyumu**: Değişiklik, güncel `.yaml` politikalarıyla çelişmemelidir.

## 4. Sorumluluk Devri (Handover Protocol) - R-12
Sorumluluk devri (`HandoverEvent`), sistemin bir varlık üzerindeki kontrolü bir başkasına (veya otonom bir ajana) resmi olarak devrettiği andır.
- Her devir işlemi `handover_events` tablosuna gerekçesiyle (`justification`) kaydedilir.
- Otonom sistem, risk skoru %20'nin üzerine çıkan varlıklar için sorumluluğu derhal insan operatöre iade etmekle yükümlüdür.

## 5. Kesintisiz Kanıt Motoru (Continuous Proof Engine)
- Sistem, her 15 dakikada bir "Basic Health Probe" çalıştırır.
- Başarısız olan her doğrulama (`ValidationResult`), ilgili bileşenin `ProductionSignoff` durumunu "PENDING" veya "REVOKED" seviyesine çekebilir.
- Kritik başarısızlık durumunda "Emergency Freeze" (Acil Durum Dondurma) protokolü devreye girer.

---
*Bu doküman otonom sistem tarafından okunabilir ve ihlal edilemez bir yapıda tasarlanmıştır.*
