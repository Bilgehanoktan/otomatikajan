$env:PYTHONPATH = "."
$env:REDIS_URL = "redis://127.0.0.1:6380/0"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/ai_company"
celery -A workers.workflow_worker.tasks.celery_app worker --loglevel=info -P solo
