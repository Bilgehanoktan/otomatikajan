import os
import sys
from pathlib import Path

# Redirect 'telegram_app' to 'apps/telegram_bot'
_base_dir = Path(__file__).parent.parent
_new_path = _base_dir / "apps" / "telegram_bot"

if _new_path.exists():
    __path__ = [str(_new_path)]
else:
    import logging
    logging.warning(f"Telegram App shim: New path {_new_path} does not exist.")
