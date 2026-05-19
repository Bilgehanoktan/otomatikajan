import os, sys, asyncio, sqlite3, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

os.environ['SOVEREIGN_DOTENV_OVERRIDE'] = 'false'
os.environ['RUNTIME_PROFILE'] = 'local-dev'
os.environ['REDIS_ENABLED'] = 'false'
os.environ['CELERY_ENABLED'] = 'false'
os.environ['QUEUE_BACKEND'] = 'inprocess'
os.environ['APP_UI_MODE'] = 'api-only'

PROJECT_ID = 'd940148e-54e9-4302-a18d-cc037ca255cf'

async def main():
    from services.workflow_api.router import reassign_workflow, ReassignRequest
    from services.orchestration.application.job_queue import job_queue
    from libs.workflow.runner import register_workflow_handlers

    await register_workflow_handlers(job_queue)
    await job_queue.start(num_workers=1)
    try:
        result = await reassign_workflow(
            PROJECT_ID,
            ReassignRequest(
                operator_id='codex_live_probe',
                reason='Verify fixed GovernedTask planner normalization after terminal workflow failure.',
                reset_steps=True,
                preserve_completed_steps=True,
            ),
            identity={'id': 'codex-live', 'name': 'Codex Live Probe'},
        )
        print('REASSIGN_RESULT', result)
        for _ in range(90):
            stats = job_queue.stats()
            print('QUEUE_STATS', stats)
            if stats.get('pending', 0) == 0 and stats.get('running', 0) == 0 and job_queue._queue.qsize() == 0:
                break
            await asyncio.sleep(2)
    finally:
        await job_queue.stop()

    p = pathlib.Path('runtime/data/cortex_local_v2.db')
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    project = con.execute('select id,title,status,job_id,retry_count,error_detail,updated_at from projects where id=?', (PROJECT_ID.replace('-', ''),)).fetchone()
    print('PROJECT', dict(project) if project else None)
    events = con.execute('select event_type,payload,created_at from workflow_events where project_id=? order by created_at desc limit 8', (PROJECT_ID.replace('-', ''),)).fetchall()
    for event in events:
        print('EVENT', dict(event))
    steps = con.execute('select agent_id,action,status,attempts,result,updated_at from subtasks where project_id=? order by created_at', (PROJECT_ID.replace('-', ''),)).fetchall()
    for step in steps:
        print('STEP', dict(step))

asyncio.run(main())

