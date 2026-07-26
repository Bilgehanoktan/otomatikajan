#!/usr/bin/env python3
"""
scripts/bilgeapi_supervisor.py
External Recovery Supervisor for BilgeAPI (Phase 31CDE).
Monitors service health, triggers allowlisted container restarts without shell=True,
and caches events locally in a spool file if BilgeAPI is down.
"""
import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Security Allowlist for Subprocess execution (No shell=True)
ALLOWED_SERVICES = {"bilgeapi", "worker", "app"}

ALLOWED_COMMANDS = {
    "bilgeapi": ["docker", "compose", "restart", "bilgeapi"],
    "worker": ["docker", "compose", "restart", "worker"],
    "app": ["docker", "compose", "restart", "app"],
    "logs_bilgeapi": ["docker", "compose", "logs", "--tail=100", "bilgeapi"],
    "logs_worker": ["docker", "compose", "logs", "--tail=100", "worker"],
    "logs_app": ["docker", "compose", "logs", "--tail=100", "app"],
}

class BilgeApiSupervisor:
    def __init__(
        self,
        url: str,
        service: str,
        cooldown: int,
        max_attempts: int,
        spool_file: str,
        api_key: str,
        mode: str = "prod"
    ):
        self.url = url
        self.service = service
        self.cooldown = cooldown
        self.max_attempts = max_attempts
        self.spool_file = spool_file
        self.api_key = api_key
        self.mode = mode  # "prod" or "test" (mock restarts)
        
        # Ensure directory for spool file exists
        spool_dir = os.path.dirname(os.path.abspath(self.spool_file))
        os.makedirs(spool_dir, exist_ok=True)

    def check_health(self) -> bool:
        """Pings health endpoint, returns True if status is 'ok'."""
        try:
            parsed_url = urllib.parse.urlparse(self.url)
            if parsed_url.scheme not in ("http", "https"):
                raise ValueError(f"Forbidden URL scheme: {parsed_url.scheme}")
            req = urllib.request.Request(self.url, method="GET")
            req.add_header("Timeout", "5")
            with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("status") == "ok"
        except Exception as e:
            # Service is unreachable or returns error
            sys.stderr.write(f"Health check failed for {self.url}: {e}\n")
        return False

    def get_state(self) -> Dict[str, Any]:
        """Reads tracking state to evaluate cooldown & max attempts."""
        state_file = self.spool_file + ".state"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"attempts": 0, "last_attempt_time": 0.0}

    def save_state(self, state: Dict[str, Any]):
        """Saves tracking state to evaluate cooldown & max attempts."""
        state_file = self.spool_file + ".state"
        try:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"Failed to save supervisor state: {e}\n")

    def spool_event(self, event: Dict[str, Any]):
        """Appends a recovery event to the local spool jsonl file."""
        try:
            with open(self.spool_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            sys.stderr.write(f"Failed to spool event: {e}\n")

    def run_restart(self) -> tuple[bool, str, str]:
        """Runs the allowlisted subprocess restart command (No shell=True)."""
        if self.service not in ALLOWED_SERVICES:
            return False, "", f"Service {self.service} is not in the allowlist."

        cmd = ALLOWED_COMMANDS.get(self.service)
        if not cmd:
            return False, "", f"No command registered for service {self.service}."

        if self.mode == "test":
            # In test mode, we simulate the command execution
            return True, f"MOCK: Command {cmd} executed successfully.", ""

        try:
            # subprocess list-only call, shell=False by default.
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def flush_spool(self) -> int:
        """Sends spooled events to BilgeAPI once it recovers."""
        if not os.path.exists(self.spool_file):
            return 0

        # Read all events
        events: List[Dict[str, Any]] = []
        try:
            with open(self.spool_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except Exception as e:
            sys.stderr.write(f"Failed to read spool file for flush: {e}\n")
            return 0

        if not events:
            return 0

        # Attempt to post to BilgeAPI
        report_url = self.url.replace("/health", "/v1/watchdog/external-recovery/report")
        payload = {"events": events}
        try:
            data = json.dumps(payload).encode("utf-8")
            parsed_url = urllib.parse.urlparse(report_url)
            if parsed_url.scheme not in ("http", "https"):
                raise ValueError(f"Forbidden URL scheme: {parsed_url.scheme}")
            req = urllib.request.Request(
                report_url,
                data=data,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.api_key
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:  # nosec B310
                if response.status == 200:
                    # Successfully flushed, clear spool file and state attempts
                    os.remove(self.spool_file)
                    state = self.get_state()
                    state["attempts"] = 0
                    self.save_state(state)
                    sys.stdout.write(f"Successfully flushed {len(events)} spooled events to BilgeAPI.\n")
                    return len(events)
        except Exception as e:
            sys.stderr.write(f"Failed to flush spooled events to {report_url}: {e}\n")
        return 0

    def execute_recovery_cycle(self) -> Optional[Dict[str, Any]]:
        """Checks health and triggers restart if down, enforcing max attempts and cooldown."""
        is_healthy = self.check_health()
        if is_healthy:
            # Flush spool if there's any spooled events
            self.flush_spool()
            return None

        # Service is down, check state
        state = self.get_state()
        attempts = state.get("attempts", 0)
        last_attempt = state.get("last_attempt_time", 0.0)
        now = time.time()

        # Check cooldown
        elapsed = now - last_attempt
        if elapsed < self.cooldown:
            sys.stdout.write(f"Recovery cooldown active. {elapsed:.0f}s elapsed < {self.cooldown}s required.\n")
            return None

        # Check max attempts
        attempt_no = attempts + 1
        if attempt_no > self.max_attempts:
            sys.stdout.write(f"Recovery blocked: max attempts {self.max_attempts} reached.\n")
            return None

        # Run restart
        sys.stdout.write(f"Starting recovery attempt #{attempt_no} for service: {self.service}...\n")
        success, stdout, stderr = self.run_restart()
        
        # Log event
        event = {
            "event_type": "SUPERVISOR_RECOVERY_COMPLETED" if success else "SUPERVISOR_RECOVERY_FAILED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service_name": self.service,
            "attempt_no": attempt_no,
            "output": stdout,
            "error": stderr,
            "status": "success" if success else "failed"
        }
        self.spool_event(event)

        # Update state
        state["attempts"] = attempt_no
        state["last_attempt_time"] = now
        self.save_state(state)

        return event

def main():
    parser = argparse.ArgumentParser(description="BilgeAPI External Recovery Supervisor Daemon")
    parser.add_argument("--url", default="http://127.0.0.1:8100/health", help="Uptime health check URL")
    parser.add_argument("--service", default="bilgeapi", help="Service name (bilgeapi, worker, app)")
    parser.add_argument("--cooldown", type=int, default=300, help="Cooldown between recovery runs in seconds")
    parser.add_argument("--max-attempts", type=int, default=2, help="Max recovery attempts before manual escalation")
    parser.add_argument("--spool-file", default="runtime/recovery/supervisor_events.jsonl", help="Path to write spooled events")
    parser.add_argument("--api-key", default="dev-test-key-001", help="BilgeAPI admin API key")
    parser.add_argument("--mode", default="prod", choices=["prod", "test"], help="Execution mode (prod = runs docker restart, test = mock)")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous daemon loop checking every 30 seconds")
    
    args = parser.parse_args()
    
    supervisor = BilgeApiSupervisor(
        url=args.url,
        service=args.service,
        cooldown=args.cooldown,
        max_attempts=args.max_attempts,
        spool_file=args.spool_file,
        api_key=args.api_key,
        mode=args.mode
    )

    if args.loop:
        sys.stdout.write(f"Supervisor daemon running in loop mode for URL: {args.url}\n")
        while True:
            try:
                supervisor.execute_recovery_cycle()
            except KeyboardInterrupt:
                sys.stdout.write("Supervisor daemon stopped by user.\n")
                break
            except Exception as e:
                sys.stderr.write(f"Error in supervisor loop: {e}\n")
            time.sleep(30)
    else:
        # One-shot check
        supervisor.execute_recovery_cycle()

if __name__ == "__main__":
    main()
