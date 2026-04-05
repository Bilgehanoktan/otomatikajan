"""
LLM maliyet takip sistemi.
Saf hesaplama cost_calc modülünden gelir; bu modül DB'siz de çalışır.
"""
from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from packages.llm_gateway.cost_calc import PRICING, calculate_cost, estimate_tokens, format_cost, cost_summary  # noqa: F401

MONTHLY_BUDGET_USD = float(os.getenv("MONTHLY_BUDGET_USD", "50.0"))


@dataclass
class CostRecord:
    provider: str
    model: str
    agent_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_s: float
    success: bool
    agent_role: str = "general"
    project_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CostTracker:
    def __init__(self):
        self._records: list[CostRecord] = []
        self._monthly_total = 0.0
        self._warned_budget = False

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        return calculate_cost(model, input_tokens, output_tokens)

    def record(self, provider: str, model: str, agent_id: str, input_tokens: int, output_tokens: int,
               latency_s: float, success: bool, project_id: str | None = None, agent_role: str = "general") -> CostRecord:
        rec = CostRecord(
            provider=provider,
            model=model,
            agent_id=agent_id,
            agent_role=agent_role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self.calculate_cost(model, input_tokens, output_tokens),
            latency_s=latency_s,
            success=success,
            project_id=project_id
        )
        self._records.append(rec)
        self._monthly_total += rec.cost_usd
        self._check_budget()
        return rec

    async def persist(self, db, rec: CostRecord):
        from packages.persistence.models import LLMCostLog, Project  # lazy
        from sqlalchemy import update
        
        # Log entry
        db.add(LLMCostLog(
            provider=rec.provider, model=rec.model, agent_id=rec.agent_id,
            agent_role=rec.agent_role,
            input_tokens=rec.input_tokens, output_tokens=rec.output_tokens,
            cost_usd=rec.cost_usd, latency_s=rec.latency_s, success=rec.success,
            project_id=rec.project_id
        ))
        
        # Update project total_cost if linked
        if rec.project_id and rec.success:
             await db.execute(
                 update(Project)
                 .where(Project.id == rec.project_id)
                 .values(total_cost=Project.total_cost + rec.cost_usd)
             )

    def _check_budget(self):
        ratio = self._monthly_total / MONTHLY_BUDGET_USD if MONTHLY_BUDGET_USD > 0 else 0.0
        if ratio >= 0.9 and not self._warned_budget:
            self._warned_budget = True
            print(f"🚨 BÜTÇE UYARISI: Aylık limitin %{ratio*100:.0f}'i kullanıldı (${self._monthly_total:.4f} / ${MONTHLY_BUDGET_USD})")
        if ratio >= 1.0:
            print(f"💸 BÜTÇE AŞILDI: ${self._monthly_total:.4f} / ${MONTHLY_BUDGET_USD}")

    def summary(self) -> dict:
        if not self._records:
            return {
                'total_cost_usd': 0.0,
                'budget_usd': MONTHLY_BUDGET_USD,
                'budget_used_pct': 0.0,
                'total_calls': 0,
                'success_rate': 0.0,
                'avg_latency_s': 0.0,
                'by_provider': {},
                'by_agent': {},
                'by_model': {},
            }
        by_provider = defaultdict(lambda: {'calls': 0, 'cost': 0.0, 'tokens': 0})
        by_agent = defaultdict(lambda: {'calls': 0, 'cost': 0.0})
        by_model = defaultdict(lambda: {'calls': 0, 'cost': 0.0, 'tokens': 0})
        for r in self._records:
            by_provider[r.provider]['calls'] += 1
            by_provider[r.provider]['cost'] += r.cost_usd
            by_provider[r.provider]['tokens'] += r.input_tokens + r.output_tokens
            by_agent[r.agent_id]['calls'] += 1
            by_agent[r.agent_id]['cost'] += r.cost_usd
            by_model[r.model]['calls'] += 1
            by_model[r.model]['cost'] += r.cost_usd
            by_model[r.model]['tokens'] += r.input_tokens + r.output_tokens
        return {
            'total_cost_usd': round(self._monthly_total, 6),
            'budget_usd': MONTHLY_BUDGET_USD,
            'budget_used_pct': round(self._monthly_total / MONTHLY_BUDGET_USD * 100, 1) if MONTHLY_BUDGET_USD > 0 else 0.0,
            'total_calls': len(self._records),
            'success_rate': round(sum(1 for r in self._records if r.success) / len(self._records), 3),
            'avg_latency_s': round(sum(r.latency_s for r in self._records) / len(self._records), 3),
            'by_provider': {k: {**v, 'cost': round(v['cost'], 6)} for k, v in by_provider.items()},
            'by_agent': {k: {**v, 'cost': round(v['cost'], 6)} for k, v in by_agent.items()},
            'by_model': {k: {**v, 'cost': round(v['cost'], 6)} for k, v in by_model.items()},
        }

    def recent(self, n: int = 20) -> list[dict]:
        return [
            {
                'provider': r.provider,
                'model': r.model,
                'agent_id': r.agent_id,
                'cost_usd': round(r.cost_usd, 6),
                'latency_s': round(r.latency_s, 3),
                'tokens': r.input_tokens + r.output_tokens,
                'success': r.success,
                'timestamp': r.timestamp.isoformat(),
            }
            for r in self._records[-n:]
        ]


cost_tracker = CostTracker()
