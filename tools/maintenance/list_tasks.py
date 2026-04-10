import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from apps.worker.tasks.celery_app import celery_app

print("📋 REGISTERED CELERY TASKS:")
for task_name in sorted(celery_app.tasks.keys()):
    print(f"  - {task_name}")
