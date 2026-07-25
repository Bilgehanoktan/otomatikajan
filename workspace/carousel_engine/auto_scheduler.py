"""
Autonomous Continuous Scheduler & Content Engine for @Ai_gucum_.
Generates new trending AI tool carousel batches and publishes them on schedule.
"""

import os
import sys
import time
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USER_DATA_DIR = BASE_DIR / "workspace" / "carousel_engine" / "browser_profile"

def run_autonomous_cycle():
    print("=" * 70)
    print("🚀 OTONOM SÜREKLİ YAYIN MOTORU ÇALIŞIYOR (@Ai_gucum_)")
    print("=" * 70)

    # Step 1: Generate new Ultra HD batch if needed
    from workspace.carousel_engine.batch_generator import run_batch_generation
    run_batch_generation()

    # Step 2: Publish pending carousel to Instagram feed
    from workspace.carousel_engine.post_via_profile import publish_all_pending_carousels
    publish_all_pending_carousels()

if __name__ == "__main__":
    run_autonomous_cycle()
