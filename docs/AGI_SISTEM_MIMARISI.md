# AGI’ye Yaklaşan Agent Sistem İçin Sistem Mimarisi ve Veri Akışı Tasarımı

## 1. Mimari yaklaşımın özü

Bu sistem klasik bir backend uygulaması gibi düşünülmemeli.
Aynı şekilde yalnızca “çok agent + tools” sistemi olarak da düşünülmemeli.

En doğru yaklaşım şudur:

**Sistem = Bilişsel çekirdek + operasyon çekirdeği + öğrenme çekirdeği + güvenlik/denetim çekirdeği**

Yani sistem dört büyük bölümden oluşmalı:

### 1. Bilişsel çekirdek
Burada sistem:
- algılar
- yorumlar
- planlar
- simüle eder
- karar verir

### 2. Operasyon çekirdeği
Burada sistem:
- araç çağırır
- görev yürütür
- dosya/komut/API/test işler
- sonuç üretir

### 3. Öğrenme çekirdeği
Burada sistem:
- episode kaydeder
- hafızayı günceller
- skill çıkarır
- policy update önerir
- başarısızlık desenleri oluşturur

### 4. Güvenlik ve denetim çekirdeği
Burada sistem:
- risk sınıflandırır
- approval ister
- sandbox zorlar
- rollback tanımlar
- doğrulama olmadan kalıcılaşmayı engeller

Bu ayrım çok önemlidir. Çünkü çoğu agent sisteminde bu katmanlar birbirine karışır ve sonuçta:
- kararla yürütme aynı yerde olur,
- öğrenme doğrulanmadan yazılır,
- riskli eylemler ayrıştırılmaz,
- sistem “zeka varmış gibi” davranır ama aslında kaotik hale gelir.

Senin sisteminde bunu en baştan ayırmak gerekir.

---

## 2. Mimari seviyeler

Bunu katmanlı yapıda düşünelim.

### Katman 1 — Interface / Input Layer
Bu katman sistemin dış dünya ile temas noktasıdır.

**Girdi kaynakları:**
- kullanıcı mesajı
- görev talebi
- kod deposu
- log akışı
- test çıktısı
- API çağrısı
- event stream
- monitoring sinyalleri
- zaman bilgisi
- daha önceki episode kayıtları

Bu katmanın görevi yalnızca veri almak değildir. Aynı zamanda:
- normalize etmek,
- kaynak güvenini etiketlemek,
- olay tipini belirlemek,
- öncelik çıkarmak,
- yapılandırılmış giriş nesnesi üretmektir.

**Bu katmanın çıktısı şu olmalıdır: `Unified Input Object`**
Örnek alanlar:
- `source_type`
- `raw_payload`
- `normalized_intent`
- `timestamp`
- `trust_level`
- `urgency`
- `domain`
- `candidate_constraints`
- `related_entities`

Bu nesne, tüm bilişsel akışın başlangıç noktası olur.

### Katman 2 — Perception and Interpretation Layer
Bu katman gelen girdiyi “işlenebilir problem”e dönüştürür.

**Alt bileşenler:**
* **2.1 Intent Interpreter:** Kullanıcı gerçekten ne istiyor? (analiz mi, düzeltme mi, araştırma mı, öneri mi, operasyonel müdahale mi, sadece bilgi mi)
* **2.2 Domain Classifier:** Görev hangi alana ait? (software engineering, debugging, ops/incident, architecture review, research, spreadsheet/process)
* **2.3 Risk Assessor:** Bu işin riski nedir? (düşük, orta, yüksek, kritik)
* **2.4 Evidence Requirement Resolver:** Bu görev için hangi tür kanıt gerekir? (test, diff, log, API sonucu, benchmark, insan onayı)
* **2.5 Context Requirement Estimator:** Ne kadar bağlam lazım? (hızlı cevap için az bağlam, kök neden analizi için geniş bağlam, değişiklik önerisi için repo bağımlılık bilgisi)

**Bu katmanın çıktısı: `Problem Frame`**
Alanlar örneğin: `task_type`, `intent`, `objective`, `constraints`, `risk_level`, `evidence_required`, `context_scope`, `urgency`, `expected_output_type`.
Bu nesne, sistemin plansız tepki vermesini engeller.

### Katman 3 — Cognitive Planning Layer
Bu sistemin gerçek “aklı” burada başlar. Bu katmanın görevi: problemi çözmek için doğru zihinsel yaklaşımı seçmek, alt hedefler üretmek, alternatif stratejiler kurmak, belirsizliği yönetmektir.

**Alt bileşenler:**
* **3.1 Context Builder:** Gerekli bağlamı toplar (kısa dönem bağlam, ilgili episodic memory, ilgili skill’ler, semantik bilgi, graph ilişkileri, geçmiş failure pattern’leri).
* **3.2 Hypothesis Generator:** Özellikle debug veya analiz işlerinde önemlidir (ör: bu bir dependency mismatch olabilir).
* **3.3 Strategy Selector:** Problem için hangi bilişsel strateji uygun? (direct answer, diagnostic investigation, plan-and-execute, compare-and-choose, multi-agent debate, simulate-before-act).
* **3.4 Planner:** Adım adım plan üretir (alt görevler, sırayla yürütme, doğrulama noktaları, karar kapıları, başarısızlıkta replan koşulları).
* **3.5 Simulation Engine:** Özellikle yüksek riskli işlerde planı önce zihinsel/sanal olarak dener (bu patch neyi etkiler, muhtemel yan etkiler vb.).

**Bu katmanın çıktısı: `Execution Plan`**
Örnek alanlar: `plan_id`, `task_goal`, `steps`, `tool_requirements`, `required_context_refs`, `verification_points`, `fallback_paths`, `rollback_conditions`, `confidence_estimate`.

### Katman 4 — Multi-Agent Reasoning Layer
Burada dikkat edilmesi gereken şey şu: *çok agent mimarisi sistemin çekirdeği olmamalı; çekirdeğin kullandığı bir muhakeme yöntemi olmalı.*

Bu katmanda roller dinamik biçimde atanmalı: Planner, Executor, Critic, Verifier, Researcher, Strategist, Safety Reviewer, Memory Curator. Bunlar illa ayrı model olmak zorunda değil ama mantıksal sorumlulukları ayrı olmalı.

Bu katmanın amacı: tek açıya sıkışmayı önlemek, alternatif yorum üretmek, erken hatayı yakalamak, strateji kalitesini artırmak.

**Yanlış kullanım:** Her işi 10 agent’a bölmek (maliyetli ve gürültülü).
**Doğru kullanım:** Yüksek belirsizlik, yüksek risk, birden fazla teknik perspektif gerekli durumlarda.

**Bu katmanın çıktısı:** `refined plan`, `disagreement notes`, `risk flags`, `competing hypotheses`, `decision recommendation`.

### Katman 5 — Operational Execution Layer
Bu katman fiziksel/dijital eylemi yapar. En önemli ilke: **Bu katman karar almaz; uygulama yapar.**

**Alt bileşenler:**
* **5.1 Tool Router:** Hangi araç kullanılacak?
* **5.2 Action Executor:** Araç çağrılarını yapar.
* **5.3 Action Recorder:** Her eylemi kaydeder.
* **5.4 Sandbox Gateway:** Riskli eylemleri doğrudan canlıya göndermez.

**Bu katmanın çıktısı:** `action logs`, `tool outputs`, `execution artifacts`, `command results`, `test evidence`, `generated diffs`.

### Katman 6 — Verification and Critique Layer
Bu katman sistemin güvenilirliği için hayati.

**Alt bileşenler:**
* **6.1 Output Verifier:** Çözüm gerçekten işe yaradı mı?
* **6.2 Evidence Checker:** Gelen kanıt yeterli mi?
* **6.3 Critic:** Çözüm yüzeysel mi? Başka yan etki var mı?
* **6.4 Confidence Calibrator:** Model aşırı özgüvenli olabilir. Güven puanını kalibre eder.
* **6.5 Integration Reality Checker:** “Repo içinde var” ile “gerçekten entegre ve çalışıyor” ayrımını tespit etmek.

**Bu katmanın çıktısı: `Verification Report`**
Örnek alanlar: `success_status`, `evidence_strength`, `unresolved_risks`, `integration_reality`, `confidence_adjusted`, `followup_needed`, `memory_write_eligible`.

### Katman 7 — Memory and Learning Layer
Bu katman sistemin evrim alanıdır.

**Alt bileşenler:**
* **7.1 Episode Store:** Her görevin tam yaşam döngüsü.
* **7.2 Semantic Memory Store:** Tanımlar, sabit bilgiler.
* **7.3 Procedural Memory Store:** Nasıl yapılır reçeteleri.
* **7.4 Failure Memory Store:** Başarısızlık desenleri.
* **7.5 Policy Memory Store:** Durumlara göre yaklaşım tercihleri.
* **7.6 Skill Registry:** Reusable skill kayıtları.
* **7.7 Memory Write Gate:** Kalıcı yazmaya değer mi kontrolü.
* **7.8 Generalization Classifier:** Deneyimin türünü belirler.

**Bu katmanın çıktısı:** `memory updates`, `skill candidates`, `policy proposals`, `discarded noise`, `escalated contradictions`.

### Katman 8 — Policy and Adaptation Layer
Öğrenme burada davranışa dönüşür.
Önemli nokta: **Bu katman “hemen canlı davranışı değiştirmemeli”.**
Önce öneri üretmeli, küçük ölçekte denenmeli, sonra policy update alınmalı.

### Katman 9 — World Model Layer
Bu katman AGI yönüne ilerleyebilmesi için kritik. Çevrenin içsel temsiliyeti tutulur.

**Alt modeller:**
* **9.1 Repository Graph:** dosyalar, modüller, import ilişkileri.
* **9.2 Service Dependency Graph:** API, DB, queue vb.
* **9.3 Task-State Graph:** görev durum geçişleri, blokaj desenleri.
* **9.4 Causal Error Graph:** semptom → kök neden olasılıkları.
* **9.5 Temporal Event Graph:** olay sırası, önce-sonra ilişkileri.
* **9.6 Counterfactual Model:** "bunu yaparsam ne olur", "yapmazsam ne olur".

---

## 3. Ana veri nesneleri

Şimdi bu mimarinin üzerinde dönen temel veri yapılarını tanımlayalım.

**3.1 Unified Input Object**
Dış girdinin normalize edilmiş hali.
`input_id`, `source_type`, `raw_content`, `timestamp`, `trust_level`, `domain_hint`, `urgency`, `metadata`

**3.2 Problem Frame**
Sistemin problemi nasıl anladığı.
`task_type`, `objective`, `constraints`, `risk_level`, `evidence_required`, `expected_output`, `priority`, `ambiguity_score`

**3.3 Context Package**
Planlama için toplanan bağlam.
`working_context`, `relevant_episodes`, `relevant_skills`, `semantic_facts`, `graph_links`, `failure_patterns`, `policy_hints`

**3.4 Hypothesis Set**
Özellikle araştırma, debug, RCA işlerinde önemli.
`hypothesis_id`, `description`, `supporting_evidence`, `contradicting_evidence`, `confidence`, `next_checks`

**3.5 Execution Plan**
`plan_id`, `goal`, `steps`, `dependencies`, `required_tools`, `verification_points`, `fallback_paths`, `rollback_conditions`, `estimated_risk`

**3.6 Action Record**
`action_id`, `plan_step_id`, `tool_used`, `input`, `output`, `duration`, `success`, `errors`, `trace_ref`

**3.7 Verification Report**
`result`, `evidence_summary`, `unresolved_issues`, `confidence`, `integration_reality_score`, `safe_to_finalize`, `safe_to_learn`

**3.8 Episode Record**
`episode_id`, `problem_frame`, `context_used`, `plan`, `actions`, `verification`, `final_output`, `lessons`, `skill_candidates`, `policy_candidates`, `world_model_updates`

**3.9 Skill Artifact**
`skill_id`, `name`, `description`, `trigger_pattern`, `preconditions`, `steps`, `tools`, `evidence_requirements`, `failure_modes`, `confidence_score`, `usage_history`, `retirement_status`

**3.10 Policy Proposal**
`proposal_id`, `current_policy`, `proposed_change`, `reason`, `evidence`, `expected_benefit`, `rollout_scope`, `rollback_rule`

---

## 4. Uçtan uca veri akışı

### Akış 1 — Standart görev akışı
1. Input gelir.
2. Input normalize edilir ve Unified Input Object oluşur.
3. Yorumlama katmanı bunu Problem Frame'e çevirir.
4. Context builder gerekli bağlamı toplar ve Context Package oluşturur.
5. Gerekirse hipotez üretilir.
6. Planner Execution Plan oluşturur.
7. Risk yüksekse simülasyon yapılır.
8. Plan, operasyon katmanına gider ve araç eylemleri başlar.
9. Her eylem Action Record olarak kaydedilir.
10. Verifier sonuçları inceler, Verification Report üretir.
11. Başarılıysa sonuç finalize edilir.
12. Episode derlenir ve Episode Record oluşur.
13. Memory write gate çalışır.
14. Uygunsa: episodic memory güncellenir, skill çıkarılır, policy proposal oluşur, world model update önerilir.

### Akış 2 — Yüksek riskli görev akışı
Risk assessor görevi kritik sınıfa atar. Simülasyon zorunlu olur, Safety reviewer devreye girer, Sandbox gateway aktifleşir.

### Akış 3 — Başarısız görev akışı
Başarısızlıkta sistemin işi bitmemeli: fail reason çıkarılır, failure pattern ile eşleşme aranır, replanning kararı verilir, episode failure biçiminde kaydedilir.

---

## 5. Karar kapıları

Mimari içinde bazı yerler özel kapı olmalı:
* **Gate 1 — Context Gate:** Ne kadar bağlam alınacak?
* **Gate 2 — Strategy Gate:** Hangi çözüm modu seçilecek?
* **Gate 3 — Risk Gate:** Bu görev hangi güvenlik moduna girecek?
* **Gate 4 — Simulation Gate:** Önce sanal deneme zorunlu mu?
* **Gate 5 — Execution Gate:** Canlı eyleme izin var mı?
* **Gate 6 — Verification Gate:** Yeterli kanıt var mı?
* **Gate 7 — Memory Write Gate:** Bu deneyim kalıcılaşabilir mi?
* **Gate 8 — Policy Update Gate:** Davranış gerçekten değiştirilmeli mi?
* **Gate 9 — Skill Promotion Gate:** Bu deneyim reusable skill’e dönüşecek kadar güçlü mü?

---

## 6. Hangi katmanlar kısa vadede zorunlu, hangileri ileri faz?

**Kısa vadede zorunlu:**
Problem Frame, Context Package, Execution Plan, Action Record, Verification Report, Episode Record, Memory Write Gate, Skill Registry, Failure Memory, Risk Gate.

**Orta vadede gerekli:**
Policy Memory, Generalization Classifier, Simulation Engine, Causal Error Graph, Integration Reality Checker.

**İleri faz:**
Temporal Event Graph, Counterfactual Model, Adaptive Policy Engine, Cross-domain transfer scorer, Self-evolving skill recomposition engine.

---

## 7. Mimari anti-pattern’ler

Bu sistemi kurarken özellikle kaçınılması gereken yapılar var:
* **Anti-pattern 1:** Her şeyi tek memory deposuna atmak.
* **Anti-pattern 2:** Doğrulanmamış öğrenimi kalıcılaştırmak.
* **Anti-pattern 3:** Planner ile executor’ı aynı karar merkezi yapmak.
* **Anti-pattern 4:** “Tool kullandıysa zeki sayalım” yaklaşımı.
* **Anti-pattern 5:** Dosya varlığını entegrasyon kanıtı saymak.
* **Anti-pattern 6:** Çok agent = daha iyi zeka sanmak.
* **Anti-pattern 7:** Başarıyı sadece final cevap kalitesiyle ölçmek.
* **Anti-pattern 8:** Skill’leri prompt parçaları gibi düşünmek.
* **Anti-pattern 9:** Riskli eylemleri doğrulama öncesi canlıya taşımak.
* **Anti-pattern 10:** Policy değişimini sessizce ve aniden yapmak.

---

## 8. Bu mimarinin felsefi özeti

**Bu sistemin özü şu olmalı:**
dış girdiyi yapısal probleme çevir -> problemi bağlamla birleştir -> hipotez üret -> plan kur -> önce düşün, sonra uygula -> eylemi kaydet -> kanıtla doğrula -> doğrulanmış dersi hafızaya yaz -> tekrar eden başarıyı skill’e dönüştür -> davranışı kontrollü biçimde güncelle -> çevre modelini zamanla derinleştir.

Yani sistem şuna dönüşmeli: **“Göreve cevap veren agent” değil, “çevresini modelleyen, eylemini doğrulayan, deneyimden politikasını güncelleyen bilişsel sistem”**

---

## 9. En net mimari sonucu

Bugünkü çok ajanlı yazılım sistemi, bu mimariye geçerse şu yönde evrilir:
1. LLM orchestration platform
2. Reliable autonomous engineering system
3. Learning agent platform
4. World-model guided adaptive system
5. Cross-domain cognitive agent core

**İşte AGI yönü tam burada başlar.** Yani AGI bir anda “çıkan ürün” değil; bu mimarinin olgunlaşmasının ileri aşamasıdır.
