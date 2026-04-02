import os
import asyncio
from typing import List, Dict, Any, Optional
from core.agi.schemas import UnifiedInput, SourceType, ProblemFrame, TaskType, RiskLevel
from observability.logging import get_logger

_log = get_logger("agi_self_audit")

# Dosya başına maksimum karakter (LLM context tasarrufu için)
_MAX_FILE_CHARS = 3000
# Tek seferde analiz edilecek maksimum dosya sayısı
_MAX_FILES_PER_BATCH = 6


class SelfAuditAgent:
    """
    Final AGI Layer (Katman 10): Self-Correction / Self-Bootstrapping.
    [FIX-7] Kendi kod tabanını LLM ile otonom olarak analiz eder ve
    teknik borç / iyileştirme fırsatlarını görev kuyruğuna ekler.
    """
    def __init__(self, core_path: str = "core/agi/", model_orch=None):
        self.core_path = core_path
        self.model_orch = model_orch

    def _collect_python_files(self) -> List[str]:
        """core/agi altındaki tüm Python dosyalarını toplar."""
        collected = []
        for root, dirs, files in os.walk(self.core_path):
            # Cache ve pycache atla
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "node_modules"}]
            for f in files:
                if f.endswith(".py") and not f.startswith("test_"):
                    collected.append(os.path.join(root, f))
        return collected

    async def _analyze_file_batch(self, files: List[str]) -> List[Dict[str, Any]]:
        """
        Bir grup dosyayı LLM'e göndererek teknik borç / kritik eksik analizi yapar.
        """
        if self.model_orch is None:
            from llm.model_orchestrator import ModelOrchestrator
            self.model_orch = ModelOrchestrator()

        # Dosya içeriklerini oku ve özetle
        snippets = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                # Sadece ilk N karakter (context tasarrufu)
                preview = content[:_MAX_FILE_CHARS]
                # TODO ve pass'leri çabuk bulmak için işaret
                todos = content.count("# TODO")
                passes = content.count("\n    pass\n") + content.count("\n        pass\n")
                snippets.append(
                    f"--- FILE: {fpath} (TODOs: {todos}, bare_pass: {passes}) ---\n{preview}"
                )
            except Exception:
                continue

        if not snippets:
            return []

        combined = "\n\n".join(snippets)
        prompt = f"""
Aşağıdaki AGI çekirdek modüllerini incele.
Her biri için şunu değerlendir:
1. Gerçekten işlevsiz veya eksik ("pass", "# TODO", "return []" ile biten metodlar)
2. İçe aktarılmamış (import edilmemiş) ama kullanılan sınıf/fonksiyonlar
3. Singleton veya bağlantı hataları

KOD DOSYALARI:
{combined[:8000]}

Her sorun için JSON listesi döndür:
[
  {{
    "file": "dosya_yolu",
    "severity": "critical|high|medium",
    "issue": "Sorunun kısa tanımı (max 100 karakter)",
    "suggested_fix": "Önerilen düzeltme (max 200 karakter)"
  }}
]
Eğer hiç sorun yoksa boş liste döndür: []
"""
        try:
            response = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt=(
                    "Sen bir AGI Öz-Denetim (Self-Audit) uzmanısın. "
                    "Python kodundaki gerçek sorunları (işlevsiz metodlar, eksik importlar, "
                    "yüzeysel implementasyonlar) tespit edersin. Abartma; sadece gerçek sorunları yaz."
                )
            )
            import json, re
            match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if match:
                issues = json.loads(match.group())
                if isinstance(issues, list):
                    return issues
        except Exception as e:
            _log.error(f"[SELF-AUDIT] Batch analiz hatası: {e}")
        return []

    async def scan_core(self) -> List[UnifiedInput]:
        """
        AGI çekirdek dizinini tarar, sorunları LLM ile analiz eder ve
        her sorun için bir self-repair görevi (UnifiedInput) üretir.
        """
        _log.info(f"[SELF-AUDIT] Öz-Denetim başlatıldı: {self.core_path}")
        all_files = self._collect_python_files()
        _log.info(f"[SELF-AUDIT] {len(all_files)} Python dosyası bulundu.")

        # Dosyaları gruplara böl
        batches = [
            all_files[i:i + _MAX_FILES_PER_BATCH]
            for i in range(0, min(len(all_files), _MAX_FILES_PER_BATCH * 3), _MAX_FILES_PER_BATCH)
        ]

        all_issues: List[Dict[str, Any]] = []
        for batch in batches:
            issues = await self._analyze_file_batch(batch)
            all_issues.extend(issues)
            _log.info(f"[SELF-AUDIT] Batch analiz: {len(issues)} sorun bulundu.")

        # Sorunları self-repair UnifiedInput görevlerine dönüştür
        tasks: List[UnifiedInput] = []
        for issue in all_issues:
            severity = issue.get("severity", "medium")
            urgency = {"critical": 9, "high": 7, "medium": 5}.get(severity, 5)
            tasks.append(UnifiedInput(
                source_type=SourceType.MONITORING,
                raw_payload=f"[SELF-AUDIT] {issue.get('file')}: {issue.get('issue')}",
                normalized_intent=issue.get("suggested_fix", ""),
                urgency=urgency,
                domain_hint="self_repair",
                metadata={
                    "audit_source": "SelfAuditAgent",
                    "file": issue.get("file"),
                    "severity": severity,
                    "issue": issue.get("issue"),
                    "suggested_fix": issue.get("suggested_fix"),
                }
            ))

        _log.info(f"[SELF-AUDIT] Toplam {len(tasks)} self-repair görevi üretildi.")
        return tasks

    async def run_cleanup(self):
        """Otonom bakım görevlerini tetikler ve sonuçları loga yazar."""
        tasks = await self.scan_core()
        if not tasks:
            _log.info("[SELF-AUDIT] Hiç sorun tespit edilmedi.")
            return

        for t in tasks:
            severity = t.metadata.get("severity", "medium")
            _log.warning(
                f"[SELF-AUDIT][{severity.upper()}] "
                f"Öz-Düzeltme Görevi: {t.raw_payload} | "
                f"Öneri: {t.normalized_intent}"
            )
        # Gelecekte: bu görevleri merkezi orkestrasyon kuyruğuna besle
        # await central_executive.queue_tasks(tasks)

    async def run_background_loop(self, interval_hours: float = 24.0):
        """24 saatte bir otonom öz-denetim çalıştırır."""
        _log.info(f"[SELF-AUDIT] Arka plan döngüsü başlatıldı ({interval_hours}h periyot).")
        while True:
            try:
                await self.run_cleanup()
            except Exception as e:
                _log.error(f"[SELF-AUDIT] Arka plan hatası: {e}")
            await asyncio.sleep(interval_hours * 3600)


# --- Singleton ---
self_audit = SelfAuditAgent()
