import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import logging
import httpx
import random
from db.session import AsyncSessionLocal
from db.models import SovereignModelPolicy, LLMCostLog
from sqlalchemy import select
from core.agi.monitoring.token_budgeter import token_budgeter
from core.agi.operational.resource_manager import resource_manager
from core.agi.consciousness.affective_core import affective_core
from core.agi.operational.metabolic_governor import metabolic_governor, MetabolicMode

logger = logging.getLogger(__name__)

from llm.llm_types import LLMResponse, CircuitState, ProviderStats, PROVIDERS

# V2 Mimari: Ajan rolüne göre model hiyerarşisi (isimler PROVIDERS ile eşleşmeli)
ROUTING_POLICY: dict[str, list[str]] = {
    # Architect: High-end models for decision making
    "architect": ["nvidia", "openai", "groq", "openrouter", "gemini", "anthropic"],
    
    # Backend Dev: Coding expertise
    "backend_dev": ["nvidia", "openai", "groq", "openrouter", "gemini", "anthropic"],
    
    # QA Engineer: Large context and speed (Balanced)
    "qa_engineer": ["openai", "gemini", "groq", "openrouter", "anthropic"],
    
    # Security: Precise and strict
    "security": ["nvidia", "openai", "groq", "anthropic"],
    
    # Tech Writer: Fluent and cheap
    "tech_writer": ["gemini", "openai", "groq", "openrouter", "anthropic"],
    
    # Self Governor: Decision/Planning
    "self_governor": ["openai", "groq", "gemini", "anthropic"],
    
    # Strategist: Planning/Reasoning
    "strategist": ["nvidia", "openai", "groq", "anthropic"],
    
    # Visual Auditor: Vision-capable models
    "visual_auditor": ["gemini", "openai", "groq"],
    
    # General fallback: Distributed load
    "general": ["openai", "gemini", "groq", "openrouter", "anthropic"]
}

_COST_PER_1K: dict[str, float] = {
    "openai":    0.00015,
    "anthropic": 0.00025,
    "gemini":    0.000075,
    "groq":      0.0001,
    "openrouter": 0.0002,
    "nvidia":     0.0003,
    "moonshot":   0.00015, # Estimated
    "deepseek":   0.0001,  # Estimated
}

class ModelOrchestrator:
    """
    V2 Mimari: Ajanlardan gelen istekleri alır, ROUTING_POLICY'ye göre
    sağlayıcıları (fallback zinciriyle) dener, devre kesiciyi yönetir.
    """

    # Global Pacing & Resilience (Faz 43: Kinetik Arbiter Entegrasyonu)
    _LATENCY_HISTORY: list[float] = []

    def __init__(self):
        self.providers = {p.name: p for p in PROVIDERS}
        
        # Faz 12.1: Dinamik Başlatma (Registry'den bağımsız ama orkestrasyon için gerekli)
        self._agents: Dict[str, Any] = {} 
        self.client = httpx.AsyncClient(timeout=90.0) # Arttırılmış timeout
        logger.info(f"ModelOrchestrator: {len(self.providers)} saglayici ile baslatildi.")
        self._log_provider_status()

    async def generate(self, prompt: str, system_prompt: str = "Sen yardımcı bir AI asistansın.") -> str:
        """Orchestrator tarafından risk değerlendirmesi vb. için kullanılır."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        return await self.complete(messages)

    def _log_provider_status(self):
        found = []
        missing = []
        placeholders = []
        for p in self.providers.values():
            if not p.api_key:
                missing.append(p.name)
            elif p.is_placeholder_key():
                placeholders.append(p.name)
            else:
                found.append(p.name)
        
        if found:
            logger.info(f"[LLM] Hazır sağlayıcılar: {', '.join(found)}")
        if placeholders:
            logger.warning(f"[LLM] Placeholder anahtar tespit edildi (atlanacak): {', '.join(placeholders)}")
        if missing:
            logger.debug(f"[LLM] Anahtarı eksik sağlayıcılar: {', '.join(missing)}")

    async def get_fallback_chain(self, agent_role: str, is_critical: bool = False) -> list[str]:
        """
        Ajan rolüne, sistemin metabolik moduna ve görevin kritiklik seviyesine göre 
        dinamik sağlayıcı zinciri üretir. (Fas 81: Strategic Routing)
        """
        # 1. Ham Politika
        chain = ROUTING_POLICY.get(agent_role, ROUTING_POLICY["general"]).copy()
        
        # 2. Metabolik Filtreleme (Energy/Cost Management)
        current_mode = metabolic_governor.get_mode()
        
        # Eğer kritik bir görev değilse ve mod ECO (Verimlilik) ise: Pahalı modelleri sona at veya çıkar.
        if current_mode == MetabolicMode.ECO and not is_critical:
            # Nvidia ve OpenAI pahalı kabul edildi (Basitleştirilmiş örnek)
            expensive = ["nvidia", "openai", "anthropic"]
            chain = [p for p in chain if p not in expensive] + [p for p in chain if p in expensive]
            logger.debug(f"[METABOLIC-ROUTING] Mod: ECO. Pahalı modeller zincirin sonuna itildi.")
            
        # 3. Kritik Görev Promosyonu (Performance Boost)
        if is_critical or current_mode == MetabolicMode.TURBO:
            # Kritik görevlerde en zeki modelleri (Top-tier) en başa al
            top_tier = ["openai", "nvidia", "anthropic"]
            chain = [p for p in top_tier if p in chain] + [p for p in chain if p not in top_tier]
            logger.info(f"[STRATEGIC-ROUTING] Kritik Görev/Hız Önceliği (TURBO). Top-tier modeller başa alındı.")

        return chain

    async def complete_task(
        self,
        agent_role: str,
        prompt: str,
        system_prompt: str,
        task_id: str = "unknown",
        project_id: str | None = None
    ) -> LLMResponse:
        # Phase 7 & 43: Budget and Pacing checks are handled below

        # ── BÜTÇE KONTROLÜ (Phase 7) ──
        if project_id:
            try:
                from db.session import AsyncSessionLocal
                from db.models import Project
                async with AsyncSessionLocal() as db:
                    proj = await db.get(Project, project_id)
                    if proj and proj.budget_limit > 0 and proj.total_cost >= proj.budget_limit:
                        err_msg = f"Bütçe Aşıldı: Proje {proj.title} bütçesi (${proj.budget_limit}) tükendi."
                        logger.error(err_msg)
                        raise PermissionError(err_msg)
            except PermissionError: raise
            except Exception as e:
                logger.warning(f"Budget check error: {e}")

        # 1. Global Pacing (Faz 43: Arbiter üzerinden otomatik yönetilir)

        # 2. Bütçe ve Kaynak Kontrolü
        if not await token_budgeter.should_execute(agent_role):
            raise RuntimeError(f"Ajan {agent_role} için bütçe/hız sınırı aşıldı.")

        # 3. Prompt Hazırlığı ve Dinamik Yama (Strategist + Empathy Tuner)
        from core.prompt_manager import prompt_manager
        from core.agi.adaptation.empathy_tuner import empathy_tuner

        system_prompt = prompt_manager.apply_patch(agent_role, system_prompt)
        system_prompt = empathy_tuner.patch_system_prompt(system_prompt)

        # Phase 81: Strategic Content Analysis - Is this task critical for North Star?
        is_critical = any(kw in (prompt + system_prompt).lower() for kw in ["critical", "architectural", "security", "production", "north star"])
        
        # 4. Dinamik Fallback Zinciri
        chain = await self.get_fallback_chain(agent_role, is_critical=is_critical)
        
        # Boş mesaj koruması (400 Bad Request Fix)
        if not prompt or not prompt.strip():
            prompt = "(İçerik boş bırakıldı - otonom dolgu)"
            
        messages = [
            {"role": "system", "content": system_prompt or "Sen bir AI asistansın."},
            {"role": "user", "content": prompt}
        ]

        # Ajanın rolüne göre fallback zincirini al
        candidates = await self.get_fallback_chain(agent_role)
        
        # Faz 48: Metabolik Koordinasyon (Update & Mode Detection)
        optimal_provider_name = None
        try:
            await metabolic_governor.update_metabolism(self.providers)
            mode = metabolic_governor.get_mode()
            
            # ECO Modunda Pacing (Dinamik Yavaşlatma)
            if mode == MetabolicMode.ECO:
                # Enerjiye göre 1.5 - 5.5 saniye arası dursa (drip-feed)
                delay = 1.5 + (1.0 - affective_core.energy) * 4.0
                logger.info(f"[METABOLISM-PACING] ECO Modu Aktif: {delay:.1f}s geciktirme uygulanıyor...")
                await asyncio.sleep(delay)
                
            # Faz 48 & 64: Hibrit NAS ve Metabolizma Önceliği
            optimal_provider_name = metabolic_governor.get_optimal_provider(candidates, self.providers)
            
            # Tüm adayları sağlık puanlarına göre sırala (Faz 64)
            candidates.sort(key=lambda p: self.providers.get(p).health_score if self.providers.get(p) else 0, reverse=True)
            
            if optimal_provider_name and optimal_provider_name in candidates:
                # Metabolik olarak en uygun olanı başa al
                candidates.remove(optimal_provider_name)
                candidates.insert(0, optimal_provider_name)
                logger.info(f"[SOVEREIGN-NAS] Metabolik optimal ({optimal_provider_name}) başa alındı, diğerleri sağlık puanına göre sıralandı.")
            else:
                logger.info(f"[SOVEREIGN-NAS] Sağlık puanına göre yeniden sıralama yapıldı: {candidates[:3]}...")
        except Exception as me:
            logger.warning(f"[METABOLISM-SYNC] Metabolik hata (Health-Fallback): {me}")
            # Fallback: Sadece sağlık puanına göre sırala
            candidates.sort(key=lambda p: self.providers.get(p).health_score if self.providers.get(p) else 0, reverse=True)
        
        # Eğer optimal bulunamadıysa (Hepsi devredeyse) orjinal listeyi dene
        if not candidates or (optimal_provider_name and optimal_provider_name not in candidates):
            # Fallback (Safety only)
             pass

        last_error = None
        skipped_details = []
        
        for provider_name in candidates:
            provider = self.providers.get(provider_name)
            
            if not provider:
                continue
                
            if not provider.api_key:
                skipped_details.append(f"{provider_name} (Key Yok)")
                continue

            if provider.is_placeholder_key():
                skipped_details.append(f"{provider_name} (Placeholder)")
                continue
                
            if not provider.is_available():
                skipped_details.append(f"{provider_name} (Circuit Open)")
                continue

            try:
                result = await self._call(provider, messages, max_tokens=2048, project_id=project_id, agent_role=agent_role)
                return result
                
            except Exception as e:
                last_error = e
                # Rate Limit (429) tespiti
                is_rate_limit = "429" in str(e) or "rate_limit" in str(e).lower()
                is_budget_error = "402" in str(e)
                
                if is_rate_limit:
                    logger.error(f"RATE LIMIT (429) hit on {provider.name}. Coordinated slowdown triggered.")
                    # Faz 43: Arbiter'ı uyar
                    from core.agi.operational.kinetic_arbiter import kinetic_arbiter
                    affective_core.adjust_state("rate_limit_429", magnitude=0.2)
                elif is_budget_error:
                    resource_manager.report_error(provider.name, 402)
                
                logger.warning(f"Sağlayıcı Hatası ({provider.name}): {str(e)}. Fallback modele geçiliyor.")
                err_summary = str(e)[:50]
                skipped_details.append(f"{provider.name} (Hata: {err_summary}...)")
                continue
                
        # Eğer tüm modeller başarısız olduysa veya atlandıysa açıklayıcı bir hata fırlat
        error_msg = f"Task {task_id} için tüm modeller başarısız oldu (Rol: {agent_role})."
        if skipped_details:
            error_msg += f" [Detaylar: {', '.join(skipped_details)}]"
        
        if last_error:
            error_msg += f" Son hata: {last_error}"
        else:
            error_msg += " Hiçbir geçerli sağlayıcı konfigüre edilmemiş veya erişilebilir değil."

        raise RuntimeError(error_msg)

    async def _call(self, provider: ProviderStats, messages: list[dict], max_tokens: int, project_id: str | None = None, agent_role: str = "general") -> LLMResponse:
        llm_timeout = float(os.getenv("LLM_TIMEOUT_S", "30"))
        t0 = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=llm_timeout) as client:
                if provider.name in ("openai", "groq", "openrouter"):
                    text = await self._call_openai(client, provider, messages, max_tokens)
                elif provider.name == "anthropic":
                    text = await self._call_anthropic(client, provider, messages, max_tokens)
                elif provider.name == "gemini":
                    text = await self._call_gemini(client, provider, messages, max_tokens)
                elif provider.name == "nvidia":
                    text = await self._call_nvidia(client, provider, messages, max_tokens)
                elif provider.name in ("moonshot", "deepseek"):
                    text = await self._call_openai(client, provider, messages, max_tokens)
                else:
                    raise ValueError(f"Bilinmeyen sağlayıcı: {provider.name}")
                    
            latency = time.time() - t0
            provider.record_success(latency)
            
            # Phase 88: Systemic Recovery signal
            affective_core.adjust_state("success", magnitude=0.05)

            # Yaklaşık token ve maliyet hesabı
            est_tokens = self._estimate_tokens(messages)
            out_tokens = self._estimate_output_tokens(text)
            est_cost   = self._estimate_cost(provider.name, est_tokens, out_tokens)

            # Metrics ve Maliyet Kaydı
            try:
                from observability.metrics import metrics
                from llm.cost_tracker import cost_tracker
                from db.session import AsyncSessionLocal

                # In-memory metrics
                metrics.record_llm_call(
                    provider=provider.name, latency_s=latency, success=True, tokens=est_tokens, cost_usd=est_cost
                )
                
                # In-memory Tracker & DB Persistence
                rec = cost_tracker.record(
                    provider=provider.name, model=provider.model, agent_id="orchestrator",
                    input_tokens=est_tokens, output_tokens=out_tokens, 
                    latency_s=latency, success=True, project_id=project_id,
                    agent_role=agent_role
                )
                
                # Arka planda DB'ye yaz (fire and forget tarzı ama await etmek daha güvenli)
                async with AsyncSessionLocal() as db:
                    await cost_tracker.persist(db, rec)
                    await db.commit()

            except Exception as e:
                logger.warning(f"Cost tracking error: {e}")

            # Zorunlu Canonical Sözleşme Çıktısı
            return LLMResponse(
                content=text,
                input_tokens=est_tokens,
                output_tokens=out_tokens,
                model_name=provider.model,
                provider=provider.name,
                latency_s=latency,
                cost_usd=est_cost
            )

        except Exception as _exc:
            provider.record_failure()
            try:
                from observability.metrics import metrics
                metrics.record_llm_call(provider=provider.name, latency_s=time.time() - t0, success=False)
                metrics.record_error(f"llm.{provider.name}.{type(_exc).__name__}")
                # Phase 88: Systemic Stress signal
                affective_core.adjust_state("error", magnitude=0.05)
            except ImportError:
                pass
            raise _exc

    # ── RAW HTTP İSTEKLERİ ──────────────────────────────────
    # ── Token / Cost Yardımcı Metodları ─────────────────────────
    def _estimate_tokens(self, messages: list[dict]) -> int:
        """Mesaj listesinin yaklaşık token sayısını tahmin et."""
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

    def _estimate_output_tokens(self, text: str) -> int:
        """Üretilen metnin yaklaşık token sayısını tahmin et."""
        return len(text) // 4

    def _estimate_cost(self, provider_name: str, input_tokens: int, output_tokens: int) -> float:
        """Token sayısından USD maliyet tahmini üret."""
        rate = _COST_PER_1K.get(provider_name, 0.0002)
        return round((input_tokens + output_tokens) / 1000 * rate, 6)

    async def _call_openai(self, client, p, messages, max_tokens) -> str:
        resp = await client.post(
            p.base_url,
            headers={"Authorization": f"Bearer {p.api_key}"},
            json={"model": p.model, "messages": messages, "max_tokens": max_tokens},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_nvidia(self, client, p, messages, max_tokens) -> str:
        # NVIDIA NIM API uses OpenAI format + optional thinking flag
        payload = {
            "model": p.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.60,
            "top_p": 0.95,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": True}
        }
        resp = await client.post(
            p.base_url,
            headers={"Authorization": f"Bearer {p.api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, client, p, messages, max_tokens) -> str:
        # Anthropic 'system' rolünü ayrı bir parametre olarak ister
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        usr_msgs = [m for m in messages if m["role"] != "system"]
        
        # Proxy & Model Overrides (Faz 45.1 Entegrasyonu)
        base_url   = os.getenv("ANTHROPIC_BASE_URL") or os.getenv("CLAUDE_PROXY_URL") or p.base_url
        auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
        model      = os.getenv("ANTHROPIC_MODEL") or p.model
        api_key    = p.api_key

        if base_url and not base_url.endswith("/messages"):
             if "/v1" not in base_url: base_url = base_url.rstrip("/") + "/v1/messages"
             else: base_url = base_url.rstrip("/") + "/messages"

        headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        # Eğer ANTHROPIC_AUTH_TOKEN varsa, Bearer token olarak kullanır (OpenRouter uyumlu)
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        else:
            headers["x-api-key"] = api_key

        resp = await client.post(
            base_url,
            headers=headers,
            json={"model": model, "max_tokens": max_tokens, "system": sys_msg, "messages": usr_msgs},
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    async def _call_gemini(self, client, p, messages, max_tokens) -> str:
        # Gemini 'system' mesajını contents'in başına veya systemInstruction'a koyar. 
        # Basitlik için tüm rolleri tek metin yapıyoruz.
        combined_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
        contents = [{"parts": [{"text": combined_text}]}]
        
        # Dinamik URL oluşturma
        api_version = "v1beta"
        url = f"{p.base_url.rstrip('/')}/{api_version}/models/{p.model}:generateContent"
        
        resp = await client.post(
            f"{url}?key={p.api_key}",
            json={"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}},
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

    async def complete(
        self,
        messages: list[dict],
        preferred_agent: str = "general",
        max_tokens: int = 2048,
        force_provider: str | None = None,
    ) -> str:
        """Basitleştirilmiş arayüz — orchestrator, recovery, reviewer çağırır.

        Faz 12: Dynamic Model Routing ile karmaşıklığa göre provider seçilir.
        complete_task() ile aynı altyapıyı kullanır, doğrudan string döner.
        """
        # force_provider varsa doğrudan o sağlayıcıyı dene
        if force_provider:
            provider = self.providers.get(force_provider)
            if provider and provider.api_key and provider.is_available():
                result = await self._call(provider, messages, max_tokens)
                return result.content

        # Faz 12: Dynamic routing — prompt karmaşıklığına göre provider seç
        try:
            from llm.model_router import get_model_router
            router   = get_model_router()
            prompt_text = " ".join(str(m.get("content", "")) for m in messages)
            decision = router.route(prompt_text, agent_role=preferred_agent)
            # force_provider üzerinden routing kararını uygula
            routed_provider = self.providers.get(decision.provider)
            if routed_provider and routed_provider.api_key and routed_provider.is_available():
                force_provider = decision.provider
                logger.debug(
                    f"Dynamic routing: {preferred_agent} -> {decision.provider}/{decision.model} "
                    f"[{decision.complexity.value}]"
                )
        except Exception:
            pass  # Routing hatası -> normal akış devam eder

        # Mesajlardan system/user prompt'ları ayıkla
        system_prompt = ""
        user_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
            elif m.get("role") == "user":
                user_prompt = m.get("content", "")

        if not user_prompt:
            user_prompt = str(messages)

        result = await self.complete_task(
            agent_role=preferred_agent,
            prompt=user_prompt,
            system_prompt=system_prompt or "Sen otonom bir sistem yöneticisisin.",
        )
        return result.content

    async def complete_vision(self, prompt: str, images: list[str] | str, preferred_provider: str = "gemini") -> str:
        """Analyze one or more images using a vision-capable model (Gemini or OpenAI)."""
        if isinstance(images, str):
            images = [images]
            
        provider = self.providers.get(preferred_provider)
        if not provider or not provider.api_key or not provider.is_available():
            # Fallback to gemini if preferred is not available
            provider = self.providers.get("gemini")
            if not provider or not provider.api_key:
                provider = self.providers.get("openai")
        
        if not provider or not provider.api_key:
            raise RuntimeError("Vision support requires Gemini or OpenAI API key.")

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if provider.name == "gemini":
                    # Gemini Vision format (Supports multiple parts)
                    parts = [{"text": prompt}]
                    for img in images:
                        parts.append({"inline_data": {"mime_type": "image/png", "data": img}})
                        
                    contents = [{"parts": parts}]
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{provider.model}:generateContent?key={provider.api_key}",
                        json={"contents": contents}
                    )
                    resp.raise_for_status()
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif provider.name == "openai":
                    # OpenAI Vision format
                    content_parts = [{"type": "text", "text": prompt}]
                    for img in images:
                        content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}})
                        
                    messages = [{"role": "user", "content": content_parts}]
                    resp = await client.post(
                        provider.base_url,
                        headers={"Authorization": f"Bearer {p.api_key}" if (p := provider) else ""},
                        json={"model": provider.model if "gpt-4o" in provider.model else "gpt-4o-mini", "messages": messages, "max_tokens": 1024}
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"]
                else:
                    raise ValueError(f"Vision not implemented for {provider.name}")
            
            latency = time.time() - t0
            provider.record_success(latency)
            affective_core.adjust_state("success", magnitude=0.1)
            return text
        except Exception as e:
            provider.record_failure()
            affective_core.adjust_state("error", magnitude=0.1)
            logger.error(f"Vision API call failed ({provider.name}): {e}")
            raise e

    def get_health_score(self) -> float:
        """Tüm sağlayıcıların genel sağlık puan ortalaması."""
        if not self.providers:
            return 1.0
        scores = [p.health_score for p in self.providers.values()]
        return sum(scores) / len(scores)

    def provider_stats(self) -> Dict[str, Any]:
        """Arayüzde (Dashboard) devre kesici durumunu göstermek için. (Faz 88 Observability)"""
        return {
            "metabolic_mode": metabolic_governor.get_mode(),
            "metabolic_score": metabolic_governor.get_score(),
            "providers": [
                {
                    "name":          p.name,
                    "health_score":  p.health_score,
                    "circuit":       p.circuit,
                    "quarantined":   p.quarantine_until > time.time(),
                    "success":       p.success,
                    "failure":       p.failure,
                    "avg_latency_s": p.avg_latency,
                }
                for p in self.providers.values()
            ]
        }

# --- Singleton ---
model_orchestrator = ModelOrchestrator()
