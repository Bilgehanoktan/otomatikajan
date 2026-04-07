import sys
import logging

# Redirect 'api' to 'apps.api'
try:
    import apps.api
    sys.modules['api'] = apps.api
except ImportError as e:
    logging.warning(f"Failed to create shim for 'api': {e}")
