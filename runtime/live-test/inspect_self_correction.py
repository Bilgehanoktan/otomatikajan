import sqlite3, pathlib
p = pathlib.Path('runtime/data/cortex_local_v2.db')
con = sqlite3.connect(p)
con.row_factory = sqlite3.Row
print('SUBTASK_COLUMNS')
for r in con.execute('pragma table_info(subtasks)'):
    print(dict(r))
rows = con.execute("""
select id,title,status,job_id,retry_count,error_detail,notes,created_at,updated_at,cancelled_at,cancelled_by
from projects
where title like ?
order by updated_at desc
limit 12
""", ('%Self-Correction Pilot%',)).fetchall()
for r in rows[:5]:
    pid = r['id']
    print('--- PID', pid, r['status'], r['job_id'])
    for e in con.execute('select event_type,step_id,payload,created_at from workflow_events where project_id=? order by created_at desc limit 18', (pid,)):
        print('EVENT', dict(e))
    for s in con.execute('select * from subtasks where project_id=? order by created_at', (pid,)):
        print('SUBTASK', dict(s))
