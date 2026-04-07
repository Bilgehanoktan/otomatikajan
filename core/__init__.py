import sys
import logging

# Redirect 'core' to 'packages.orchestration'
try:
    import packages.orchestration
    sys.modules['core'] = packages.orchestration
except ImportError as e:
    logging.warning(f"Failed to create shim for 'core': {e}")
