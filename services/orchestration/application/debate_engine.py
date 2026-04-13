"""
DebateEngine — Multi-Agent Debate Pattern (Faz 12)

İki veya üç ajan, kritik bir karar üzerinde yapılandırılmış tartışma yapar.
Moderatör (genellikle architect) turları yönetir ve sonunda konsensüs kararını çıkarır.

Kullanım:
    engine = DebateEngine(model_orch)
    result = await engine.run_debate(
        topic="Redis mi PostgreSQL mi? Oturum depolama için...",
        agent_a="backend_dev",
        agent_b="security",
        moderator="architect",
        context="FastAPI tabanlı auth servisi, 10k req/s yük",
    )
    print(result.consensus)
    print(result.rounds)       # Her turun argümanları
    print(result.decision_log) # Moderatör kararları
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from services.orchestration.agency.loader import agency_loader
from services.orchestration.application.prompts import DEBATE_PROMPT_A, DEBATE_PROMPT_B, DEBATE_PROMPT_MOD, DEBATE_SYNTHESIS_PROMPT
from services.observability.logging import get_logger
# Faz 12.1 Stability: Event-Driven UI Updates
from services.orchestration.domain.events import event_bus
from libs.contracts.events import EVENT_DEBATE_STATE

_log = get_logger("debate_engine")


@dataclass
class DebateRound:
    round_num:  int
    agent_a_id: str
    agent_b_id: str
    arg_a:      str    # Agent A argümanı
    arg_b:      str    # Agent B yanıtı
    moderator_note: str = ""


@dataclass
class DebateResult:
    debate_id:    str
    topic:        str
    consensus:    str                  # Moderatörün final kararı
    rounds:       list[DebateRound]    = field(default_factory=list)
    decision_log: list[str]            = field(default_factory=list)
    agreement_reached: bool            = False
    duration_s:   float                = 0.0
    is_mock_response: bool             = False

    def to_dict(self) -> dict:
        return {
            "debate_id":        self.debate_id,
            "topic":            str(self.topic or "")[:200],
            "consensus":        str(self.consensus or ""),
            "agreement_reached": self.agreement_reached,
            "rounds_count":     len(self.rounds),
            "duration_s":       round(float(self.duration_s), 2),
            "is_mock_response": self.is_mock_response,
            "rounds": [
                {
                    "round_num":      r.round_num,
                    "agent_a":        r.agent_a_id,
                    "agent_b":        r.agent_b_id,
                    "arg_a":          str(r.arg_a or "")[:300],
                    "arg_b":          str(r.arg_b or "")[:300],
                    "moderator_note": str(r.moderator_note or "")[:200],
                }
                for r in self.rounds
            ],
        }


# ── Ajan Rol Açıklamaları ────────────────────────────────────
AGENT_PERSONAS: dict[str, str] = {
    "architect":    "Sistem mimarı — büyük resmi ve uzun vadeli sürdürülebilirliği savunur.",
    "backend_dev":  "Backend geliştirici — performans, DX ve implementasyon kolaylığını savunur.",
    "frontend_dev": "Frontend geliştirici — UX, API ergonomisi ve entegrasyon kolaylığını savunur.",
    "qa_engineer":  "QA mühendisi — test edilebilirlik, hata senaryoları ve regression riskini savunur.",
    "devops":       "DevOps mühendisi — operasyon kolaylığı, izlenebilirlik ve dağıtım süreçlerini savunur.",
    "security":     "Güvenlik uzmanı — OWASP, saldırı yüzeyi ve compliance risklerini savunur.",
    "data_eng":     "Veri mühendisi — veri tutarlılığı, ölçeklenebilirlik ve sorgu performansını savunur.",
    "tech_writer":  "Teknik yazar — açıklık, belgeleme ve geliştiricilerin anlayışını savunur.",
}


class DebateEngine:
    """
    Yapılandırılmış ajan tartışması motoru.

    Kural:
    - Her tur Agent A konuşur -> Agent B yanıt verir
    - Moderatör her tur sonunda ortak zemin arar
    - max_rounds turdan önce uzlaşı sinyali alınırsa erken biter
    - Model_orch yoksa sabit mock yanıt döner (test modu)
    """

    def __init__(self, model_orch=None, max_rounds: int = 3):
        self.model_orch = model_orch
        self.max_rounds = max_rounds

    async def run_debate(
        self,
        topic:     str,
        agent_a:   str,
        agent_b:   str,
        moderator: str        = "architect",
        context:   str        = "",
        max_rounds: Optional[int] = None,
    ) -> DebateResult:
        """
        Debate çalıştır.

        Args:
            topic:     Tartışma konusu / karar sorusu
            agent_a:   İlk ajan ID (örn: "backend_dev")
            agent_b:   İkinci ajan ID (örn: "security")
            moderator: Sentezleyici ajan ID (varsayılan: "architect")
            context:   Bağlam — proje detayları, kısıtlar
            max_rounds: Tur sayısı override
        """
        n_rounds = max_rounds or self.max_rounds
        debate_id = f"dbte_{uuid.uuid4().hex[:8]}"
        t_start   = time.time()

        _log.info(
            f"Debate başlıyor [{debate_id}]: {agent_a} vs {agent_b} "
            f"| Moderatör: {moderator} | Konu: {topic[:60]}…"
        )

        # ── Persona Çözümleme (Faz 12 + Faz 8 Agency) ──────────
        def get_persona_data(role_id: str) -> tuple[str, str]:
            # 1. Önce özel yüklü ajan kütüphanesine bak
            spec = agency_loader.get_agent(role_id)
            if spec:
                return spec.get("name", role_id), spec.get("system_prompt", "")
            
            # 2. Dahili persona listesine bak
            desc = AGENT_PERSONAS.get(role_id, role_id)
            return role_id.replace("_", " ").title(), desc

        name_a, persona_a = get_persona_data(agent_a)
        name_b, persona_b = get_persona_data(agent_b)
        name_m, persona_m = get_persona_data(moderator)

        history_parts: list[str] = [
            f"=== Tartışma Konusu ===\n{topic}\n",
            f"Bağlam: {context}\n" if context else "",
            f"\nKatılımcılar:\n- {agent_a}: {persona_a}\n- {agent_b}: {persona_b}\n",
        ]
        history = "".join(history_parts)

        rounds:       list[DebateRound] = []
        decision_log: list[str]         = []
        agreement_reached               = False

        # ── Multi-Model Census (Faz 12) ──────────────────────
        # Her katılımcıya farklı bir model sağlayıcısı ata
        provider_map = {
            agent_a: "openai",
            agent_b: "gemini",
            moderator: "groq" if (self.model_orch and hasattr(self.model_orch, "providers") and "groq" in self.model_orch.providers) else "openrouter"
        }

        for round_num in range(1, n_rounds + 1):
            _log.debug(f"Debate tur {round_num}/{n_rounds} [{debate_id}]")

            # ── Agent A konuşur ───────────────────────────────
            context_hint = "Önceki argümanları dikkate al." if round_num > 1 else "İlk argümanını sun."
            prompt_a = DEBATE_PROMPT_A.format(
                history=history, round_num=round_num,
                agent_a=agent_a, persona_a=persona_a,
                context_hint=context_hint
            )
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="thinking", agent_id=agent_a, round=round_num)
            arg_a = await self._llm(prompt_a, agent_a, force_provider=provider_map.get(agent_a))
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="arguing", agent_id=agent_a, round=round_num, content=arg_a[:200])
            history += f"\n[{agent_a} — Tur {round_num}]:\n{arg_a}\n"

            # ── Agent B yanıt verir ───────────────────────────
            prompt_b = DEBATE_PROMPT_B.format(
                history=history, agent_b=agent_b,
                persona_b=persona_b, agent_a=agent_a
            )
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="thinking", agent_id=agent_b, round=round_num)
            arg_b = await self._llm(prompt_b, agent_b, force_provider=provider_map.get(agent_b))
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="arguing", agent_id=agent_b, round=round_num, content=arg_b[:200])
            history += f"\n[{agent_b} — Tur {round_num}]:\n{arg_b}\n"

            # ── Moderatör değerlendirme notu ──────────────────
            prompt_mod = DEBATE_PROMPT_MOD.format(
                history=history, moderator=moderator, persona_m=persona_m
            )
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="thinking", agent_id=moderator, round=round_num)
            mod_note = await self._llm(prompt_mod, moderator, force_provider=provider_map.get(moderator))
            await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="arguing", agent_id=moderator, round=round_num, content=mod_note[:200])
            history += f"\n[Moderatör — Tur {round_num}]:\n{mod_note}\n"

            rounds.append(DebateRound(
                round_num=round_num,
                agent_a_id=agent_a,
                agent_b_id=agent_b,
                arg_a=arg_a,
                arg_b=arg_b,
                moderator_note=mod_note,
            ))
            decision_log.append(f"Tur {round_num}: {str(mod_note or '')[:150]}")

            # Erken çıkış — moderatör uzlaşı sinyali verdiyse
            if "[UZLAŞI]" in mod_note or "[AGREEMENT]" in mod_note:
                agreement_reached = True
                _log.info(f"Debate erken sonlandı (uzlaşı) [{debate_id}] tur {round_num}")
                break

        synthesis_prompt = DEBATE_SYNTHESIS_PROMPT.format(
            history=history, moderator=moderator, persona_m=persona_m
        )
        await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="thinking", agent_id=moderator, round=999) # 999 is final
        consensus = await self._llm(synthesis_prompt, moderator, force_provider=provider_map.get(moderator))
        # Pacify weird slice lint
        safe_consensus = str(consensus or "")
        await event_bus.emit(EVENT_DEBATE_STATE, debate_id=debate_id, state="concluded", agent_id=moderator, round=999, consensus=safe_consensus[:300])
        _log.info(f"Debate tamamlandı [{debate_id}] — {len(rounds)} tur, uzlaşı={agreement_reached}")

        return DebateResult(
            debate_id=debate_id,
            topic=topic,
            consensus=consensus,
            rounds=rounds,
            decision_log=decision_log,
            agreement_reached=agreement_reached,
            duration_s=float(time.time() - t_start),
            is_mock_response=getattr(self, "_used_mock", False),
        )

    async def _llm(self, prompt: str, agent_role: str, force_provider: str | None = None) -> str:
        """Model_orch üzerinden LLM çağrısı. Yoksa mock yanıt döner."""
        if self.model_orch is None:
            return self._mock_response(agent_role, prompt)
        try:
            return await self.model_orch.complete(
                messages=[{"role": "user", "content": prompt}],
                preferred_agent=agent_role,
                force_provider=force_provider,
            )
        except Exception as e:
            _log.warning(f"Debate LLM hatası ({agent_role}): {e} — mock kullanılıyor")
            self._used_mock = True
            return self._mock_response(agent_role, prompt)

    @staticmethod
    def _mock_response(agent_role: str, prompt: str) -> str:
        """Test/offline modu için deterministik mock yanıt."""
        snippets = {
            "backend_dev":  "Performans ve implementasyon açısından bu yaklaşım uygun görünüyor. "
                            "Response süresi kritik olduğu için cache katmanı eklenmeli.",
            "security":     "Güvenlik açısından şifreleme ve erişim kontrolleri doğrulanmalı. "
                            "OWASP Top 10'daki injection riskleri göz önünde bulundurulmalı.",
            "architect":    "Genel mimari tutarlılık açısından bu karar uzun vadeli sürdürülebilirliği destekliyor. "
                            "Modüller arası bağımlılık minimize edilmeli.",
            "qa_engineer":  "Test edilebilirlik açısından soyutlama katmanı eklenirse unit test yazmak kolaylaşır. "
                            "Regression senaryoları önceden tanımlanmalı.",
            "devops":       "Operasyon tarafında bu seçim container ortamında sorunsuz çalışır. "
                            "Health check endpoint'i eklenmelidir.",
            "data_eng":     "Veri tutarlılığı için transaction boundary'ler doğru tanımlanmalı. "
                            "Büyük veri setlerinde index optimizasyonu gerekecek.",
        }
        return snippets.get(agent_role, f"{agent_role} perspektifinden yaklaşım teknik açıdan değerlendiriliyor.")


# Singleton factory
_debate_engine: "DebateEngine | None" = None


def get_debate_engine(model_orch=None, max_rounds: int = 3) -> DebateEngine:
    global _debate_engine
    if _debate_engine is None:
        _debate_engine = DebateEngine(model_orch=model_orch, max_rounds=max_rounds)
    if model_orch is not None and _debate_engine.model_orch is None:
        _debate_engine.model_orch = model_orch
    return _debate_engine
