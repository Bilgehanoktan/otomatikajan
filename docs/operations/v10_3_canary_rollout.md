# Rollout Runbook: Baseline v10.3 Candidate Canary Deployment

## 1. Overview
The transition from Baseline v10.2 to v10.3 involves 44 tuning parameters. To mitigate systemic risk, this update will **not** be deployed as a single block. Instead, it will be strictly segmented into three canary phases: Safe, Core, and Governance. 

## 2. Phased Rollout Plan

### [ ] KÜME 1: "Safe" Parametre Grubu
- **Kapsam:** Etkisi düşük, geri alınması anında mümkün olan analitik ve loglama parametreleri (12 Parametre).
- **Hedef:** Sistemin genel stabilizasyonunu bozmadan, yeni log formatlarının ve analitik hook'ların validasyonu.
- **Onay Kriteri:** 10 dakika boyunca Hata Oranı (Error Rate) artışı %0.5'in altında kalmalı.

### [ ] KÜME 2: "Core" Parametre Grubu
- **Kapsam:** Merkezi orkestrasyon time-out süreleri, queue fallback limitleri ve retry katsayıları (18 Parametre).
- **Hedef:** Dağıtık işlem güvencesini sarsmadan, throughput iyileştirmelerini doğrulamak.
- **Onay Kriteri:** `Execution Latency` değerlerinin stabil kalması.

### [ ] KÜME 3: "Governance" Parametre Grubu
- **Kapsam:** Karar ağacı eşik değerleri (threshold), approval timeout süreleri, veri mühürleme (sealing) hash revizyonları (14 Parametre).
- **Hedef:** Karar mekanizmalarında herhangi bir bypass ya da yanlış alarm (false positive) oluşmadığını kanıtlamak.
- **Onay Kriteri:** `decision_lineage` doğrulamalarında (signature verifiers) %100 başarı sağlanması.

## 3. Geri Dönüş (Rollback) Prosedürü
Herhangi bir kümede (batch) anomali tespit edilmesi durumunda:
1. Son başarılı konfigürasyon olan `Baseline-v10.2` anında hafızadan geri yüklenir.
2. Tüm aktif workflow'lar safe-mode'a alınır.
3. Yönetici onaylı bir Audit-Dump alınır.
