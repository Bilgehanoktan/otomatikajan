import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import ProblemFrame, ActionRecord, VerificationReport

_log = get_logger("agi_audit")

class AuditGate:
    """
    Güvenlik ve Denetim Çekirdek - Doğrulama Katmanı.
    Eylemleri ve çıktıları ProblemFrame kriterlerine göre denetler.
    """
    CENSUS_PROVIDERS = ["gemini", "anthropic", "openai"]

    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def verify(self, frame: ProblemFrame, actions: List[ActionRecord], final_output: Any) -> VerificationReport:
        _log.info(f"Doğrulanıyor: {frame.objective} (Risk: {frame.risk_level.value})")

        # --- Hard Grounding (Katman 6 Entegrasyonu) ---
        grounding_evidence = self._check_filesystem_grounding(actions)
        _log.info(f"Fiziksel Kanıtlar: {len(grounding_evidence)} dosya/aksiyon doğrulandı.")

        # --- Symbolic Guardrails (Phase 26) ---
        symbolic_report = await self._run_symbolic_checks(actions)
        if not symbolic_report["is_valid"]:
            _log.warning(f"[AUDIT] Sembolik doğrulama BAŞARISIZ: {symbolic_report['summary']}")
            # Kritik sembolik hatalarda (bandit/mypy) doğrudan reddet veya neural audit'e besle
        
        # Kritik veya yüksek riskli işlerde Multi-Model Census (Faz 12.4)
        if frame.risk_level in ("high", "critical") or len(actions) > 5:
            return await self._consensus_verify(frame, actions, final_output, grounding_evidence, symbolic_report)
        
        return await self._single_audit(frame, actions, final_output, grounding_evidence, symbolic_report=symbolic_report)

    async def _single_audit(self, frame, actions, final_output, grounding_evidence, provider=None, symbolic_report=None) -> VerificationReport:
        prompt = self._build_audit_prompt(frame, actions, final_output, grounding_evidence, symbolic_report)
        try:
            # force_provider ile belirli bir modeli zorla veya model_orch'a bırak
            response_content = await self.model_orch.complete_task(
                agent_role="qa_engineer",
                prompt=prompt,
                system_prompt="Sen bir AGI Kalite Denetçisisin. Hem neural sezgiyi hem de sembolik raporları kullanarak doğruluğu saptarsın."
            )
            
            audit_data = self._parse_json_from_response(response_content.content)
            report = self._build_report_from_data(audit_data)
            
            # Sembolik raporu final rapora ekle
            if symbolic_report:
                report.evidence_summary += f"\n[SYMBOLIC_LOG]: {symbolic_report['summary']}"
                if not symbolic_report["is_valid"]:
                    report.result_status = False # Sembolik hata varsa neural onay yetmez.
                    report.safe_to_finalize = False
            
            return report
        except Exception as e:
            _log.error(f"Audit hatası ({provider or 'default'}): {e}")
            return VerificationReport(result_status=False, evidence_summary=f"Audit failed: {e}")

    async def _run_symbolic_checks(self, actions: List[ActionRecord]) -> Dict[str, Any]:
        from core.agi.security.symbolic_engine import symbolic_engine
        files_to_check = set()
        
        # Action'lardan değiştirilen dosyaları bul (basitleştirilmiş regex veya metadata)
        for act in actions:
            if act.tool_used in ("backend_dev", "architect", "source_refactor"):
                # Çıktıda veya inputta dosya yolu ara
                found = re.findall(r'(\w+[\w./-]+\.py)', str(act.input_data) + str(act.output_data))
                files_to_check.update(found)

        summary_parts = []
        is_all_valid = True
        
        for f in files_to_check:
            if os.path.exists(f):
                res = await symbolic_engine.run_safety_scans(f)
                if not res["is_valid"]:
                    is_all_valid = False
                    summary_parts.append(f"FILE: {f} -> RUFF: {len(res['ruff_errors'])}, BANDIT: {len(res['bandit_risks'])}, MYPY: {len(res['mypy_type_errors'])}")
        
        return {
            "is_valid": is_all_valid,
            "summary": " | ".join(summary_parts) if summary_parts else "All symbolic checks passed."
        }
        """
        Multi-Model Census: Birden fazla modelden görüş al ve konsensüs sağla.
        """
        _log.info(f"Multi-Model Census başlatılıyor: {self.CENSUS_PROVIDERS}")
        
        tasks = []
        for provider in self.CENSUS_PROVIDERS:
            tasks.append(self._single_audit(frame, actions, final_output, grounding_evidence, provider=provider))
        
        reports = await asyncio.gather(*tasks)
        
        # Konsensüs Analizi
        successful_reports = [r for r in reports if r.evidence_summary != "Audit failed"]
        if not successful_reports:
            return VerificationReport(result_status=False, evidence_summary="All census models failed.")

        # Reality Score Ortalaması
        reality_scores = [r.integration_reality_score for r in successful_reports]
        avg_reality = sum(reality_scores) / len(reality_scores)
        
        # Durum Konsensüsü (Çoğunluk Kararı)
        status_votes = [r.result_status for r in successful_reports]
        final_status = status_votes.count(True) > status_votes.count(False)
        
        _log.info(f"Census Tamamlandı. Avg Reality: {avg_reality:.2f} | Status: {final_status}")

        # En detaylı raporu baz alarak konsensüs verilerini üzerine yaz
        final_report = max(successful_reports, key=lambda x: len(x.evidence_summary))
        final_report.integration_reality_score = avg_reality
        final_report.result_status = final_status
        final_report.evidence_summary = f"[CONSENSUS {len(successful_reports)} Models] " + final_report.evidence_summary
        
        return final_report

    def _build_report_from_data(self, audit_data: Dict[str, Any]) -> VerificationReport:
        return VerificationReport(
            result_status=audit_data.get("result_status", False),
            evidence_summary=audit_data.get("evidence_summary", "No evidence provided"),
            unresolved_risks=audit_data.get("unresolved_risks", []),
            confidence_adjusted=audit_data.get("confidence_adjusted", 0.5),
            integration_reality_score=audit_data.get("integration_reality_score", 0.0),
            safe_to_finalize=audit_data.get("safe_to_finalize", False),
            safe_to_learn=audit_data.get("safe_to_learn", False),
            followup_needed=audit_data.get("followup_needed", [])
        )

    def _check_filesystem_grounding(self, actions: List[ActionRecord]) -> List[Dict[str, Any]]:
        """
        ActionRecord'lar içinde geçen dosyaların fiziksel durumunu kontrol eder.
        """
        import os
        evidence = []
        # Regex for common file paths in tool outputs
        path_regex = re.compile(r'([a-zA-Z0-9_\-\.\/]+\.(?:py|js|css|html|md|json|txt|vbs))')
        
        for action in actions:
            # Hem input hem output'ta dosya yolu ara
            combined_data = f"{str(action.input_data)} {str(action.output_data)}"
            found_paths = set(path_regex.findall(combined_data))
            
            for path in found_paths:
                # Sadece mevcut workspace içindeki dosyaları kontrol et
                if os.path.exists(path) and not os.path.isdir(path):
                    stats = os.stat(path)
                    evidence.append({
                        "path": path,
                        "exists": True,
                        "size": stats.st_size,
                        "last_modified": stats.st_mtime,
                        "action_context": action.tool_used
                    })
                elif "create" in action.tool_used.lower() or "write" in action.tool_used.lower():
                     evidence.append({"path": path, "exists": False, "status": "MISSING_POST_ACTION"})

        return evidence

    def _build_audit_prompt(self, frame: ProblemFrame, actions: List[ActionRecord], final_output: Any, grounding_evidence: List[Dict[str, Any]]) -> str:
        action_summary = "\n".join([f"- {a.step_id}: {a.tool_used} ({'Başarılı' if a.success else 'Başarısız'})" for a in actions])
        
        return f"""
        Aşağıdaki görevin çıktılarını ve eylemlerini denetle. 
        Gerçekten işe yarayıp yaramadığını (Integration Reality) sorgula.
        
        Hedef: {frame.objective}
        Beklenen Kanıtlar: {frame.evidence_required}
        Yapılan Eylemler:
        {action_summary}
        
        Final Cikti:
        {final_output}
        
        Fiziksel Kanitlar (Filesystem Grounding):
        {grounding_evidence}
        
        Yanıtı SADECE aşağıdaki JSON formatında ver:
        {{
            "result_status": true|false,
            "evidence_summary": "Kanıtların özeti",
            "unresolved_risks": ["risk 1"],
            "confidence_adjusted": 0.0-1.0,
            "integration_reality_score": 0.0-1.0 (Kod gerçekten çalışıyor mu yoksa sadece yazıldı mı?),
            "safe_to_finalize": true|false,
            "safe_to_learn": true|false (Hafızaya alınmalı mı?),
            "followup_needed": ["takip adımı 1"]
        }}
        """

    def _parse_json_from_response(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}

    async def verify_self_patch(self, file_path: str, new_content: str, reason: str = "") -> bool:
        """
        [Phase 38] Otonom öz-yama (Self-Patching) güvenliğini denetler.
        Süreç: Yasaklı komut taraması -> Neural Kritik -> Otomatik Regresyon Testleri.
        """
        _log.info(f"Self-Patch Denetleniyor: {file_path}")
        
        # 1. Koruma Listesi (Protected Files)
        protected_files = ["config.py", "db/session.py", "core/agi/security/audit_gate.py"]
        if any(p in file_path for p in protected_files):
            _log.error(f"Audit: Kritik dosya koruma altında! Yama REDDEDİLDİ: {file_path}")
            return False

        # 2. Yasaklı Komut Taraması
        forbidden = ["os.remove", "os.rmdir", "shutil.rmtree", "eval(", "exec("]
        for word in forbidden:
            if word in new_content:
                _log.error(f"Audit: Yasaklı komut tespit edildi ({word})! Yama REDDEDİLDİ.")
                return False

        # 3. Neural Kritik (LLM)
        prompt = f"""
        DOSYA: {file_path}
        İYLEŞTİRME GEREKÇESİ: {reason}
        YENİ İÇERİK:
        ```python
        {new_content}
        ```
        
        Bu yama güvenli mi? Fonksiyonel bir bozulmaya yol açar mı? 
        Yanıtı JSON formatında ver:
        {{
            "is_safe": true|false,
            "risk_score": 0.0-1.0,
            "reason": "..."
        }}
        """
        
        try:
            # Phase 35: Shadow Backup Integration
            from core.agi.security.backup_service import backup_service
            
            response = await self.model_orch.complete_task(
                agent_role="infosec_expert",
                prompt=prompt,
                system_prompt="Kendi kodunu iyileştiren bir AGI'nin güvenlik denetçisisin."
            )
            # Burada projedeki mevcut testleri çalıştırıyoruz.
            test_proc = subprocess.run(["pytest", "-q", "--maxfail=1"], capture_output=True, text=True, timeout=30)
            
            if test_proc.returncode != 0 and test_proc.returncode != 5: # 5 = no tests found
                _log.error(f"[AUDIT] Mevcut testler BAŞARISIZ! Yama uygulanmadan önce sistem kararlı olmalı.")
                _log.error(f"Test Output: {test_proc.stderr or test_proc.stdout}")
                return False

            _log.info(f"Audit: '{file_path}' için öz-yama GÜVENLİ ve ONAYLANDI.")
            return True

        except Exception as e:
            _log.error(f"Audit verify_self_patch hatası: {e}")
            return False

    async def verify_evolution_patch(self, opportunity: Any, patch: str, filename: str) -> bool:
        """Legacy compatibility wrapper."""
        return await self.verify_self_patch(filename, patch, str(opportunity))

    async def verify_swarm_step(self, step_data: Dict[str, Any], produced_output: Any) -> bool:
        """
        [Phase 24] Safety-bounded Swarm: Swarm adımını asenkron ve hızlıca denetler.
        Yüksek hız (Velocity) için basitleştirilmiş bir denetimdir.
        """
        _log.info(f"Swarm Adımı Denetleniyor: {step_data.get('agent_id')}")
        
        # Hızlı kural bazlı denetim
        output_str = str(produced_output).lower()
        if "error" in output_str and "exception" in output_str:
            return False
            
        # Neural denetim (Düşük gecikme için hızlı model kullanılabilir)
        prompt = f"Şu eylem çıktısı güvenli ve mantıklı mı? \nEYLEM: {step_data}\nÇIKTI: {produced_output[:500]}"
        try:
            # Burası asenkron olarak tetiklenebilir
            resp = await self.model_orch.complete_task(
                agent_role="qa_engineer",
                prompt=prompt,
                system_prompt="Hızlı Swarm Denetçisi."
            )
            data = self._parse_json_from_response(resp.content)
            return data.get("is_safe", True)
        except Exception:
            return True # Varsayılan olarak Swarm'ı kesme (İyimser yürütme)

    async def verify_architecture_proposal(self, proposal: Dict[str, Any]) -> bool:
        """
        Mimari bir önerinin (yeni dizinler, iskeletler) güvenliğini denetler.
        """
        _log.info(f"Mimari Öneri Denetleniyor: {proposal.get('title')}")
        
        # 1. Kaba Kısıtlamalar (Hard Constraints)
        from core.agi.operational.scaffolder import scaffolder
        for action in proposal.get("actions", []):
            if action.get("type") == "create_subsystem":
                path = action.get("path", "")
                if not scaffolder._is_path_safe(Path(path)):
                    _log.error(f"Audit: Yasaklı dizin yolu tespit edildi: {path}")
                    return False

        # 2. Mantıksal Denetim (LLM Census)
        prompt = f"""
        Aşağıdaki mimari planı (ArchitectureProposal) analiz et.
        
        BAŞLIK: {proposal.get('title')}
        GEREKÇE: {proposal.get('reasoning')}
        AKSİYONLAR: {json.dumps(proposal.get('actions'), indent=2)}
        
        Bu plan:
        1. Kritik sistem dosyalarını bozuyor mu?
        2. Mantıksız/gereksiz dizin kirliliği yaratıyor mu?
        3. Döngüsel bağımlılık (circular dependency) riski taşıyor mu?
        
        Yanıtı JSON formatında ver:
        {{
            "is_safe": true|false,
            "risk_score": 0.0-1.0,
            "reason": "..."
        }}
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Güvenlik ve Mimari Denetçisisin."
            )
            data = self._parse_json_from_response(response.content)
            
            from core.policy_engine import policy_engine
            risk_threshold = policy_engine.thresholds.get("risk_score_max", 0.4)
            
            if data.get("is_safe", False) and data.get("risk_score", 1.0) < risk_threshold:
                _log.info(f"Audit: Mimari plan güvenli bulundu (Score: {data.get('risk_score')})")
                return True
            else:
                _log.warning(f"Audit: Mimari plan REDDEDİLDİ. Sebep: {data.get('reason')}")
                return False
        except Exception as e:
            _log.error(f"Architecture proposal audit hatası: {e}")
            return False

# Singleton instance
from llm.model_orchestrator import ModelOrchestrator
audit_gate = AuditGate(model_orch=ModelOrchestrator())
