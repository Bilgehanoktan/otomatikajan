import sys
import logging

# Redirect 'memory' to 'packages.memory'
try:
    import packages.memory
    sys.modules['memory'] = packages.memory
except ImportError as e:
    logging.warning(f"Failed to create shim for 'memory': {e}")
