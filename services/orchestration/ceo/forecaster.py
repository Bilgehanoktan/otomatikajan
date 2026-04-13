import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
try:
    from sqlalchemy import select, func, desc
except ImportError:
    pass
from libs.db.session import session_scope
from libs.db.models import LLMCostLog, Project, TaskLog, ApiMetric
from services.observability.logging import get_logger

logger = get_logger("ceo.forecaster")

class CEOForecaster:
    """
    CEO için stratejik tahminleme ve anomali tespit motoru.
    Geçmiş verileri analiz ederek gelecek riskleri öngörür.
    """

    @staticmethod
    async def predict_budget_burn(days: int = 7) -> Dict[str, Any]:
        """
        Son 7 günlük harcama trendine bakarak gelecek tahmini yapar.
        """
        async with session_scope() as db:
            # Son 7 günün günlük maliyetlerini al
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            stmt = select(
                func.date(LLMCostLog.created_at).label("day"),
                func.sum(LLMCostLog.cost_usd).label("daily_cost")
            ).where(
                LLMCostLog.created_at >= start_date
            ).group_by(
                func.date(LLMCostLog.created_at)
            ).order_by("day")
            
            res = await db.execute(stmt)
            history = res.all()
            
            if not history:
                return {"trend": "neutral", "predicted_burn": 0, "confidence": 0}

            costs = [float(h.daily_cost) for h in history]
            avg_daily = sum(costs) / len(costs)
            
            # Basit lineer eğilim (son gün vs ortalama)
            last_day_cost = costs[-1]
            trend = "increasing" if last_day_cost > avg_daily * 1.1 else "stable"
            if last_day_cost < avg_daily * 0.9: trend = "decreasing"
            
            prediction = avg_daily * days
            
            return {
                "avg_daily_burn": round(avg_daily, 4),
                "predicted_7d_burn": round(prediction, 4),
                "trend": trend,
                "confidence": 0.7 if len(history) > 3 else 0.4
            }

    @staticmethod
    async def detect_anomalies() -> List[Dict[str, Any]]:
        """
        Hata oranlarında veya işlem hacminde ani sapmaları tespit eder.
        """
        anomalies = []
        async with session_scope() as db:
            # Son 1 saatteki hata sayısı vs son 24 saat ortalaması
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(days=1)
            
            # 1. Hata Artış Analizi
            err_count_1h = await db.execute(select(func.count(TaskLog.id)).where(TaskLog.level == "ERROR", TaskLog.created_at >= one_hour_ago))
            err_1h = err_count_1h.scalar() or 0
            
            err_count_24h = await db.execute(select(func.count(TaskLog.id)).where(TaskLog.level == "ERROR", TaskLog.created_at >= one_day_ago))
            avg_err_per_hour = (err_count_24h.scalar() or 0) / 24
            
            if err_1h > avg_err_per_hour * 3 and err_1h > 5:
                anomalies.append({
                    "type": "error_surge",
                    "severity": "high",
                    "message": f"Hata oranında anormal artış: Son 1 saatte {err_1h} hata (Normal: {avg_err_per_hour:.1f}/saat)",
                    "growth_factor": round(err_1h / (avg_err_per_hour or 1), 1)
                })

            # 2. İş Kuyruğu Şişme Analizi
            queued_count = await db.execute(select(func.count(Project.id)).where(Project.status == "queued"))
            q_size = queued_count.scalar() or 0
            if q_size > 15:
                anomalies.append({
                    "type": "queue_backlog",
                    "severity": "medium",
                    "message": f"İş kuyruğu şişiyor: {q_size} bekleyen görev var.",
                    "value": q_size
                })
            
            # 3. Gecikme (Latency) Analizi
            latency_anomalies = await CEOForecaster.detect_latency_spikes()
            anomalies.extend(latency_anomalies)

            # 4. Operasyonel Sapma (Drift) Analizi - FAZ 12.1
            drift_anomalies = await CEOForecaster.detect_operational_drift()
            anomalies.extend(drift_anomalies)
                
        return anomalies

    @staticmethod
    async def detect_latency_spikes() -> List[Dict[str, Any]]:
        """
        API uç noktalarındaki gecikme (latency) artışlarını tespit eder.
        """
        anomalies = []
        async with session_scope() as db:
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            
            # Son 1 saat içindeki endpoint bazlı ortalama gecikme
            stmt = select(
                ApiMetric.endpoint,
                func.avg(ApiMetric.response_ms).label("avg_latency")
            ).where(
                ApiMetric.created_at >= one_hour_ago
            ).group_by(ApiMetric.endpoint)
            
            try:
                res = await db.execute(stmt)
                for row in res.all():
                    if row.avg_latency > 3000: # 3 saniye barajı (Faz 12 standardı)
                        anomalies.append({
                            "type": "latency_spike",
                            "severity": "medium",
                            "message": f"Performans Düşüşü: {row.endpoint} ({row.avg_latency:.0f}ms)",
                            "endpoint": row.endpoint,
                            "value": row.avg_latency
                        })
            except Exception as e:
                logger.warning(f"Latency detection failed: {e}")
                
        return anomalies

    @staticmethod
    async def detect_operational_drift() -> List[Dict[str, Any]]:
        """
        Kısa vadeli metrikleri uzun vadeli baseline ile karşılaştırarak 
        sinsi performans düşüşlerini (drift) tespit eder.
        """
        anomalies = []
        async with session_scope() as db:
            now = datetime.now(timezone.utc)
            # Baseline: Son 48 saat, Current: Son 4 saat
            baseline_start = now - timedelta(hours=48)
            current_start = now - timedelta(hours=4)
            
            try:
                # Baseline Gecikme
                stmt_base = select(func.avg(ApiMetric.response_ms)).where(ApiMetric.created_at.between(baseline_start, current_start))
                res_base = await db.execute(stmt_base)
                base_latency = res_base.scalar() or 500 # Default fallback
                
                # Current Gecikme
                stmt_curr = select(func.avg(ApiMetric.response_ms)).where(ApiMetric.created_at >= current_start)
                res_curr = await db.execute(stmt_curr)
                curr_latency = res_curr.scalar() or 500
                
                if curr_latency > base_latency * 1.3: # %30 sapma
                    anomalies.append({
                        "type": "operational_drift",
                        "severity": "medium",
                        "message": f"Sistem Gecikmesinde Drift: %{((curr_latency/base_latency)-1)*100:.1f} artış (Current: {curr_latency:.0f}ms, Baseline: {base_latency:.0f}ms)",
                        "drift_factor": round(curr_latency / base_latency, 2)
                    })
            except Exception as e:
                logger.warning(f"Drift detection failed: {e}")
        return anomalies

    @staticmethod
    async def calculate_agent_roi() -> List[Dict[str, Any]]:
        """
        Ajanların başarı oranı / maliyet rasyosunu hesaplar.
        """
        roi_data = []
        async with session_scope() as db:
            from libs.db.models import CEOPerformanceLog
            # Ajan bazlı başarıları ve toplam maliyetleri birleştir
            stmt = select(
                LLMCostLog.agent_id,
                func.sum(LLMCostLog.cost_usd).label("total_cost"),
                func.count(LLMCostLog.id).label("total_calls")
            ).group_by(LLMCostLog.agent_id)
            
            res = await db.execute(stmt)
            for row in res.all():
                # ROI = SuccessCount / TotalCost (Basitleştirilmiş)
                roi_data.append({
                    "agent_id": row.agent_id,
                    "total_cost": float(row.total_cost),
                    "efficiency": round(float(row.total_calls) / (float(row.total_cost) or 0.001), 2)
                })
        return roi_data

    @staticmethod
    async def audit_token_efficiency() -> List[Dict[str, Any]]:
        """
        Aşırı token tüketen 'chatty' ajanları tespit eder.
        """
        findings = []
        async with session_scope() as db:
            stmt = select(
                LLMCostLog.agent_id,
                func.avg(LLMCostLog.output_tokens).label("avg_output")
            ).group_by(LLMCostLog.agent_id).having(func.avg(LLMCostLog.output_tokens) > 1500)
            
            res = await db.execute(stmt)
            row_results = res.all()
            for row in row_results:
                findings.append({
                    "type": "token_inefficiency",
                    "severity": "low",
                    "message": f"Ajan '{row.agent_id}' yüksek ortalama token tüketiyor ({row.avg_output:.0f} tokens/request)",
                    "agent_id": row.agent_id
                })
        return findings


    @classmethod
    async def get_strategic_outlook(cls) -> Dict[str, Any]:
        """
        CEO Dashboard için kapsamlı stratejik görünüm üretir.
        """
        budget = await cls.predict_budget_burn()
        anomalies = await cls.detect_anomalies()
        
        # Risk Skoru Hesaplama (0-100)
        risk_score = 10
        if budget["trend"] == "increasing": risk_score += 20
        risk_score += (len(anomalies) * 15)
        
        return {
            "budget_forecast": budget,
            "detected_anomalies": anomalies,
            "risk_score": min(risk_score, 100),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
