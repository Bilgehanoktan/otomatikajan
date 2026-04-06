"""
Test Synthesis Engine — Faz 11

Bug'a özel minimal reproducer test üretir.
Patch ile birlikte test diff önerir.

Girdi:  IncidentRecord + PatchPlan + DiagnosisTicket
Çıktı:  GeneratedTest (test kodu + dosya yolu)
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from packages.repair_engine.schemas.incident import IncidentRecord
from packages.repair_engine.schemas.patch_plan import PatchPlan
from packages.repair_engine.schemas.diagnosis import DiagnosisTicket, ProblemClass
from packages.observability.logging import get_logger

_log = get_logger("repair.generation.test_generator")


@dataclass
class GeneratedTest:
    test_id:        str
    job_id:         str
    test_code:      str
    target_file:    str       # tests/ altına önerilen dosya yolu
    test_type:      str       # "unit" | "api" | "smoke" | "regression"
    description:    str
    fixture_hints:  list[str] = field(default_factory=list)
    generated_at:   datetime  = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "test_id":       self.test_id,
            "job_id":        self.job_id,
            "test_code":     self.test_code,
            "target_file":   self.target_file,
            "test_type":     self.test_type,
            "description":   self.description,
            "fixture_hints": self.fixture_hints,
        }


# ── Şablon havuzu ─────────────────────────────────────────────

def _unit_test_template(module: str, symptom: str, target_symbol: str) -> str:
    safe_sym = re.sub(r"[^a-zA-Z0-9_]", "_", target_symbol or "function")
    return f'''"""
Otomatik üretilmiş regression testi — {module}
Semptom: {symptom[:80]}
"""
import pytest


def test_{safe_sym}_regression():
    """
    Bu test, {module} modülündeki hatanın tekrarını engeller.
    Patch öncesi bu test FAIL etmeli, patch sonrası PASS etmeli.
    """
    # TODO: Aşağıdaki import ve assertion'ları gerçek kodla doldurun
    try:
        from {module.replace("/", ".").replace(".py", "")} import {safe_sym}
    except ImportError as e:
        pytest.skip(f"Modül import edilemedi: {{e}}")

    # Hatayı tetikleyen senaryo
    # result = {safe_sym}(...)
    # assert result is not None, "Beklenen sonuç None olmamalı"
    pytest.skip("Test gövdesi tamamlanmamış — lütfen doldurun")
'''


def _api_test_template(module: str, symptom: str, route: str) -> str:
    safe_route = re.sub(r"[^a-zA-Z0-9_]", "_", route)
    return f'''"""
Otomatik üretilmiş API regression testi — {route}
Semptom: {symptom[:80]}
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_{safe_route}_regression(client: AsyncClient):
    """
    {route} endpoint'inin hatalı senaryosu.
    Patch öncesi hata dönmeli, patch sonrası başarılı yanıt.
    """
    # Hatayı tetikleyen istek
    response = await client.get("{route}")

    # Beklenen: 200 veya uygun hata kodu
    assert response.status_code != 500, (
        f"Internal Server Error — repair patch uygulanmadı mı? "
        f"Response: {{response.text[:200]}}"
    )
'''


def _smoke_test_template(module: str) -> str:
    return f'''"""
Otomatik üretilmiş smoke testi — {module}
"""
import pytest


def test_{re.sub(r"[^a-zA-Z0-9_]", "_", module)}_smoke():
    """Modül import edilebiliyor mu?"""
    try:
        import importlib
        importlib.import_module("{module.replace("/", ".").replace(".py", "")}")
    except ImportError as e:
        pytest.fail(f"Smoke test başarısız — {module} import edilemiyor: {{e}}")
'''


# ── Test Generator ────────────────────────────────────────────

class TestGenerator:
    """
    Incident + PatchPlan kombinasyonundan minimal test üretir.
    Üretilen test:
      1. Patch öncesi FAIL etmeli
      2. Patch sonrası PASS etmeli
    """

    def generate(
        self,
        incident:  IncidentRecord,
        plan:      PatchPlan,
        ticket:    Optional[DiagnosisTicket] = None,
        job_id:    str = "",
    ) -> GeneratedTest:
        cls      = ticket.classification if ticket else None
        module   = incident.module
        symptom  = incident.symptom
        files    = plan.target_files[:2]

        # Önce test tipine karar ver
        if cls in (ProblemClass.ROUTE_ERROR,) or _is_api_incident(symptom):
            route = _extract_route(symptom, incident.stack_trace)
            code  = _api_test_template(module, symptom, route)
            ttype = "api"
            fname = f"test_repair_{re.sub(r'[^a-z0-9]', '_', module)}_regression.py"
        elif cls in (ProblemClass.IMPORT_ERROR,):
            code  = _smoke_test_template(module)
            ttype = "smoke"
            fname = f"test_repair_{re.sub(r'[^a-z0-9]', '_', module)}_smoke.py"
        else:
            symbol = _extract_symbol(incident.stack_trace, files)
            code   = _unit_test_template(module, symptom, symbol)
            ttype  = "unit"
            fname  = f"test_repair_{re.sub(r'[^a-z0-9]', '_', module)}_unit.py"

        target_file = f"tests/{fname}"
        fixtures    = _suggest_fixtures(cls, module)

        _log.info(f"Test üretildi: {ttype} -> {target_file} (job={job_id})")

        return GeneratedTest(
            test_id    = f"tgen_{uuid.uuid4().hex[:8]}",
            job_id     = job_id,
            test_code  = code,
            target_file= target_file,
            test_type  = ttype,
            description= f"{ttype.upper()} regression test — {module}: {symptom[:60]}",
            fixture_hints = fixtures,
        )


def _is_api_incident(symptom: str) -> bool:
    return any(x in symptom for x in ["404", "405", "422", "500", "/api/", "endpoint", "route"])


def _extract_route(symptom: str, stack: str) -> str:
    m = re.search(r"(/api/[^\s\"']+)", symptom + " " + stack)
    return m.group(1) if m else "/api/unknown"


def _extract_symbol(stack: str, files: list[str]) -> str:
    m = re.search(r"in (\w+)\n", stack)
    return m.group(1) if m else "target_function"


def _suggest_fixtures(cls: Optional[ProblemClass], module: str) -> list[str]:
    hints = []
    if cls == ProblemClass.ROUTE_ERROR:
        hints += ["AsyncClient (httpx)", "TestApp (FastAPI)"]
    if cls == ProblemClass.AUTH_FAILURE:
        hints += ["auth_token fixture", "mock_user fixture"]
    if "db" in module or "repository" in module:
        hints += ["async_db_session fixture"]
    return hints


# Singleton
_generator = TestGenerator()


def get_test_generator() -> TestGenerator:
    return _generator
