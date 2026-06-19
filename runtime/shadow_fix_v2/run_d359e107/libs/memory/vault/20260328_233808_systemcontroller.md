---
type: task_memory
created_at: 2026-03-28T23:38:08.381762+00:00
project_id: dd33d5b4
agent_id: system_controller
task_type: subtask_preflight
---

# system_controller

## Description
Proje Görevi: Hatalı Proje
Genel Açıklama: Test

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
{'shared_context': '[architect]: AgentOutput(agent_id=\'architect\', summary=\'Sistem için yeni bir yazılım mimarisi tasarımı yapılacak, bu tasarım microservices yaklaşımını temel alacak. Bu sayede sistem esnekliği ve ölçeklenebilirliği artırılacak.\', decisions=[\'Microservices yaklaşımının kullanılması\', \'Docker konteynırlarının kullanılmaması\', \'Kubernetes оршеştirme aracının kullanılması\'], assumptions=[\'Gerekli altyapı ve kaynakların vorhand edilmesi\', \'Geliştirme ekibinin microservices yaklaşımına aşinalığının olması\'], risks=[Risk(description=\'Sistem複ksitesinin artması\', severity=<RiskSeverity.MEDIUM: \'medium\'>, mitigation=\'Sistem tasarımının dikkatli bir şekilde yapılması ve düzenli olarak gözden geçirilmesi\'), Risk(description=\'Ekip üyelerinin microservices yaklaşımına adapte olamaması\', severity=<RiskSeverity.LOW: \'low\'>, mitigation=\'Eğitim ve destek sağlanması\')], deliverables=[Deliverable(type=\'design\', name=\'Sistem Mimari Tasarımı\', description=\'Microservices yaklaşımına dayalı sistem mimari tasarımı\', content=\'Tasarım dokümanı\'), Deliverable(type=\'doc\', name=\'Sistem Teknik Raporu\', description=\'Sistem teknik ayrıntılarının belgelenmesi\', content=\'Rapor dokümanı\')], next_actions=[\'Implement microservices yaklaşımını kullanarak sistem mimari tasarımı geliştir\', \'Create sistem technical raporunu\', \'Add düzenli olarak sistem tasarımının gözden geçirilmesini\'], quality_notes=[\'Sistem tasarımının dikkatli bir şekilde yapılması ve düzenli olarak gözden geçirilmesi\', \'Ekip üyelerinin microservices yaklaşımına adapte olabilmesi için yeterli eğitim ve destek sağlanması\'], raw_response=\'{\\n  "summary": "Sistem için yeni bir yazılım mimarisi tasarımı yapılacak, bu tasarım microservices yaklaşımını temel alacak. Bu sayede sistem esnekliği ve ölçeklenebilirliği artırılacak.",\\n  "decisions": [\\n    "Microservices yaklaşımının kullanılması",\\n    "Docker konteynırlarının kullanılmaması",\\n    "Kubernetes оршеştirme

## Links
- [[incidents]]
- [[patterns]]
- [[architectural-decisions]]
