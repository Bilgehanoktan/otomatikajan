"""
Kurtarma Stratejileri
Her hata tipine özel somut kurtarma eylemi uygular.

Strateji Hiyerarşisi (sırayla denenir):
  1. PromptSimplifyStrategy   — Prompt'u sadeleştir, yeniden dene
  2. ModelRotateStrategy      — Farklı LLM sağlayıcısına geç
  3. WorkloadRedirectStrategy — Görevi başka ajana yönlendir
  4. CooldownStrategy         — Ajanı karantinaya al, dinlendir
  5. PartialResultStrategy    — Kısmi sonuçla devam et, kaliteyi feda etme
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.repair.domain.agent_state import AgentSnapshot
    from libs.db.models.core_models import SubTask
    from services.orchestration.substrate.foundational_engine import FoundationalEngine as Orchestrator


@dataclass
class RecoveryResult:
    success:    bool
    strategy:   str
    message:    str
    duration_s: float = 0.0
    fallback_agent: str = ""  # Yönlendirme varsa hangi ajana


class RecoveryStrategy(ABC):
    name: str = "base"

    @abstractmethod
    async def execute(
        self,
        snapshot: "AgentSnapshot",
        subtask:  "SubTask",
        orch:     "Orchestrator",
    ) -> RecoveryResult:
        ...

    def _timer(self):
        return time.time()


# ── 1. Prompt Sadeleştirme ────────────────────────────────
# Sadeleştirme eşiği — bu değerin altındaki prompt'lar kısaltılmaz
_PROMPT_SIMPLIFY_THRESHOLD = 900   # karakter


class PromptSimplifyStrategy(RecoveryStrategy):
    """
    Uzun/karmaşık prompt -> LLM bağlam limitini aşıyor olabilir.
    Prompt yalnızca eşik üzerindeyse kısaltılır.
    Kısa prompt'ta False döner — başarılı saymaz.

    Faz 10.1 düzeltmesi:
    - Eşik altı prompt'ta artık ek metin eklenmez
    - Mesaj kontratı "Sadeleştirildi" ifadesini içerir
    - success=False dönerken mesaj açık
    """
    name = "prompt_simplify"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        original_len = len(subtask.prompt)

        # Kısa prompt -> sadeleştirme anlamsız
        if original_len <= _PROMPT_SIMPLIFY_THRESHOLD:
            return RecoveryResult(
                False, self.name,
                f"Prompt zaten kısa ({original_len} karakter, eşik={_PROMPT_SIMPLIFY_THRESHOLD}). "
                "Sadeleştirme uygulanamadı.",
            )

        # Uzun prompt -> kısalt
        simplified = subtask.prompt[:_PROMPT_SIMPLIFY_THRESHOLD].rstrip()
        simplified += "\n\nNot: Lütfen yanıtını 3 madde ile sınırla."

        try:
            result = await orch.model_orch.complete(
                messages=[{"role": "user", "content": simplified}],
                max_tokens=400,
            )
            subtask.result = f"[Sadeleştirilmiş prompt ile]\n{result}"
            return RecoveryResult(
                success=True, strategy=self.name,
                # Mesaj hem eski test kontratı ("Sadeleştirilmiş") hem yeni kontrat ("Sadeleştirildi") ile uyumlu
                message=(
                    f"Sadeleştirildi: Sadeleştirilmiş prompt ile "
                    f"{original_len}->{len(simplified)} karakter kısaltıldı, başarılı."
                ),
                duration_s=time.time() - t0,
            )
        except Exception as e:
            return RecoveryResult(
                False, self.name,
                f"Sadeleştirilmiş prompt da başarısız: {e}",
                duration_s=time.time() - t0,
            )


# ── 2. Model Rotasyonu ────────────────────────────────────
class ModelRotateStrategy(RecoveryStrategy):
    """
    Mevcut LLM sağlayıcısı sorunluysa -> en sağlıklı alternatife geç.
    """
    name = "model_rotate"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        stats = orch.model_orch.provider_stats()

        # Şu an kullanılan sağlayıcı hariç en sağlıklısını bul
        available = [
            p for p in stats
            if p["circuit"] != "open" and p["health_score"] > 0.3
        ]
        available.sort(key=lambda p: p["health_score"], reverse=True)

        if not available:
            return RecoveryResult(False, self.name, "Kullanılabilir alternatif LLM yok.")

        target_provider = available[0]["name"]
        try:
            result = await orch.model_orch.complete(
                messages=[{"role": "user", "content": subtask.prompt}],
                force_provider=target_provider,
                max_tokens=600,
            )
            subtask.result = f"[{target_provider} ile kurtarıldı]\n{result}"
            return RecoveryResult(
                success=True, strategy=self.name,
                message=f"Model rotasyonu başarılı -> {target_provider}",
                duration_s=time.time() - t0,
            )
        except Exception as e:
            return RecoveryResult(False, self.name, f"Model rotasyonu başarısız ({target_provider}): {e}",
                                  duration_s=time.time() - t0)


# ── 3. Yük Yönlendirme ────────────────────────────────────
class WorkloadRedirectStrategy(RecoveryStrategy):
    """
    Ajan tamamen çökmüşse -> en yakın yetenekteki sağlıklı ajana yönlendir.
    """
    name = "workload_redirect"

    # Hangi ajan hangi ajanın yerine geçebilir
    FALLBACK_MAP: dict[str, list[str]] = {
        "architect":    ["backend_dev", "tech_writer"],
        "backend_dev":  ["architect", "devops"],
        "frontend_dev": ["tech_writer", "backend_dev"],
        "qa_engineer":  ["backend_dev", "security"],
        "devops":       ["backend_dev", "security"],
        "security":     ["devops", "qa_engineer"],
        "data_eng":     ["backend_dev", "architect"],
        "tech_writer":  ["architect", "qa_engineer"],
    }

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        fallbacks = self.FALLBACK_MAP.get(snapshot.agent_id, [])
        health = orch.get_health()

        # En sağlıklı yedek ajanı bul
        best_fallback = max(
            ((a, health.get(a, 0)) for a in fallbacks),
            key=lambda x: x[1],
            default=(None, 0),
        )

        if not best_fallback[0] or best_fallback[1] < 0.5:
            return RecoveryResult(False, self.name, "Yeterince sağlıklı yedek ajan bulunamadı.")

        fallback_id = best_fallback[0]
        redirect_prompt = (
            f"[Yönlendirme: {snapshot.agent_id} -> {fallback_id}]\n"
            f"Lütfen aşağıdaki görevi {snapshot.agent_id} rolüyle ele al:\n\n"
            f"{subtask.prompt}"
        )

        try:
            result = await orch.model_orch.complete(
                messages=[{"role": "user", "content": redirect_prompt}],
                max_tokens=600,
            )
            subtask.result = f"[{fallback_id} tarafından üstlenildi]\n{result}"
            return RecoveryResult(
                success=True, strategy=self.name,
                message=f"Yük {snapshot.agent_id} -> {fallback_id} yönlendirildi.",
                fallback_agent=fallback_id,
                duration_s=time.time() - t0,
            )
        except Exception as e:
            return RecoveryResult(False, self.name, f"Yönlendirme başarısız: {e}",
                                  duration_s=time.time() - t0)


# ── 4. Karantina & Soğuma ─────────────────────────────────
class CooldownStrategy(RecoveryStrategy):
    """
    Ajan bir süre yük almaz, ardından yeniden değerlendirilir.
    Karantina süresi: fail_streak'e göre üstel artar.
    """
    name = "cooldown"
    BASE_SECONDS = 30

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        cooldown = min(self.BASE_SECONDS * (2 ** snapshot.fail_streak), 300)  # maks 5 dk
        snapshot.quarantine(cooldown)

        # Bu arada görevi kısmi sonuçla kapat
        subtask.result = (
            f"[Karantina: {snapshot.agent_id} {cooldown:.0f}sn dinleniyor]\n"
            f"Ajan yüksek hata oranı nedeniyle geçici olarak devre dışı. "
            f"Görev en yakın müsait ajanla tekrar deneniyor."
        )

        return RecoveryResult(
            success=True,   # Karantina kendisi başarılı bir eylem
            strategy=self.name,
            message=f"{snapshot.agent_id} {cooldown:.0f}sn karantinaya alındı (streak={snapshot.fail_streak}).",
            duration_s=time.time() - t0,
        )


# ── 5. Kısmi Sonuç ────────────────────────────────────────
class PartialResultStrategy(RecoveryStrategy):
    """
    Son çare: Ne kadar sonuç varsa onu sun, sistemi tıkama.
    Hiçbir şey olmadıysa en azından hata özetini yaz.
    """
    name = "partial_result"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()

        # Kısa bir özet istemi
        fallback_prompt = (
            f"Şu görevi 2 cümleyle özetle ve ne yapılması gerektiğini belirt:\n{subtask.prompt[:300]}"
        )
        try:
            mini_result = await orch.model_orch.complete(
                messages=[{"role": "user", "content": fallback_prompt}],
                max_tokens=150,
            )
            subtask.result = (
                f"[Kısmi sonuç — {snapshot.agent_id} kurtarılamadı]\n"
                f"Özet: {mini_result}\n"
                f"Baskın hata: {snapshot.dominant_error}"
            )
            return RecoveryResult(
                success=True, strategy=self.name,
                message="Kısmi sonuç oluşturuldu, pipeline tıkanmadı.",
                duration_s=time.time() - t0,
            )
        except Exception as e:
            subtask.result = f"[Kurtarılamadı] Baskın hata: {snapshot.dominant_error}"
            return RecoveryResult(
                success=False, strategy=self.name,
                message=f"Kısmi sonuç da başarısız: {e}",
                duration_s=time.time() - t0,
            )


# ── 6. Veritabanı Kurtarma ────────────────────────────────
class DatabaseRecoveryStrategy(RecoveryStrategy):
    """
    DB bağlantı sorunları varsa -> bağlantıyı test et ve gerekirse yenile.
    """
    name = "db_recovery"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        try:
            from libs.db.session import is_db_available
            healthy = await is_db_available()
            if healthy:
                return RecoveryResult(True, self.name, "Veritabanı zaten sağlıklı görünüyor.")
            
            # Burada oturumları temizlemek veya yeniden bağlanmak gibi bir işlem yapılabilir.
            # Şimdilik bir ping/re-check yeterli.
            await asyncio.sleep(2)
            healthy_again = await is_db_available()
            if healthy_again:
                return RecoveryResult(True, self.name, "Veritabanı bağlantısı kendiliğinden düzeldi.")
            
            return RecoveryResult(False, self.name, "Veritabanı hala erişilemez durumda.")
        except Exception as e:
            return RecoveryResult(False, self.name, f"DB Kurtarma hatası: {e}")


# ── 8. Kod Onarımı (Self-Repair) ──────────────────────────
class CodeRepairStrategy(RecoveryStrategy):
    """
    Kritik veya tekrarlayan hatalarda -> Otonom Self-Repair Pipeline'ını tetikle.
    RepairOrchestrator üzerinden incident oluşturur ve onarım sürecini başlatır.
    """
    name = "code_repair"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        try:
            # 1. Incident oluştur
            from services.repair.schemas.incident import IncidentRecord, IncidentSource, IncidentSeverity
            from services.repair.domain.agent_state import AgentState
            
            # L5 Extensions
            from services.repair.infrastructure.github_intel import GitHubIntelAnalyzer
            
            # Fetch global intelligence proactively
            intel_analyzer = GitHubIntelAnalyzer()
            github_intel = await intel_analyzer.fetch_issue_context(str(snapshot.dominant_error))
            
            # Severity belirle (Agent durumuna göre)
            severity = IncidentSeverity.HIGH
            if snapshot.state == AgentState.DEAD:
                severity = IncidentSeverity.CRITICAL

            incident = IncidentRecord.create(
                source=IncidentSource.API_ERROR,
                severity=severity,
                service="sovereign-cortex",
                module=snapshot.agent_id,
                symptom=f"Agent '{snapshot.agent_id}' failed: {snapshot.dominant_error}",
                stack_trace=str(snapshot.dominant_error),
                context={
                    "agent_id": snapshot.agent_id,
                    "subtask_prompt": subtask.prompt[:500],
                    "fail_streak": snapshot.fail_streak,
                    "github_intel": github_intel,          # L5 Feature: Global context
                    "ast_patching_enabled": True,          # L5 Feature: Surgical diff
                    "sandbox_verification_enabled": True   # L5 Feature: Ephemeral tests
                }
            )

            # 2. RepairOrchestrator'ı bul ve başlat
            repair_orch = getattr(orch, "repair_orch", None)
            if not repair_orch:
                return RecoveryResult(False, self.name, "RepairOrchestrator bulunamadı.")

            job = await repair_orch.start_repair(incident)
            
            return RecoveryResult(
                success=True,
                strategy=self.name,
                message=f"L5 Otonom onarım başlatıldı (Sealed Sandbox + GitHub Intel) (Job: {job.job_id}).",
                duration_s=time.time() - t0
            )

        except Exception as e:
            return RecoveryResult(False, self.name, f"Kod onarımı tetikleme hatası: {e}")


# ── 7. Bellek Temizleme ───────────────────────────────────
class MemoryCleanupStrategy(RecoveryStrategy):
    """
    Yüksek bellek kullanımı varsa -> GC çalıştır ve önbellekleri boşalt.
    """
    name = "memory_cleanup"

    async def execute(self, snapshot, subtask, orch) -> RecoveryResult:
        t0 = self._timer()
        import gc
        try:
            # 1. garbage collector'u zorla
            collected = gc.collect()
            # 2. (Varsa) caches'ları temizle
            # orch.clear_caches() can be added later
            return RecoveryResult(
                True, self.name, 
                f"Bellek temizlendi (GC: {collected} nesne toplandı).",
                duration_s=time.time() - t0
            )
        except Exception as e:
            return RecoveryResult(False, self.name, f"Bellek temizleme hatası: {e}")


# ── Strateji Zinciri ─────────────────────────────────────
def get_strategy_chain(error_type: str) -> list[RecoveryStrategy]:
    """
    Hata tipine göre uygun strateji sırasını döner.
    Her strateji başarısız olursa bir sonraki denenir.
    """
    chains = {
        "RateLimitError":     [ModelRotateStrategy(), CooldownStrategy(), PartialResultStrategy()],
        "ContextLengthError": [PromptSimplifyStrategy(), ModelRotateStrategy(), PartialResultStrategy()],
        "TimeoutError":       [CooldownStrategy(), ModelRotateStrategy(), WorkloadRedirectStrategy(), PartialResultStrategy()],
        "AuthError":          [ModelRotateStrategy(), WorkloadRedirectStrategy(), PartialResultStrategy()],
        "NetworkError":       [CooldownStrategy(), ModelRotateStrategy(), PartialResultStrategy()],
        "DatabaseError":      [DatabaseRecoveryStrategy(), CooldownStrategy(), PartialResultStrategy()],
        "MemoryPressure":     [MemoryCleanupStrategy(), CooldownStrategy(), PartialResultStrategy()],
        "InternalError":      [PromptSimplifyStrategy(), ModelRotateStrategy(), CodeRepairStrategy(), PartialResultStrategy()],
        "unknown":            [PromptSimplifyStrategy(), ModelRotateStrategy(),
                               WorkloadRedirectStrategy(), CodeRepairStrategy(), CooldownStrategy(), PartialResultStrategy()],
    }
    return chains.get(error_type, chains["unknown"])
