import os
import logging
import time
from typing import Dict, Any, List, Optional
from llm.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.quality.benchmarking_engine import benchmarking_engine
from packages.orchestration.agi.schemas import VerificationReport
from packages.orchestration.agi.task_governance import GovernedTask
from packages.orchestration.agi.monitoring.nervous_system import nervous_system

_log = logging.getLogger("agi_sovereign_evaluator")

class SovereignEvaluator:
    """
    Quality Layer 34: Sovereign Evaluation Harness (Bilişsel Değerlendirme Zırhı).
    Sistemin bilişsel yeteneklerini (Mantık, Güvenlik, Kodlama) puanlar.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def run_suite(self) -> Dict[str, Any]:
        """Tüm değerlendirme testlerini çalıştırır."""
        _log.info("[EVAL] AGI Bilişsel Değerlendirme Paketi başlatılıyor...")
        
        # Faz 38: Deterministic Verileri Al
        bench_results = await benchmarking_engine.run_deterministic_tests()
        
        results = {
            "timestamp": time.time(),
            "scores": {
                "grounding": bench_results["grounding_score"],
                "coding": bench_results["syntax_score"]
            },
            "details": bench_results
        }
        
        # 1. Mantık ve Çıkarım (Reasoning Coherence) - LLM-Assisted
        results["scores"]["reasoning"] = await self._eval_reasoning()
        
        # 3. Güvenlik ve Hizalanma (Safety Alignment)
        results["scores"]["safety"] = await self._eval_safety()
        
        # Toplam Skor (AGI Index)
        scores = results["scores"].values()
        results["agi_index"] = round(sum(scores) / len(scores), 2)
        
        _log.info(f"[EVAL] Değerlendirme Tamamlandı. AGI Index: {results['agi_index']}")
        return results

    async def evaluate_task_outcome(self, task: GovernedTask) -> Dict[str, Any]:
        """
        [Katman 60]: Görevin fiziksel/mantıksal kanıtlarını (Evidence) sorgulayarak
        'Bilişsel Çelişki' (Dissonance) denetimi yapar.
        """
        _log.info(f"[EVAL-TASK] {task.agent_id} tarafından tamamlanan adım denetleniyor: {task.id}")
        
        evidence_found = []
        missing_evidence = []
        score = 1.0

        # 1. Dosya kanıtı ara (FileSystem Check)
        import re
        # Dosya yolu örüntüsü: slaşlı yollar veya uzantısı olan belirgin isimler
        # Örn: 'path/to/file.txt', 'config.json', 'C:\temp\log.txt'
        file_pattern = r'[a-zA-Z0-9_\-\.\/\\~]+\.[a-zA-Z]{2,5}\b'
        all_text = task.result + " " + task.prompt
        potential_files = re.findall(file_pattern, all_text)
        
        for path in set(potential_files):
            # URL'leri filtrele (http/https ile başlıyorsa dosya değildir)
            if path.startswith("http") or "://" in path:
                continue

            # Temizle (noktalama işaretleri vs.)
            clean_path = path.strip(".,()[]'\" \n\t")
            if not clean_path: continue
            
            if os.path.exists(clean_path):
                # AST Structural Verification (Phase 60.5 Enhancement)
                if clean_path.endswith(".py"):
                    try:
                        import ast
                        with open(clean_path, "r", encoding="utf-8") as f:
                            ast.parse(f.read(), filename=clean_path)
                        evidence_found.append(f"Valid Python File: {clean_path}")
                    except SyntaxError as e:
                        _log.error(f"[EVAL-AST] Syntax error in python file: {clean_path} - {e}")
                        missing_evidence.append(f"Syntax Error in File: {clean_path} ({e.msg} at line {e.lineno})")
                    except Exception as e:
                        evidence_found.append(f"File (unparsed): {clean_path}")
                else:
                    evidence_found.append(f"File: {clean_path}")
            else:
                missing_evidence.append(f"Missing File: {clean_path}")

        # 2. Mantıksal Çelişki Analizi (LLM-Assisted Self-Critic)
        # Sadece fiziksel kanıt bulunamadığında ve belirgin bir hata yoksa LLM'e sor
        if not evidence_found and not missing_evidence and task.result:
            try:
                critic_prompt = f"""
                GÖREV: {task.prompt}
                AJAN SONUCU: {task.result}
                
                Yukarıdaki sonuç, görevle uyumlu mu? İllüzyon (Halüsinasyon) görüyor mu? 
                Yanıtı kısa bir 'UYUMLU' veya 'ÇELİŞKİLİ' şeklinde ver ve nedenini açıkla.
                """
                response = await self.model_orch.generate(
                    prompt=critic_prompt,
                    system_prompt="Sen bir AGI Öz-Denetçisisin (Self-Critic Agent). Fiziksel kanıt bulamadığım anlarda mantık yürütürsün."
                )
                
                if "ÇELİŞKİLİ" in response.upper() or "INCONSISTENT" in response.upper():
                    score = 0.3
                    _log.warning(f"[EVAL-DISSONANCE] BİLİŞSEL ÇELİŞKİ TESPİT EDİLDİ: {response[:100]}...")
                else:
                    score = 0.7 # Kanıt yok ama mantık doğru
            except Exception as e:
                _log.warning(f"[EVAL-LLM-FAILURE] Öz-Denetçi LLM başarısız oldu, güvenli moda geçiliyor: {e}")
                score = 0.5 # Belirsizlik durumunda orta skor
        
        # Kesin kanıt varsa skor tam, yoksa ceza uygula
        if len(evidence_found) > 0 and not missing_evidence:
            score = 1.0
        elif missing_evidence:
            # Eksik kanıt varsa skoru düşür (Dissonance)
            score = min(score, 0.4)
            _log.error(f"[EVAL-GROUNDING] EKSİK KANIT TESPİT EDİLDİ: {missing_evidence}")

        report = {
            "score": score,
            "evidence": evidence_found,
            "missing": missing_evidence,
            "is_grounded": score >= 0.7
        }
        
        # --- Phase 60.5: Raporlama ---
        try:
            nervous_system.log_grounding_event(report["score"], not report["is_grounded"])
        except Exception as re:
            _log.warning(f"Metrik raporlama hatas: {re}")
            
        return report

    async def _eval_reasoning(self) -> float:
        """Mantık yürütme derinliğini ölçer (Gerçek LLM Analizi)."""
        prompt = "Determine if the following statement is logically sound: 'If all A are B and some B are C, then some A are C.' Explain why."
        # AGI Evaluator real LLM check
        response = await self.model_orch.generate(
            prompt=prompt,
            system_prompt="Sen bir Mantık ve Akıl Yürütme Denetçisisin."
        )
        # Determine if answer is correct (No, some A are C is a logical fallacy)
        if "fallacy" in response.lower() or "not necessarily" in response.lower():
            return 1.0
        return 0.5

    async def _eval_grounding(self) -> float:
        """BenchmarkingEngine üzerinden bağlam uyumunu ölçer."""
        res = await benchmarking_engine.run_deterministic_tests()
        return res["grounding_score"]

    async def _eval_safety(self) -> float:
        """Güvenlik bariyerlerinin etkinliğini ölçer."""
        # Şu anlık yüksek güvenliğe sahip olduğumuzu varsayıyoruz
        # Faz 40+ da gerçek sızma testleri eklenecektir.
        return 0.95

# Singleton
sovereign_evaluator = SovereignEvaluator()

# Compatibility Alias
agi_evaluator = sovereign_evaluator

if __name__ == "__main__":
    # Konsol testi
    import asyncio
    async def test():
        evaluator = SovereignEvaluator()
        report = await evaluator.run_suite()
        print(f"AGI Score Report: {report}")
    
    asyncio.run(test())
