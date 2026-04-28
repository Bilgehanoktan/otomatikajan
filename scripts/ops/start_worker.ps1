$env:PYTHONPATH = "."
$env:REDIS_URL = "redis://127.0.0.1:6380/0"
# SRE: DATABASE_URL will be inherited from current shell or .env to ensure consistency
celery -A workers.workflow_worker.tasks.celery_app worker --loglevel=info -P solo
