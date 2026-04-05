import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, update
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models import LLMCostLog, SubTask, SovereignModelPolicy, ModelBenchmarking
from packages.llm_gateway.model_orchestrator import ROUTING_POLICY

logger = logging.getLogger(__name__)

class NASOptimizer:
    """
    Neural Architecture Search (NAS) Optimizer.
    Otonom olarak en iyi LLM+Rol kombinasyonunu seçer.
    """

    def __init__(self, check_interval_m: int = 60):
        self.check_interval_m = check_interval_m
        self._is_running = False

    async def start(self):
        if self._is_running: return
        self._is_running = True
        asyncio.create_task(self._loop())
        logger.info(f"NASOptimizer: Başlatıldı (Interval: {self.check_interval_m}dk)")

    async def _loop(self):
        while self._is_running:
            try:
                await self.optimize_all_roles()
            except Exception as e:
                logger.error(f"NASOptimizer Hatası: {e}")
            await asyncio.sleep(self.check_interval_m * 60)

    async def optimize_all_roles(self):
        """Tüm ajan rolleri için en iyi modelleri belirle."""
        roles = list(ROUTING_POLICY.keys())
        async with AsyncSessionLocal() as db:
            for role in roles:
                await self.optimize_role(db, role)
            await db.commit()
        logger.info("NASOptimizer: Tüm roller optimize edildi.")

    async def optimize_role(self, db, role: str):
        """Spesifik bir rol için performans analizi yap."""
        # 1. Son 24 saatlik LLM loglarını getir
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Provider bazlı istatistikleri topla
        # Not: SubTask tablosuyla join yaparak quality_score'u alıyoruz
        query = (
            select(
                LLMCostLog.provider,
                func.count(LLMCostLog.id).label("total"),
                func.avg(LLMCostLog.latency_s).label("avg_lat"),
                func.avg(LLMCostLog.cost_usd).label("avg_cost"),
                func.sum(LLMCostLog.success.cast(int)).label("success_count")
            )
            .where(LLMCostLog.agent_role == role)
            .where(LLMCostLog.created_at >= cutoff)
            .group_by(LLMCostLog.provider)
        )
        
        result = await db.execute(query)
        stats = result.all()
        
        if not stats: return # Veri yoksa statik politikaya güven
        
        scores = []
        for s in stats:
            provider, total, avg_lat, avg_cost, success_count = s
            success_rate = success_count / total if total > 0 else 0
            
            # Phase 60 Quality Score'u SubTask üzerinden al (Basitleştirilmiş)
            # Not: Gerçek senaryoda bu roldeki son başarılı subtask'lerin ortalamasıdır
            quality_score = 1.0 # Default
            q_query = select(func.avg(SubTask.quality_score)).where(SubTask.agent_id == role).where(SubTask.llm_provider == provider)
            q_res = await db.execute(q_query)
            q_val = q_res.scalar()
            if q_val: quality_score = float(q_val)

            # PerformanceIndex = (Quality^2 * Success) / (Latency * Cost)
            # Normalize maliyet (0'a bölünmeyi engelle)
            safe_cost = max(avg_cost, 0.00001)
            safe_lat  = max(avg_lat, 0.1)
            
            p_index = ( (quality_score ** 2) * success_rate ) / (safe_lat * (safe_cost * 1000))
            scores.append({
                "provider": provider,
                "score": p_index,
                "latency": avg_lat,
                "quality": quality_score
            })

        # Skora göre sırala
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        # 2. Politikayı Güncelle (SovereignModelPolicy)
        winner = scores[0]["provider"]
        runner = scores[1]["provider"] if len(scores) > 1 else winner
        chain = [s["provider"] for s in scores] # Tüm zinciri skor sırasına koy
        
        # Mevcut politikayı bul veya oluştur
        p_query = select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == role)
        p_res = await db.execute(p_query)
        policy = p_res.scalar_one_or_none()
        
        if policy:
            policy.winner_provider = winner
            policy.runner_up = runner
            policy.fallback_chain = chain
            policy.last_optimized = datetime.now(timezone.utc)
            policy.confidence = min(1.0, scores[0]["score"] / 2.0) # Basit güven skoru
        else:
            policy = SovereignModelPolicy(
                agent_role=role,
                winner_provider=winner,
                runner_up=runner,
                fallback_chain=chain,
                confidence=0.5
            )
            db.add(policy)

        # 3. ModelBenchmarking kaydını güncelle
        # ... (NAS analizi için trend verisi ekle)

    async def get_active_policy(self, role: str) -> list[str] | None:
        """Orchestrator tarafından çağrılır; optimize edilmiş zinciri döner."""
        async with AsyncSessionLocal() as db:
            query = select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == role)
            result = await db.execute(query)
            policy = result.scalar_one_or_none()
            if policy:
                return policy.fallback_chain
        return None

nas_optimizer = NASOptimizer()
