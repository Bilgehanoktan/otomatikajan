import os, sys, asyncio, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
os.environ['SOVEREIGN_DOTENV_OVERRIDE'] = 'false'
os.environ['RUNTIME_PROFILE'] = 'local-dev'
os.environ['REDIS_ENABLED'] = 'false'
os.environ['CELERY_ENABLED'] = 'false'
os.environ['QUEUE_BACKEND'] = 'inprocess'
PROJECT_ID = 'd940148e-54e9-4302-a18d-cc037ca255cf'

async def main():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, ProjectStatus
    from libs.workflow.persistence import WorkflowPersistence
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == PROJECT_ID))
        project = res.scalar_one()
        final_status = (project.execution_context or {}).get('final_status')
        print('BEFORE', project.status.value, 'final_status=', final_status)
        if project.status == ProjectStatus.COMPLETED and str(final_status).upper().endswith('ERROR'):
            project.status = ProjectStatus.ERROR
            project.error_detail = 'Semantic final_status was TaskStatus.ERROR after live repair investigation.'
            await db.commit()
            await WorkflowPersistence.save_event(
                PROJECT_ID,
                'workflow_semantic_status_corrected',
                payload={
                    'previous_status': 'COMPLETED',
                    'corrected_status': 'ERROR',
                    'reason': 'execution_context.final_status indicated TaskStatus.ERROR',
                    'operator_id': 'codex_live_probe',
                },
            )
        else:
            await db.rollback()
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == PROJECT_ID))
        project = res.scalar_one()
        print('AFTER', project.status.value, project.error_detail)

asyncio.run(main())
