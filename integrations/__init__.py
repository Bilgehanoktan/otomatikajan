import os
import sys
from pathlib import Path

# Redirect 'integrations' to 'packages.integrations'
# This shim allows 'import integrations.submodule' to work by pointing to the new location.

_base_dir = Path(__file__).parent.parent
_new_path = _base_dir / "packages" / "integrations"

if _new_path.exists():
    __path__ = [str(_new_path)]
else:
    import logging
    logging.warning(f"Integrations shim: New path {_new_path} does not exist.")
