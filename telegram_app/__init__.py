import sys
import logging

# Redirect 'telegram_app' to 'apps.telegram_bot'
try:
    import apps.telegram_bot
    sys.modules['telegram_app'] = apps.telegram_bot
except ImportError as e:
    logging.warning(f"Failed to create shim for 'telegram_app': {e}")
