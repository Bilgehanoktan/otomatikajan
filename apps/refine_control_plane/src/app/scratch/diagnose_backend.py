import subprocess
import time
import urllib.request
import os
import signal

def run_test():
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    # Start backend
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "apps.public_api.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Backend starting...")
    time.sleep(15) # Wait for startup
    
    if proc.poll() is not None:
        print(f"Backend failed to start. Exit code: {proc.poll()}")
        print("STDOUT:", proc.stdout.read())
        print("STDERR:", proc.stderr.read())
        return

    print("Making request to /api/v1/workflows...")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/v1/workflows", timeout=10) as response:
            print(f"Response status: {response.status}")
            data = response.read().decode()
            print(f"Response data length: {len(data)}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    time.sleep(5)
    
    if proc.poll() is not None:
        print(f"Backend crashed after request! Exit code: {proc.poll()}")
        print("STDOUT tail:")
        for line in proc.stdout.readlines():
            print(line.strip())
        print("STDERR:")
        for line in proc.stderr.readlines():
            print(line.strip())
    else:
        print("Backend still running. Sending SIGTERM...")
        proc.terminate()

if __name__ == "__main__":
    run_test()
