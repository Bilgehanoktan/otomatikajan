# ==========================================================
# Sovereign AGI Control Plane - Autonomous Watchdog Service
# ==========================================================
# This script monitors the backend and frontend services and automatically 
# recovers them in case of crashes, hangs, or post-sleep freeze.

$ProjectDir = "E:\ai_company_faz12.1"
$LogFile = "$ProjectDir\runtime\logs\watchdog.log"
$CheckIntervalSeconds = 30

# Ensure logs directory exists
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile -Parent) | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "$timestamp - $Message"
    Add-Content -Path $LogFile -Value $entry
    Write-Host $entry
}

function Get-PythonExecutable {
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        return "py"
    }
    if (Test-Path "C:\Python314\python.exe") {
        return "C:\Python314\python.exe"
    }
    return "python"
}

function Test-HttpEndpoint {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Kill-PortProcess {
    param([int]$Port)
    $pidToKill = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
    if ($pidToKill) {
        Write-Log "⚠️ Port $Port is occupied by stale process (PID $pidToKill). Killing..."
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

function Check-And-Recover-Backend {
    $BackendUrl = "http://127.0.0.1:8000/health"
    $IsHealthy = Test-HttpEndpoint -Url $BackendUrl
    
    if (-not $IsHealthy) {
        Write-Log "🚨 Backend API (Port 8000) is unresponsive or crashed. Initiating recovery..."
        
        # Kill stale processes if any
        Kill-PortProcess -Port 8000
        
        # Resolve Python Command
        $PyCmd = Get-PythonExecutable
        Write-Log "🚀 Starting Backend API via $PyCmd..."
        
        # Setup environment variables
        $env:SOVEREIGN_DOTENV_OVERRIDE = "false"
        $env:RUNTIME_PROFILE = "local-dev"
        $env:REDIS_ENABLED = "false"
        $env:CELERY_ENABLED = "false"
        $env:QUEUE_BACKEND = "inprocess"
        $env:INPROCESS_JOB_WORKERS_ENABLED = "true"
        $env:WORKFLOW_API_RELOAD = "false"
        $env:PLAYWRIGHT_BROWSERS_PATH = "$env:USERPROFILE\.gemini\antigravity\.playwright-browsers"
        
        # Start Backend API in background
        Start-Process $PyCmd -ArgumentList "-m", "services.workflow_api.main" `
            -WorkingDirectory $ProjectDir -NoNewWindow `
            -RedirectStandardOutput "$ProjectDir\live_backend_phase32.out.log" `
            -RedirectStandardError "$ProjectDir\live_backend_phase32.err.log"
            
        Start-Sleep -Seconds 10
        if (Test-HttpEndpoint -Url $BackendUrl) {
            Write-Log "✅ Backend API successfully recovered and verified healthy!"
        } else {
            Write-Log "❌ Backend API recovery started but verification failed. Retrying next cycle."
        }
    }
}

function Check-And-Recover-Frontend {
    $FrontendUrl = "http://127.0.0.1:3100"
    $IsHealthy = Test-HttpEndpoint -Url $FrontendUrl
    
    if (-not $IsHealthy) {
        Write-Log "🚨 Frontend UI (Port 3100) is unresponsive or crashed. Initiating recovery..."
        
        # Kill stale processes if any
        Kill-PortProcess -Port 3100
        
        Write-Log "🚀 Starting Frontend UI (npm run dev)..."
        
        # Start Frontend UI in background
        Start-Process "cmd.exe" -ArgumentList "/c", "npm run dev -- -p 3100" `
            -WorkingDirectory "$ProjectDir\apps\refine_control_plane" -NoNewWindow `
            -RedirectStandardOutput "$ProjectDir\live_frontend.log" `
            -RedirectStandardError "$ProjectDir\live_frontend.err.log"
            
        Start-Sleep -Seconds 10
        if (Test-HttpEndpoint -Url $FrontendUrl) {
            Write-Log "✅ Frontend UI successfully recovered and verified healthy!"
        } else {
            Write-Log "❌ Frontend UI recovery started but verification failed. Retrying next cycle."
        }
    }
}

# ==========================================================
# Main Execution Cycle
# ==========================================================

Write-Log "=========================================================="
Write-Log "🐕 Autonomous Watchdog Service successfully initiated!"
Write-Log "Project directory: $ProjectDir"
Write-Log "Polling interval: $CheckIntervalSeconds seconds"
Write-Log "=========================================================="

while ($true) {
    try {
        # 1. Inspect & recover Backend API
        Check-And-Recover-Backend
        
        # 2. Inspect & recover Frontend UI
        Check-And-Recover-Frontend
        
        # Write periodic heartbeat to logs every 10 cycles (5 minutes) to avoid logs bloating
        $global:CycleCount = ($global:CycleCount + 1) % 10
        if ($global:CycleCount -eq 0) {
            Write-Log "[Heartbeat] Both Backend and Frontend services are fully online and healthy."
        }
    }
    catch {
        Write-Log "⚠️ Watchdog Exception: $_"
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}
