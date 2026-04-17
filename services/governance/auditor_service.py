import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from libs.db.session import get_db
from libs.db.models.compliance_models import AuditBundle
from services.governance.compliance_service import ComplianceService
from services.observability.logging import get_logger

logger = get_logger("governance.auditor")

class AuditorService:
    EXPORT_DIR = "runtime/data/audit_exports"

    @staticmethod
    async def prepare_export_package(bundle_id: str) -> str:
        """
        Takes an AuditBundle record, fetches the linked data, 
        and packages it into a verifiable ZIP file.
        """
        os.makedirs(AuditorService.EXPORT_DIR, exist_ok=True)
        
        async with get_db() as session:
            # Fetch bundle
            from sqlalchemy import select
            result = await session.execute(select(AuditBundle).where(AuditBundle.id == bundle_id))
            bundle = result.scalar_one_or_none()
            
            if not bundle:
                raise ValueError(f"Audit bundle {bundle_id} not found.")

            metadata = bundle.evidence_metadata
            package_name = f"{bundle.bundle_name.replace(' ', '_')}_{bundle.id.hex[:8]}"
            package_path = os.path.join(AuditorService.EXPORT_DIR, f"{package_name}.zip")
            
            # Temporary JSON file for evidence
            evidence_file = os.path.join(AuditorService.EXPORT_DIR, f"{package_name}_evidence.json")
            
            # Fetch actual records based on metadata IDs
            # (In a larger system, we'd fetch full objects here)
            export_content = {
                "bundle_header": {
                    "id": str(bundle.id),
                    "name": bundle.bundle_name,
                    "purpose": bundle.purpose,
                    "range": {
                        "start": bundle.start_time.isoformat(),
                        "end": bundle.end_time.isoformat()
                    },
                    "integrity_hash": bundle.integrity_hash,
                    "created_at": bundle.created_at.isoformat()
                },
                "evidence_ids": metadata
            }

            with open(evidence_file, "w", encoding="utf-8") as f:
                json.dump(export_content, f, indent=2, ensure_ascii=False)

            # Create ZIP
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(evidence_file, arcname="evidence.json")
                # We could also add a manifest.txt with the hash
                manifest = f"Sovereign AGI Audit Manifest\n"
                manifest += f"Package: {package_name}\n"
                manifest += f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
                manifest += f"Integrity Hash: {bundle.integrity_hash}\n"
                zipf.writestr("manifest.txt", manifest)

            # Cleanup temp file
            os.remove(evidence_file)
            
            # Update bundle with path
            bundle.storage_path = package_path
            await session.commit()
            
            logger.info(f"Audit package generated: {package_path}")
            return package_path

    @staticmethod
    async def create_and_export_bundle(name: str, purpose: str, start: datetime, end: datetime, operator: str) -> str:
        """Helper to create and export in one go."""
        bundle = await ComplianceService.generate_audit_bundle(name, purpose, start, end, operator)
        return await AuditorService.prepare_export_package(bundle.id)
