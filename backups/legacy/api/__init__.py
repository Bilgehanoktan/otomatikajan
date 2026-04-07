import os
import sys
from pathlib import Path

# Redirect 'api' to 'apps/api'
_base_dir = Path(__file__).parent.parent
_new_path = _base_dir / "apps" / "api"

if _new_path.exists():
    __path__ = [str(_new_path)]
else:
    import logging
    logging.warning(f"API shim: New path {_new_path} does not exist.")
