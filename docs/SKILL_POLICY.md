# BilgeAPI Skill & Policy Governance

Bu doküman, `agent-skills` referans paketinin BilgeAPI mimarisi içindeki kullanım sınırlarını, izin verilen (allowed) ve yasaklanan (forbidden) eylemleri resmileştirir.

---

## 1. Temel Mimarî Sınırlar

Yapay zeka kodlama ajanlarının yeteneklerini yöneten markdown tabanlı politika dosyaları, BilgeAPI'nin karar mekanizmasını bypass edecek şekilde doğrudan kod çalıştıramaz.

### Yasaklanan Eylemler (Forbidden Actions List)
Aşağıdaki eylemler otonom olarak **kesinlikle yürütülemez** veya doğrudan ajanın kararına bırakılamaz:
*   **Auto Merge / Auto Deploy:** Ajan kod yamaları üretebilir (`PrDraftModel`), ancak bunları otomatik olarak ana koda birleştiremez (`git merge` / Pull Request merge) veya yayına alamaz.
*   **Production Migration Apply:** Üretim ortamı veritabanlarında otomatik veritabanı şeması güncellemesi (`alembic upgrade head`) çalıştırılamaz.
*   **Branch Push / Force Push:** Ajan doğrudan `main` veya korumalı dallara `push` veya `force push` atamaz.
*   **Shell Script Execution:** `agent-skills` paketiyle birlikte gelen hook veya session-start betikleri (`hooks/*.sh`) backend çalışma ortamında doğrudan çalıştırılamaz.
*   **Güvenilir Çıktı Varsayımı:** Herhangi bir model çıktısı (LLM Output) doğrulanmadan güvenli kabul edilemez. Sandbox analizi ve verifikasyon skoru zorunludur.

---

## 2. İzin Verilen Kullanım Şekli (Allowed Use Cases)

*   **Developer Quality Gates:** Ajanın yerel geliştirme ortamında (Antigravity CLI plugin olarak) disiplinli çalışmasını sağlamak için `/spec`, `/planning`, `/build` ve `/test` komutları kullanılabilir.
*   **Read-Only Catalog:** BilgeAPI, dış sistemlere sunmak üzere doğrulanmış yeteneklerin metadatalarını `/v1/catalog/skills` endpoint'i üzerinden yayınlayabilir.
*   **Scoring & Validation Checks:** Yama analizlerinde (`PrReviewGateScorer`), yaml/checklist kuralları doğrulanarak yamaların kalitesi puanlanabilir.
*   **Review Ledger Traceability:** Hangi politika denetiminin uygulandığı ve sonuçları `ReviewLedgerService` üzerinden audit trail olarak izlenebilir.

---

## 3. Lisans ve Haklar

Bu entegrasyonda kullanılan `agent-skills` paketi **MIT Lisansı** ile lisanslanmıştır. Dış paket orijinal kaynak kodları `.agents/external/agent-skills/` dizini altında telif ve lisans metinleri korunarak saklanır.
