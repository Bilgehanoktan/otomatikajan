import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from libs.db.models import SovereignCodeFile, SovereignCodeResult


def _utcnow():
    return datetime.now(UTC)

class CodeRepository:
    """
    Sovereign Code Generation için veri erişim katmanı.
    Faz 12.1 uyumlu kalıcılık sağlar.
    """

    @staticmethod
    async def create_result(
        db: AsyncSession,
        project_id: uuid.UUID,
        title: str,
        language: str = "mixed",
        technologies: list[str] = None,
        summary: str = "",
        provenance_hash: str = None
    ) -> SovereignCodeResult:
        result = SovereignCodeResult(
            project_id=project_id,
            title=title,
            language=language,
            technologies=technologies or [],
            summary=summary,
            provenance_hash=provenance_hash,
            status="generating"
        )
        db.add(result)
        await db.flush()
        return result

    @staticmethod
    async def add_files(
        db: AsyncSession,
        result_id: uuid.UUID,
        files_data: list[dict]
    ) -> list[SovereignCodeFile]:
        files = []
        for f in files_data:
            code_file = SovereignCodeFile(
                result_id=result_id,
                filename=f["filename"],
                path=f["path"],
                content=f["content"],
                language=f.get("language", "python"),
                is_generated=f.get("is_generated", True),
                provenance_id=f.get("provenance_id")
            )
            files.append(code_file)

        db.add_all(files)
        # Update total_files count
        await db.execute(
            update(SovereignCodeResult)
            .where(SovereignCodeResult.id == result_id)
            .values(total_files=len(files), status="completed", updated_at=_utcnow())
        )
        await db.flush()
        return files

    @staticmethod
    async def get_result(db: AsyncSession, result_id: uuid.UUID) -> SovereignCodeResult | None:
        query = select(SovereignCodeResult).where(SovereignCodeResult.id == result_id).options(selectinload(SovereignCodeResult.files))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_project(db: AsyncSession, project_id: uuid.UUID) -> SovereignCodeResult | None:
        query = select(SovereignCodeResult).where(SovereignCodeResult.project_id == project_id).options(selectinload(SovereignCodeResult.files))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_recent(db: AsyncSession, limit: int = 20) -> list[SovereignCodeResult]:
        query = select(SovereignCodeResult).order_by(desc(SovereignCodeResult.created_at)).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_status(db: AsyncSession, result_id: uuid.UUID, status: str, summary: str = None):
        values = {"status": status, "updated_at": _utcnow()}
        if summary:
            values["summary"] = summary

        await db.execute(
            update(SovereignCodeResult)
            .where(SovereignCodeResult.id == result_id)
            .values(**values)
        )
