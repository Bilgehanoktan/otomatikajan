
import os
from libs.db.session import get_engine, is_db_degraded

engine = get_engine()
print(f"Engine URL: {engine.url}")
print(f"Is Degraded: {is_db_degraded()}")

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath("libs/db/session.py"))))
print(f"Computed Root: {_root}")
sqlite_path = os.path.join(_root, "runtime", "data", "cortex_local.db")
print(f"Expected Path: {sqlite_path}")
print(f"Exists: {os.path.exists(sqlite_path)}")
