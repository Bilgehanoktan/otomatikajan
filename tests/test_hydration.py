import pytest
import asyncio
from datetime import datetime, timezone
import uuid

# Proje Yolları Config
from repair.memory.incident_memory import incident_memory
from repair.ingestion.incident_ingestor import incident_ingestor
from core.repair_orchestrator import get_repair_orchestrator
from db.session import AsyncSessionLocal
from db.repair_repository import RepairIncidentRepo, RepairJobRepo
from db.repair_models import RepairIncident, RepairJobRecord

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def cleanup_memory():
    """Her testten önce ve sonra memory/ingestor temizliği"""
    incident_memory._incidents.clear()
    incident_ingestor._seen.clear()
    orch = get_repair_orchestrator()
    orch._jobs_cache.clear()
    orch._hydrated = False
    yield
    incident_memory._incidents.clear()
    incident_ingestor._seen.clear()
    orch._jobs_cache.clear()
    orch._hydrated = False

async def test_incident_memory_hydration():
    """Test: IncidentMemory veritabanındaki açık kayıtları belleğe alıyor mu?"""
    # 1. DB'ye sahte (mock) veri yazalım (Gerçek test DB ortamı varsayımı)
    test_incident_id = f"inc_test_{uuid.uuid4().hex[:8]}"
    
    async with AsyncSessionLocal() as db:
        new_record = RepairIncident(
            incident_id=test_incident_id,
            source="test_failure",
            severity="high",
            service="test_service",
            module="test_module",
            symptom="Mock error for hydration finding",
            status="open",
            first_seen_at=datetime.now(timezone.utc)
        )
        db.add(new_record)
        await db.commit()
        
    # 2. Hydration Metodunu Çağır
    count = await incident_memory.hydrate_from_db()
    
    # 3. İddia (Assertion)
    assert count > 0, "Hydration en az 1 kayıt yüklemeli"
    assert test_incident_id in incident_memory._incidents, "Eklenen test kaydı hafızaya gelmeli"
    
    incident = incident_memory._incidents[test_incident_id]
    assert incident.symptom == "Mock error for hydration finding"
    assert incident.status == "open"

async def test_repair_orchestrator_hydration():
    """Test: RepairOrchestrator veritabanındaki işleri listelerken schema sorunu çıkartıyor mu?"""
    # 1. DB'ye örnek onarım işi ekle
    test_incident_id = f"inc_test_{uuid.uuid4().hex[:8]}"
    test_job_id = f"rjob_test_{uuid.uuid4().hex[:8]}"
    
    async with AsyncSessionLocal() as db:
        new_inc = RepairIncident(
            incident_id=test_incident_id,
            source="test_failure", severity="high", service="test_service",
            module="test_module", symptom="Test", status="open",
            first_seen_at=datetime.now(timezone.utc)
        )
        db.add(new_inc)
        
        new_job = RepairJobRecord(
            job_id=test_job_id,
            incident_id=test_incident_id,
            status="new",
            history=[],
            meta={"risk_score": 10, "test_field": True},  # Alembic revizyon 0008 meta alanı!
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_job)
        await db.commit()
        
    # 2. Orchestrator Hydration Çağrısı (Startup LifeSpan davranışı)
    orch = get_repair_orchestrator()
    count = await orch.hydrate_from_db()
    
    # 3. Assertion: Alembic migrasyonu çalıştığı için 'meta' çökmemeli
    assert orch._hydrated is True
    
    # 4. Liste üzerinden meta doğrulama
    jobs = await orch.list_jobs(limit=100)
    found_job = next((j for j in jobs if j.job_id == test_job_id), None)
    
    assert found_job is not None, "Job listelemede gelmeli"
    assert found_job.status.value == "new"
