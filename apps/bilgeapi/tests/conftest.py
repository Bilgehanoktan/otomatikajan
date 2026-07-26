import sys
import os
import asyncio
from pathlib import Path

# Bootstrap python path to make bilgeapi and import shim available
tests_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(tests_dir) # apps/bilgeapi
parent_dir = os.path.dirname(root_dir) # apps/
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Override default workspace to be a test workspace inside the package to keep it self-contained
from bilgeapi.core.workspace import WorkspaceManager
test_workspace = os.path.join(root_dir, "runtime", "test_workspace")
os.makedirs(os.path.join(test_workspace, "memory"), exist_ok=True)

original_init = WorkspaceManager.__init__
def mock_init(self, start_path=None, *args, **kwargs):
    if start_path is None and not os.getenv("BILGEAPI_MANAGED_ROOT"):
        start_path = Path(test_workspace)
    original_init(self, start_path=start_path, *args, **kwargs)

WorkspaceManager.__init__ = mock_init

# Import bilgeapi to trigger its __init__.py and import shim
try:
    import bilgeapi
except ImportError:
    pass

# Initialize default database schemas for tests
from bilgeapi.memory.db import init_workspace_db
from bilgeapi.libs.db.session import get_engine
from bilgeapi.models.database import Base

try:
    async def init_databases():
        # Initialize workspace memory db
        await init_workspace_db(Path(test_workspace))
        
        # Initialize main database tables
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_databases())
    loop.close()
except Exception as e:
    print(f"Failed to initialize test DBs: {e}")

