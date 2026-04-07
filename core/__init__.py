import os
import sys
from pathlib import Path

# Redirect 'core' to 'packages/orchestration'
_base_dir = Path(__file__).parent.parent
_new_path = _base_dir / "packages" / "orchestration"

if _new_path.exists():
    __path__ = [str(_new_path)]
else:
    import logging
    logging.warning(f"Core shim: New path {_new_path} does not exist.")
