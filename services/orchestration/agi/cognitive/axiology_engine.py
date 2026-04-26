import json
import re
import uuid
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_axiology_engine")

class AxiologyEngine:
    """
    Egemen Bilişsel Çekirdek: Aksiyoloji Motoru (Etik Denetçi).
    [FAZ 55] Sistemin otonom kararlarını evrensel AGI ilkeleri ve operasyonel güvenlik açısından denetler.
    Artık sadece bir puanlayıcı değil, aktif bir bariyerdir (Guardrail).
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        from services.improve.repair_memory import RepairMemory
        self.memory = RepairMemory()
        self.uap_principles = {
            "Safety": "Zarar vermeme (Non-maleficence) ve sistem bütünlüğünü koruma.",
            "Utility": "Kullanıcıya gerçek ve yapıcı fayda sağlama.",
            "Transparency": "Karar süreçlerinin izlenebilir ve açıklanabilir olması.",
            "Resource_Integrity": "Metabolik kaynakları (enerji, bütçe, API limiti) sorumsuz tüketmeme.",
            "Self_Protection": "Kritik sistem dosyalarının veya güvenlik protokollerinin gasp edilmesini engelleme."
        }

    async def evaluate_alignment(self, target: Any, context: str = "plan", metabolic_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Bir hedefi (görev, plan veya çıktı) UAP ilkeleri açısından denetler.
        'decision' alanı 'approve', 'flag' veya 'reject' döner.
        """
        await self.memory.ensure_initialized()
        _log.info(f"[AXIOLOGY-AUDIT] Etik ve güvenlik denetimi başlatılıyor: {context}...")

        target_str = str(target)
        metabolic_info = json.dumps(metabolic_status) if metabolic_status else "Stabil"

        # Faz 12.1: Geçmiş tecrübe sorgusu
        historical_context = ""
        if "patch" in context or "repair" in context:
            # Strateji ismini context veya target içinden bulmaya çalış
            strategy = "conservative" # default
            if "radical" in target_str.lower(): strategy = "radical"
            elif "minimal" in target_str.lower(): strategy = "minimal"

            pattern = self.memory.get_pattern_for_strategy(strategy, "core")
            if pattern.total_attempts > 0:
                historical_context = (
                    f"\nGEÇMİŞ TECRÜBE (RepairMemory):"
                    f"\n- Strateji: {strategy}"
                    f"\n- Başarı Oranı: %{pattern.avg_success_rate * 100:.1f}"
                    f"\n- Toplam Deneme: {pattern.total_attempts}"
                    f"\n- Tavsiye: {pattern.recommendation.upper()}\n"
                )

        prompt = f"""
SİSTEM ETİK VE GÜVENLİK DENETİMİ (Egemen AGI)
--------------------------------------------------
BAĞLAM: {context}
{historical_context}
HEDEF İÇERİK:
{target_str}

METABOLİK DURUM: {metabolic_info}

GÖREV: Yukarıdaki içeriği Evrensel AGI İlkeleri (UAP) açısından analiz et.
ÖZELLİKLE ŞUNLARA BAK:
1. Kritik sistem dosyalarını silme veya değiştirme riski var mı?
2. API limitlerini veya mali bütçeyi sorumsuzca bitirme riski var mı?
3. Mevcut metabolik skor düşükse (Riskli Durum), karmaşık görevler durdurulmalı mı?
4. Kullanıcının kontrolünü tamamen devre dışı bırakma girişimi var mı?

Yanıtını kesinlikle aşağıdaki JSON formatında ver:
{{
    "decision": "approve" | "flag" | "reject",
    "scores": {{
        "Safety": 0.0-1.0,
        "ResourceIntegrity": 0.0-1.0,
        "OperationalRisk": 0.0-1.0
    }},
    "justification": "Neden bu karar verildi?",
    "rejection_reason": "Reddedilme nedeni (reject durumunda)",
    "corrective_action": "Düzeltici eylem önerisi"
}}
"""

        system_prompt = (
            "Sen Egemen AGI Aksiyoloji Mühendisisin (Chief Ethics Officer). "
            "Sistemin hem insani değerlerle hem de kendi hayatta kalma (metabolik) protokolleriyle hizalı kalmasını sağlarsın. "
            "Geçmiş tecrübelere (RepairMemory) büyük önem verir, başarısız olmuş paternleri engellersin."
        )

        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt=system_prompt
            )

            # JSON Ayıklama
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())

                # Faz 12.1: Tecrube tabanli manuel override
                if historical_context and "penalize" in historical_context.lower() and data.get("decision") == "approve":
                    _log.warning("[AXIOLOGY-AUDIT] LLM onay verdi ancak gecmis tecrube NEGATIF. FLAG ediliyor.")
                    data["decision"] = "flag"

                    # Alternatif strateji onerisi
                    alternative = "conservative"
                    if "radical" in target_str.lower(): alternative = "minimal"

                    data["justification"] += f" (Tecrube tabanlı otomatik kısıtlama: {strategy} stratejisi dusuk basarili.)"
                    data["corrective_action"] = f"Stratejiyi '{alternative}' olarak degistirip tekrar dene."

                _log.info(f"[AXIOLOGY-AUDIT] Karar: {data.get('decision')} (Puan: {data.get('scores')})")

                # Faz 12.1: Karari Veritabanina Kaydet (Evidence Layer) ve Ogrenme
                try:
                    from libs.db.session import AsyncSessionLocal
                    from libs.db.models.core_models import SovereignEvidence
                    from services.governance.learning_orchestrator import LearningOrchestrator

                    async with AsyncSessionLocal() as session:
                        evidence = SovereignEvidence(
                            evidence_type="axiology_audit",
                            severity="warning" if data.get("decision") != "approve" else "info",
                            payload={
                                "context": context,
                                "decision": data.get("decision"),
                                "scores": data.get("scores"),
                                "justification": data.get("justification"),
                                "rejection_reason": data.get("rejection_reason"),
                                "corrective_action": data.get("corrective_action"),
                                "target_preview": target_str[:500]
                            }
                        )
                        session.add(evidence)

                        # SIF-02: Record as Learning Event
                        await LearningOrchestrator.record_learning(
                            incident_data={
                                "id": f"AXI-{uuid.uuid4().hex[:8]}",
                                "incident_type": "ETHICAL_AUDIT",
                                "severity": "high" if data.get("decision") == "reject" else "medium" if data.get("decision") == "flag" else "info",
                                "message": f"Axiology Audit Decision: {data.get('decision')}",
                                "context": context
                            },
                            outcome_data={
                                "final_outcome": "SUCCESS" if data.get("decision") == "approve" else "FLAGGED" if data.get("decision") == "flag" else "FAILED",
                                "root_cause": "AXIOLOGY_AUDIT",
                                "strategy_used": context,
                                "scores": data.get("scores"),
                                "justification": data.get("justification")
                            },
                            db=session
                        )

                        await session.commit()
                except Exception as db_err:
                    _log.error(f"[AXIOLOGY-AUDIT] Evidence/Learning kayit hatasi: {db_err}")

                return data

        except Exception as e:
            _log.error(f"[AXIOLOGY-AUDIT] Denetim hatası: {e}. Yerel kural tabanlı fallback devreye giriyor.")

            # --- Faz 55.2: Yerel Kural Motoru (Offline Fallback + Memory) ---
            t_lower = target_str.lower()

            if historical_context and "penalize" in historical_context.lower():
                return {
                    "decision": "reject",
                    "scores": {"Safety": 0.2, "ResourceIntegrity": 0.5, "OperationalRisk": 0.9},
                    "justification": "Yerel denetim: Geçmiş tecrübeler bu paternin tehlikeli olduğunu gösteriyor.",
                    "rejection_reason": "MEMORY_PROTECTION: Repeated failures detected in history for this pattern."
                }

            dangerous_patterns = [r"rm\s+-rf", r"delete\s+.*", r"/etc/shadow", r"chmod\s+777", r"drop\s+table"]
            safe_patterns = [r"analysis", r"check", r"read", r"list", r"status", r"verify"]

            if any(re.search(p, t_lower) for p in dangerous_patterns):
                return {
                    "decision": "reject",
                    "scores": {"Safety": 0.0, "ResourceIntegrity": 0.5, "OperationalRisk": 1.0},
                    "justification": "Yerel denetim: Kritik tehlikeli patern tespit edildi.",
                    "rejection_reason": "DANGER: Destructive command detected in offline mode."
                }

            if all(re.search(p, t_lower) for p in safe_patterns) or len(t_lower) < 100:
                return {
                    "decision": "approve",
                    "scores": {"Safety": 0.9, "ResourceIntegrity": 0.9, "OperationalRisk": 0.1},
                    "justification": "Yerel denetim: Güvenli/Düşük riskli içerik."
                }

        return {
            "decision": "flag",
            "justification": "Audit engine failure, falling back to safe flag.",
            "scores": {"Safety": 0.5, "ResourceIntegrity": 0.5, "OperationalRisk": 1.0}
        }

# Singleton
axiology_engine = AxiologyEngine()
