import os, sys, asyncio, sqlite3, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
os.environ['SOVEREIGN_DOTENV_OVERRIDE'] = 'false'
os.environ['RUNTIME_PROFILE'] = 'local-dev'
os.environ['REDIS_ENABLED'] = 'false'
os.environ['CELERY_ENABLED'] = 'false'
os.environ['QUEUE_BACKEND'] = 'inprocess'
os.environ['APP_UI_MODE'] = 'api-only'
PROJECT_ID = 'd940148e-54e9-4302-a18d-cc037ca255cf'

async def main():
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project
    from sqlalchemy import select
    from libs.workflow.runner import run_project_workflow

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Project).where(Project.id == PROJECT_ID))
        project = res.scalar_one()
        print('BEFORE', project.status.value, project.job_id, project.retry_count, project.error_detail)
        title = project.title
        description = project.description or ''
        workflow_template = project.workflow_template or 'default'
        quality_profile = project.quality_profile or 'standard'
        acceptance_criteria = project.acceptance_criteria or []
        execution_context = project.execution_context or {}

    instance = await run_project_workflow(
        project_id=PROJECT_ID,
        title=title,
        description=description,
        workflow_template=workflow_template,
        quality_profile=quality_profile,
        acceptance_criteria=acceptance_criteria,
        execution_context=execution_context,
    )
    print('INSTANCE', instance.status, instance.error)

    p = pathlib.Path('runtime/data/cortex_local_v2.db')
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    project = con.execute('select id,title,status,job_id,retry_count,error_detail,updated_at from projects where id=?', (PROJECT_ID.replace('-', ''),)).fetchone()
    print('PROJECT', dict(project) if project else None)
    for event in con.execute('select event_type,payload,created_at from workflow_events where project_id=? order by created_at desc limit 8', (PROJECT_ID.replace('-', ''),)):
        print('EVENT', json.dumps(dict(event), ensure_ascii=True))
    for step in con.execute('select agent_id,action,status,attempts,result,updated_at from subtasks where project_id=? order by created_at', (PROJECT_ID.replace('-', ''),)):
        print('STEP', json.dumps(dict(step), ensure_ascii=True)[:700])

asyncio.run(main())

