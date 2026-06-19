#!/usr/bin/env python
"""
scripts/run_release_gate.py — Phase 11
CLI runner for BilgeAPI production release gate.
Allows running pytest dynamically (evidence generation) and computes the readiness scorecard.
Exits with code 1 if status is BLOCKED, otherwise exits with 0.
"""
import argparse
import asyncio
import os
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

# ANSI Colors
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_BLUE = "\033[94m"
COLOR_RESET = "\033[0m"


def run_tests_subprocess():
    """Runs the test suite and captures output to pytest_output.txt."""
    print(f"{COLOR_BLUE}[CLI Release Gate] Running test suite to gather evidence...{COLOR_RESET}")
    cmd = ["python", "-m", "pytest", "tests/unit/bilgeapi/", "-v"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        with open("pytest_output.txt", "w", encoding="utf-8") as f:
            f.write(res.stdout)
        
        if res.returncode == 0:
            print(f"{COLOR_GREEN}[CLI Release Gate] Test suite ran successfully (exit 0).{COLOR_RESET}")
        else:
            print(f"{COLOR_YELLOW}[CLI Release Gate] Test suite completed with failures (exit {res.returncode}).{COLOR_RESET}")
    except Exception as e:
        print(f"{COLOR_RED}[CLI Release Gate] Failed to run test suite: {e}{COLOR_RESET}")


async def main():
    parser = argparse.ArgumentParser(description="BilgeAPI v1.0 Production Release Gate Runner")
    parser.add_argument("--run-tests", action="store_true", help="Execute pytest suite to generate evidence before checks")
    parser.add_argument("--env", type=str, default=None, help="Force override APP_ENV (production/development/test)")
    args = parser.parse_args()

    # Load session and config first to let them parse .env
    from libs.db.session import AsyncSessionLocal
    import libs.config

    if args.env:
        os.environ["APP_ENV"] = args.env
        # Update libs.config attributes for production checking consistency
        libs.config.APP_ENV = args.env
        libs.config.is_prod = (args.env == "production")
        libs.config.is_dev = (args.env == "development")
        libs.config.is_test = (args.env == "test")

    if args.run_tests or not os.path.exists("pytest_output.txt"):
        run_tests_subprocess()

    print(f"\n{COLOR_BLUE}=====================================================")
    print("      BilgeAPI v1.0 Production Release Gate Gatekeeper")
    print(f"====================================================={COLOR_RESET}")

    from apps.bilgeapi.repositories.postgres import PostgresReleaseCheckRepository
    from apps.bilgeapi.services.release import BilgeAPIReleaseGate

    async with AsyncSessionLocal() as db:
        repo = PostgresReleaseCheckRepository(db)
        gate = BilgeAPIReleaseGate(repo)

        print("[CLI Release Gate] Running readiness audit...")
        check_data = await gate.execute_readiness_audit(triggered_by="CLI-Runner")

        # Dynamically verify endpoints against the app routes
        from apps.bilgeapi.main import app
        endpoints_res = gate.check_endpoints(app)
        check_data["checked_endpoints"] = endpoints_res

        # Check for missing endpoints
        missing_endpoints = [ep for ep, stat in endpoints_res.items() if stat == "MISSING"]
        if missing_endpoints:
            check_data["blockers"].append(f"Crucial endpoint check failed: {', '.join(missing_endpoints)}")
            check_data["status"] = "BLOCKED"
            # Recalculate score
            score = 100.0 - len(check_data["warnings"]) * 5.0 - len(check_data["blockers"]) * 20.0
            check_data["score"] = max(0.0, score)

        # Print detailed scorecard
        status = check_data["status"]
        score = check_data["score"]
        blockers = check_data["blockers"]
        warnings = check_data["warnings"]
        modules = check_data["checked_modules"]
        endpoints = check_data["checked_endpoints"]

        print(f"\n--- AUDIT SCORECARD ---")
        print(f"Environment: {check_data['environment'].upper()}")
        print(f"Git SHA:     {check_data['git_sha']}")
        print(f"Version:     {check_data['app_version']}")
        print(f"Score:       {score:.2f}")

        status_color = COLOR_GREEN
        if status == "BLOCKED":
            status_color = COLOR_RED
        elif status == "WARNING":
            status_color = COLOR_YELLOW

        print(f"Status:      {status_color}{status}{COLOR_RESET}")

        print(f"\n--- CORE MODULES ({len(modules)}) ---")
        for mod, state in modules.items():
            state_color = COLOR_GREEN if state == "OK" else COLOR_RED
            print(f"  {mod:<40}: {state_color}{state}{COLOR_RESET}")

        print(f"\n--- CORE ENDPOINTS ({len(endpoints)}) ---")
        for ep, state in endpoints.items():
            state_color = COLOR_GREEN if state == "VERIFIED_PRESENT" else COLOR_RED
            print(f"  {ep:<40}: {state_color}{state}{COLOR_RESET}")

        print(f"\n--- WARNINGS ({len(warnings)}) ---")
        if warnings:
            for w in warnings:
                print(f"  {COLOR_YELLOW}[WARNING]{COLOR_RESET} {w}")
        else:
            print("  None")

        print(f"\n--- BLOCKERS ({len(blockers)}) ---")
        if blockers:
            for b in blockers:
                print(f"  {COLOR_RED}[BLOCKER]{COLOR_RESET} {b}")
        else:
            print("  None")

        # Persist the check results to the DB
        persisted = await repo.create_check(check_data)
        print(f"\n{COLOR_GREEN}[CLI Release Gate] Results persisted to DB. Record ID: {persisted['id']}{COLOR_RESET}")

        print(f"\n{COLOR_BLUE}=====================================================")
        if status == "BLOCKED":
            print(f"      RELEASE DECISION: {COLOR_RED}NO-GO (BLOCKED){COLOR_RESET}")
            print(f"====================================================={COLOR_RESET}")
            sys.exit(1)
        elif status == "WARNING":
            print(f"      RELEASE DECISION: {COLOR_YELLOW}CONDITIONAL GO (WARNING){COLOR_RESET}")
            print(f"====================================================={COLOR_RESET}")
            sys.exit(0)
        else:
            print(f"      RELEASE DECISION: {COLOR_GREEN}GO (PASSED){COLOR_RESET}")
            print(f"====================================================={COLOR_RESET}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit as e:
        sys.exit(e.code)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
