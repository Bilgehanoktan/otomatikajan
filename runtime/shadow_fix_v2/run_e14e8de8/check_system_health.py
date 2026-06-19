import asyncio
import os
import sys
import socket
import urllib.request
import urllib.error
import json
import subprocess

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

def print_status(name, ok, details=""):
    status_str = "\033[92m[PASS]\033[0m" if ok else "\033[91m[FAIL]\033[0m"
    print(f" {status_str} {name:<40} {details}")

async def test_endpoint(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3.0) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            return status == 200, f"HTTP {status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"Connection Failed: {str(e)}"

def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(('127.0.0.1', port))
            return True
    except Exception:
        return False

async def main():
    print_header("Sovereign AGI Deep Health Verification")
    
    # 1. Backend Port & GET /health Check (Port 8000)
    print("\n[*] 1. Backend API Connectivity Check (Port 8000)...")
    backend_live = check_port(8000)
    if backend_live:
        print_status("Backend TCP Port 8000 Open", True)
        ok, details = await test_endpoint("http://localhost:8000/health")
        print_status("Backend GET /health Status", ok, details)
    else:
        print_status("Backend TCP Port 8000 Open", False, "Uvicorn server might not be running on Port 8000")
        print_status("Backend GET /health Status", False, "Backend unreachable")

    # 2. Frontend Port & HTTP GET Check (Port 3100)
    print("\n[*] 2. Frontend Control Plane Check (Port 3100)...")
    frontend_live = check_port(3100)
    if frontend_live:
        print_status("Frontend TCP Port 3100 Open", True)
        # Frontend Next.js might return 200 or 307 depending on redirection/authentication
        ok, details = await test_endpoint("http://localhost:3100")
        print_status("Frontend HTTP Access Check", ok, details)
    else:
        print_status("Frontend TCP Port 3100 Open", False, "Next.js dev server might not be running on Port 3100")

    # 3. GET /api/v1/workflows/stats/summary Check
    print("\n[*] 3. Workflow API Service Summary Check...")
    if backend_live:
        ok, details = await test_endpoint("http://localhost:8000/api/v1/workflows/stats/summary")
        print_status("Workflow Stats Summary Endpoint", ok, details)
    else:
        print_status("Workflow Stats Summary Endpoint", False, "Skipped (Backend offline)")

    # 4. GET /api/v1/health/dashboard Check
    print("\n[*] 4. Health Dashboard Summary Check...")
    if backend_live:
        ok, details = await test_endpoint("http://localhost:8000/api/v1/health/dashboard")
        print_status("Health Dashboard Endpoint", ok, details)
    else:
        print_status("Health Dashboard Endpoint", False, "Skipped (Backend offline)")

    # 5. Playwright Browser & Runtime Guard Dependency Check
    print("\n[*] 5. Self-Repair Runtime Dependency Guard Probe...")
    try:
        from services.ui_repair.runtime_guard import check_runtime_dependencies
        guard = await check_runtime_dependencies()
        if guard["status"] == "degraded":
            print_status("Runtime Guard", False, f"Degraded - Reason: {guard['reason']}")
            print(f"      - Operator Action Required: \033[93m{guard['operator_action']}\033[0m")
            print(f"      - Fallback Activated: {guard['fallback_used']}")
        else:
            print_status("Runtime Guard / Playwright", True, "All critical infrastructure and Playwright are fully active")
    except Exception as e:
        print_status("Runtime Guard Execution", False, f"Error checking dependencies: {str(e)}")

    # 6. Check if Docker mode dependency resolver is stuck/hanging
    print("\n[*] 6. Docker Mode Dependency Resolver Verification...")
    try:
        docker_check = subprocess.run(["docker", "ps", "--format", "{{.Names}} ({{.Status}})"], capture_output=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        if docker_check.returncode == 0:
            containers = docker_check.stdout.strip().split("\n")
            containers = [c for c in containers if c]
            if len(containers) > 0:
                print_status("Docker Engine Connection", True, f"{len(containers)} active container(s) detected")
                for c in containers:
                    print(f"      - Container: {c}")
                # Check for stuck resolver / unhealthy containers
                stuck_found = False
                for c in containers:
                    if "unhealthy" in c.lower() or "restarting" in c.lower():
                        stuck_found = True
                        print(f"      - \033[91m[WARNING]\033[0m Container '{c}' is stuck or unhealthy!")
                if not stuck_found:
                    print_status("Docker Container Stability", True, "No stuck or restarting containers found")
                else:
                    print_status("Docker Container Stability", False, "One or more containers are stuck/unhealthy")
            else:
                print_status("Docker Engine Connection", True, "No active Sovereign AGI docker containers (running in local mode)")
        else:
            print_status("Docker Engine Connection", True, "Docker is offline or not installed (System is operating in standard local mode)")
    except subprocess.TimeoutExpired:
        print_status("Docker Command Execution", False, "Docker ps command timed out! Daemon might be stuck or hanging")
    except Exception as e:
        print_status("Docker Check", True, "Docker command not available. Operating cleanly in Local/Venv Mode")

    # 7. Database Connectivity & SQLite fallback engine seeding
    print("\n[*] 7. Database Health & SQLite Fallback Seeding Check...")
    try:
        from libs.db.session import is_db_degraded, AsyncSessionLocal
        from sqlalchemy import text
        
        degraded = is_db_degraded()
        if degraded:
            print_status("Database Connection Status", True, "Operating in Graceful SQLite Fallback mode")
            # Verify if fallback file exists
            sqlite_path = "runtime/data/cortex_local_v2.db"
            if os.path.exists(sqlite_path):
                print_status("SQLite Fallback DB File Found", True, f"Located at: {sqlite_path} ({os.path.getsize(sqlite_path)} bytes)")
            else:
                # Check other directories or local project root
                if os.path.exists("cortex_local_v2.db"):
                    print_status("SQLite Fallback DB File Found", True, f"Located in project root ({os.path.getsize('cortex_local_v2.db')} bytes)")
                else:
                    print_status("SQLite Fallback DB File Found", False, "DB File missing, auto-seeding will occur upon first request")
        else:
            print_status("Database Connection Status", True, "Primary database connection healthy (PostgreSQL)")

        # Verify active session query execution
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            scalar = result.scalar()
            if scalar == 1:
                print_status("DB Query Execution Test", True, "Session queries validated successfully")
            else:
                print_status("DB Query Execution Test", False, "Query executed but returned incorrect value")

    except Exception as e:
        print_status("Database Integrity Check", False, f"DB Error: {str(e)}")

    # 8. Autonomous Watchdog & Auto-Heal Probe
    print("\n[*] 8. Autonomous Watchdog & Auto-Heal Probe...")
    watchdog_path = "services/ui_repair/watchdog/watchdog.ps1"
    if os.path.exists(watchdog_path):
        print_status("Watchdog Script Found", True, f"Located at: {watchdog_path}")
        try:
            # Query CIM instance for any running PowerShell processes containing watchdog.ps1
            cmd = 'Get-CimInstance Win32_Process -Filter "CommandLine LIKE \'%watchdog.ps1%\'" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessId'
            proc_check = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=3)
            active_pids = proc_check.stdout.strip().split()
            active_pids = [p for p in active_pids if p]
            if len(active_pids) > 0:
                print_status("Watchdog Active State", True, f"Running in background (PID: {', '.join(active_pids)})")
            else:
                print_status("Watchdog Active State", False, "Inactive - Run services/ui_repair/watchdog/kur_watchdog.bat to register background service")
        except Exception as e:
            print_status("Watchdog Active State", False, f"Check failed: {e}")
    else:
        print_status("Watchdog Script Found", False, "watchdog.ps1 is missing from workspace")

    print_header("Health Check Complete")

if __name__ == "__main__":
    # Handle event loop policies for Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
