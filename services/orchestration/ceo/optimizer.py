import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, update, delete, func, cast, Integer
from libs.db.session import session_scope
from libs.db.models import LLMCostLog, SovereignModelPolicy, ModelBenchmarking
from services.observability.logging import get_logger

logger = get_logger("ceo.optimizer")

class CEOStochasticOptimizer:
    """
    Sovereign Neural Architecture Search (NAS) & Model Policy Optimizer.
    Synchronizes high-performance models with agent roles based on latency/failure telemetry.
    """

    @staticmethod
    async def run_optimization_cycle():
        """
        Main entry point for optimizing model policies based on recent data.
        """
        logger.info("👔 CEO Optimizer: NAS Optimization Cycle started.")
        
        async with session_scope() as db:
            # 1. Performance-Based Winner Selection (Benchmarking Update)
            await CEOStochasticOptimizer._update_benchmarks(db)
            
            # 2. ROI-Based Optimization
            await CEOStochasticOptimizer._optimize_by_roi(db)
            
            # 3. Latency-Based Demotion (Policy Update)
            await CEOStochasticOptimizer._handle_latency_regressions(db)

    @staticmethod
    async def calculate_roi(db, agent_role: str) -> Dict[str, float]:
        """
        Calculates ROI (Cost per successful completion) for each provider in a given role.
        """
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        
        stmt = select(
            LLMCostLog.provider,
            func.sum(LLMCostLog.cost_usd).label("total_cost"),
            func.sum(cast(LLMCostLog.success, Integer)).label("total_success")
        ).where(
            LLMCostLog.agent_role == agent_role,
            LLMCostLog.created_at >= seven_days_ago
        ).group_by(LLMCostLog.provider)
        
        results = await db.execute(stmt)
        roi_map = {}
        for row in results.all():
            if row.total_success > 0:
                cost_per_success = row.total_cost / row.total_success
                roi_map[row.provider] = cost_per_success
            else:
                roi_map[row.provider] = float('inf') # Hiç başarısı yoksa maliyeti sonsuz say
        
        return roi_map

    @staticmethod
    async def _optimize_by_roi(db):
        """
        Gelişmiş ROI Karşılaştırması: Aynı rol için farklı sağlayıcıları kıyaslar
        ve verimlilik farkı (Efficiency Factor) %30'u aşarsa otomatik pivot yapar.
        """
        # Aktif rolleri bul
        roles_stmt = select(SovereignModelPolicy.agent_role)
        res_roles = await db.execute(roles_stmt)
        roles = res_roles.scalars().all()
        
        for role in roles:
            roi_map = await CEOStochasticOptimizer.calculate_roi(db, role)
            if not roi_map or len(roi_map) < 2: continue # Kıyaslanacak rakip yoksa geç
            
            # ROI = Cost Per Success. Düşük olan iyidir.
            sorted_providers = sorted(roi_map.items(), key=lambda x: x[1])
            best_provider, best_roi = sorted_providers[0]
            
            # Mevcut politikayı al
            policy_stmt = select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == role)
            res_policy = await db.execute(policy_stmt)
            policy = res_policy.scalars().first()
            
            if policy:
                current_winner = policy.winner_provider
                current_roi = roi_map.get(current_winner, 999.0)
                
                # EFFICIENCY FACTOR: Mevcut ROI / En iyi ROI
                efficiency_factor = current_roi / (best_roi or 0.0001)
                
                if efficiency_factor > 1.3: # %30'dan fazla verimsizlik varsa!
                    logger.important(f"👔 CEO NAS: Efficient Provider Detected for '{role}'!")
                    logger.info(f"   Current: {current_winner} (${current_roi:.4f}) -> Better: {best_provider} (${best_roi:.4f})")
                    
                    # Runner-up'ı güncelle ve kazananı değiştir
                    policy.runner_up = current_winner
                    policy.winner_provider = best_provider
                    
                    # Kararı logla
                    from libs.db.models import CEODecision
                    from datetime import datetime, timezone
                    import uuid
                    decision = CEODecision(
                        id=str(uuid.uuid4()),
                        decision_type="MODEL_ROI_PIVOT",
                        summary=f"Switched {role} to {best_provider} due to {efficiency_factor:.1f}x better ROI.",
                        context={"role": role, "old": current_winner, "new": best_provider, "eff_factor": efficiency_factor},
                        applied_at=datetime.now(timezone.utc)
                    )
                    db.add(decision)

    @staticmethod
    async def _update_benchmarks(db):
        """
        LLMCostLog verilerini kullanarak ModelBenchmarking tablosunu günceller.
        """
        # Son 24 saatlik verileri özetle
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        
        stmt = select(
            LLMCostLog.agent_role,
            LLMCostLog.provider,
            func.avg(LLMCostLog.latency_s).label("avg_latency"),
            func.avg(LLMCostLog.cost_usd).label("avg_cost"),
            func.avg(cast(LLMCostLog.success, Integer)).label("success_rate")
        ).where(
            LLMCostLog.created_at >= yesterday,
            LLMCostLog.agent_role != None
        ).group_by(LLMCostLog.agent_role, LLMCostLog.provider)
        
        results = await db.execute(stmt)
        
        for row in results.all():
            # Update or create benchmark
            bench_stmt = select(ModelBenchmarking).where(
                ModelBenchmarking.agent_role == row.agent_role,
                ModelBenchmarking.provider == row.provider
            )
            res_bench = await db.execute(bench_stmt)
            bench = res_bench.scalars().first()
            
            if not bench:
                bench = ModelBenchmarking(agent_role=row.agent_role, provider=row.provider)
                db.add(bench)
            
            bench.avg_latency = row.avg_latency
            bench.avg_cost = row.avg_cost
            bench.success_rate = row.success_rate
            bench.recorded_at = now
            
        await db.commit()

    @staticmethod
    async def _handle_latency_regressions(db):
        """
        Gecikmesi artan modelleri tespit edip politikada alt sıralara iter.
        """
        # Gecikme limiti: 4.0 saniye
        LATENCY_THRESHOLD = 4.0 
        
        stmt = select(ModelBenchmarking).where(ModelBenchmarking.avg_latency > LATENCY_THRESHOLD)
        res = await db.execute(stmt)
        slow_models = res.scalars().all()
        
        for model in slow_models:
            policy_stmt = select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == model.agent_role)
            res_policy = await db.execute(policy_stmt)
            policy = res_policy.scalars().first()
            
            if policy and policy.winner_provider == model.provider:
                logger.warning(f"👔 CEO Optimizer: '{model.provider}' for role '{model.agent_role}' is too slow ({model.avg_latency:.2f}s). Demoting.")
                
                if policy.runner_up:
                    old_winner = policy.winner_provider
                    policy.winner_provider = policy.runner_up
                    policy.runner_up = old_winner
                    
                    if old_winner in policy.fallback_chain:
                        chain = list(policy.fallback_chain)
                        chain.remove(old_winner)
                        chain.append(old_winner)
                        policy.fallback_chain = chain
                        
        await db.commit()

    @staticmethod
    async def report_latency_anomaly(provider: str, model: str, latency_s: float, agent_role: str = "all"):
        """
        Emergency reporting of a slow request. If extreme, triggers immediate policy pivot.
        """
        if latency_s > 10.0: # Kritik eşik: 10 saniye
            logger.warning(f"🚨 CEO Optimizer: CRITICAL LATENCY on '{provider}' ({latency_s:.1f}s). Emergency pivoting role '{agent_role}'.")
            async with session_scope() as db:
                policy_stmt = select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == agent_role)
                res_policy = await db.execute(policy_stmt)
                policy = res_policy.scalars().first()
                
                if policy and policy.winner_provider == provider:
                    # Hızlı pivot: Runner-up ile yer değiştir
                    if policy.runner_up:
                        old_winner = policy.winner_provider
                        policy.winner_provider = policy.runner_up
                        policy.runner_up = old_winner
                        logger.info(f"👔 CEO Optimizer: Emergency pivot complete. New winner: {policy.winner_provider}")

    @staticmethod
    async def get_active_policies() -> Dict[str, Dict[str, Any]]:
        """
        Returns a map of agent_role -> policy details for the ModelOrchestrator.
        """
        async with session_scope() as db:
            stmt = select(SovereignModelPolicy)
            res = await db.execute(stmt)
            policies = res.scalars().all()
            
            return {
                p.agent_role: {
                    "winner": p.winner_provider,
                    "runner_up": p.runner_up,
                    "fallback_chain": p.fallback_chain
                } for p in policies
            }
