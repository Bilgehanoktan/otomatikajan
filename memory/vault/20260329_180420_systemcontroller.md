---
type: task_memory
created_at: 2026-03-29T18:04:20.131206+00:00
project_id: a8a4fde9
agent_id: system_controller
task_type: subtask_preflight
---

# system_controller

## Description
Proje Görevi: Sistem Sağlık ve Beceri Entegrasyon Testi
Genel Açıklama: 
    Bu bir otonom test görevidir. 
    Lütfen sistemdeki 'debugging' ve 'optimization' becerilerinin (skills) 
    mevcut iş akışına doğru entegre edilip edilmediğini kontrol et.
    Async/Await yapısında bir hata (traceback) var mı incele.
    

Senin Uzmanlığın: Sistem sağlığı, maliyet analizi ve genel denetim
Kapsam Sınırın (BUNUN DIŞINA ÇIKMA): Teknik geliştirme yapma. Sadece diğer ajanların çıktılarını sistem bütünlüğü ve maliyet açısından denetle.

Senden Beklenen Kesin Çıktı Formatı (Veri Sözleşmesi):
1. Sistem Sağlık Raporu
2. Tahmini Operasyonel Maliyetler
3. Mimari Uyum Onayı

Talimat: Bu projeye SADECE kendi rolün (system_controller) çerçevesinde katkı sağla. Eğer sana önceki ajanlardan bir 'Bağlam (Önceki Çıktılar)' verildiyse, onların mimari kararlarına saygı duy ve kendi çıktılarını onlara mükemmel bir şekilde entegre et.


Yanıtını aşağıdaki JSON şemasında ver. Başka bir şey yazma.

{
  "summary": "1-2 cümle özet",
  "decisions": ["karar1", "karar2"],
  "assumptions": ["varsayım1"],
  "risks": [
    {"description": "risk açıklaması", "severity": "low|medium|high|critical", "mitigation": "önlem"}
  ],
  "deliverables": [
    {"type": "code|config|doc|design|test|other", "name": "isim", "description": "açıklama", "content": ""}
  ],
  "next_actions": ["adım1", "adım2"],
  "quality_notes": ["not1"]
}


## Context Snippet
{'shared_context': '[architect]: (Yanıt alınamadı)\n[backend_dev]: (Yanıt alınamadı)\n[frontend_dev]: (Yanıt alınamadı)\n[qa_engineer]: (Yanıt alınamadı)\n[devops]: (Yanıt alınamadı)\n[security]: (Yanıt alınamadı)\n[data_eng]: (Yanıt alınamadı)\n[tech_writer]: (Yanıt alınamadı)', 'memories': [], 'file_hits': []}

## Links
- [[incidents]]
- [[patterns]]
- [[architectural-decisions]]
