"""
Repair Benchmark Engine — Faz 11

Her repair job kapanınca metrik üretir.
Trend ve özet API'lere veri sağlar.

Ölçülen metrikler:
  - first_patch_success_rate
  - false_repair_rate
  - manual_review_rejection_rate
  - repeated_incident_rate
  - time_to_diagnose (triage -> root cause)
  - time_to_verified_patch (start -> verified)
  - create_pr_to_approved_ratio
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.observability.logging import get_logger

_log = get_logger("repair.services.repair.verification.metrics")


@dataclass
class RepairMetricRecord:
    metric_id:        str
    job_id:           str
    incident_id:      str
    incident_class:   str
    module:           str
    decision:         str        # "success" | "rejected" | "manual" | "failed"
    patch_size_lines: int        = 0
    confidence:       int        = 0
    time_to_diagnose_s:  float   = 0.0
    time_to_verified_s:  float   = 0.0
    duration_s:          float   = 0.0
    confidence:          int     = 0
    has_reproducer:   bool       = False
    canary_passed:    Optional[bool] = None
    feedback_code:    str        = ""
    recorded_at:      datetime   = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "metric_id":          self.metric_id,
            "job_id":             self.job_id,
            "incident_id":        self.incident_id,
            "incident_class":     self.incident_class,
            "module":             self.module,
            "decision":           self.decision,
            "patch_size_lines":   self.patch_size_lines,
            "confidence":         self.confidence,
            "time_to_diagnose_s": round(self.time_to_diagnose_s, 2),
            "time_to_verified_s": round(self.time_to_verified_s, 2),
            "duration_s":         round(self.duration_s, 2),
            "confidence":         self.confidence,
            "has_reproducer":     self.has_reproducer,
            "canary_passed":      self.canary_passed,
            "feedback_code":      self.feedback_code,
            "recorded_at":        self.recorded_at.isoformat(),
        }


class RepairMetricsStore:
    """
    In-memory metrik deposu.
    Özet ve trend hesaplama sağlar.
    """

    def __init__(self):
        self._records: list[RepairMetricRecord] = []

    def record(self, metric: RepairMetricRecord) -> None:
        self._records.append(metric)
        _log.debug(
            f"Metrik kaydedildi: job={metric.job_id} "
            f"decision={metric.decision} conf={metric.confidence}%"
        )

    # ── Özet metrikleri ──────────────────────────────────────

    def summary(self, last_days: int = 30) -> dict:
        """Dashboard özeti — in-memory."""
        from datetime import timedelta
        records = list(self._records)
        if not records: return self._empty_summary(last_days)
        cutoff  = datetime.now(timezone.utc) - timedelta(days=last_days)
        recent  = [r for r in records if getattr(r,'recorded_at',datetime.now(timezone.utc)) >= cutoff] or records
        total   = len(recent)
        if not total: return self._empty_summary(last_days)
        success  = sum(1 for r in recent if getattr(r,'decision','')=='success')
        rejected = sum(1 for r in recent if getattr(r,'decision','')=='rejected')
        failed   = sum(1 for r in recent if getattr(r,'decision','') in ('failed','rolled_back'))
        avg_conf = round(sum(getattr(r,'confidence',0) for r in recent)/total,1)
        avg_dur  = round(sum(getattr(r,'duration_s',0) for r in recent)/total,1)
        rejection_rate = round(rejected/total*100,1) if total else 0.0
        manual_count   = total - success - rejected - failed
        return {'period_days':last_days,'total_jobs':total,
                'success_count':success,'rejected_count':rejected,
                'failed_count':failed,'manual_count':manual_count,
                'success_rate':round(success/total*100,1) if total else 0.0,
                'rejection_rate':rejection_rate,
                'first_patch_success_rate':round(success/total*100,1) if total else 0.0,
                'manual_review_rate':round(manual_count/total*100,1) if total else 0.0,
                'avg_confidence':avg_conf,'avg_duration_s':avg_dur,'source':'in_memory'}

    def trends(self, last_days: int = 14, bucket_days: int = 2) -> list[dict]:
        """Bucket'lar halinde trend verisi döndür."""
        now    = datetime.now(timezone.utc)
        result = []
        for i in range(0, last_days, bucket_days):
            end   = now - timedelta(days=i)
            start = end - timedelta(days=bucket_days)
            bucket = [
                r for r in self._records
                if start <= r.recorded_at < end
            ]
            if bucket:
                total   = len(bucket)
                success = sum(1 for r in bucket if r.decision == "success")
                result.append({
                    "date":         start.strftime("%Y-%m-%d"),
                    "total":        total,
                    "success_rate": round(success / total * 100, 1),
                    "avg_conf":     round(sum(r.confidence for r in bucket) / total, 1),
                })
        result.reverse()
        return result

    def top_modules(self, top_n: int = 10) -> list:
        """En çok onarım modülleri — in-memory."""
        from collections import Counter
        counts = Counter(getattr(r,'module','unknown') for r in self._records)
        return [{'module':m,'count':n} for m,n in counts.most_common(top_n)]

    def _canary_rate(self, records: list[RepairMetricRecord]) -> Optional[float]:
        canary_records = [r for r in records if r.canary_passed is not None]
        if not canary_records:
            return None
        return round(
            sum(1 for r in canary_records if r.canary_passed) / len(canary_records) * 100, 1
        )

    def _empty_summary(self, last_days: int) -> dict:
        return {
            "period_days": last_days, "total_jobs": 0,
            "first_patch_success_rate": 0.0, "rejection_rate": 0.0, "manual_review_rate": 0.0, "manual_count": 0,
            "rejection_rate": 0.0, "failure_rate": 0.0,
            "avg_confidence": 0.0, "avg_time_to_diagnose_s": 0.0,
            "avg_time_to_verified_s": 0.0, "top_failing_modules": [],
            "rejection_reasons": {}, "reproducer_usage_rate": 0.0,
            "canary_pass_rate": None,
        }


def make_metric(
    job_id:        str,
    incident_id:   str,
    incident_class:str,
    module:        str,
    decision:      str,
    **kwargs,
) -> RepairMetricRecord:
    return RepairMetricRecord(
        metric_id=f"met_{uuid.uuid4().hex[:8]}",
        job_id=job_id,
        incident_id=incident_id,
        incident_class=incident_class,
        module=module,
        decision=decision,
        **kwargs,
    )


# Singleton
_metrics_store = RepairMetricsStore()


def get_metrics_store() -> RepairMetricsStore:
    return _metrics_store
