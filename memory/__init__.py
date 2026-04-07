import os
import sys
from pathlib import Path

# Redirect 'memory' to 'packages/memory'
_base_dir = Path(__file__).parent.parent
_new_path = _base_dir / "packages" / "memory"

if _new_path.exists():
    __path__ = [str(_new_path)]
else:
    import logging
    logging.warning(f"Memory shim: New path {_new_path} does not exist.")

# Redirect 'api' to 'apps/api'
_api_path = _base_dir / "apps" / "api"

if _api_path.exists():
    __path__.append(str(_api_path))
else:
    import logging
    logging.warning(f"API shim: New path {_api_path} does not exist.")
