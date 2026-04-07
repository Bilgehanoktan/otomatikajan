import sys
import logging
from pathlib import Path

# Redirect 'integrations' to 'packages.integrations'
try:
    import packages.integrations
    sys.modules['integrations'] = packages.integrations
    # Also redirect submodules if needed
    # (Note: Standard python import mechanism will now look into packages.integrations for submodules)
except ImportError as e:
    logging.warning(f"Failed to create shim for 'integrations': {e}")
