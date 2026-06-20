param(
    [ValidateSet('local', 'docker', 'auto')]
    [string]$Mode = 'auto',
    [int[]]$Ports = @(8000, 8100, 3100),
    [int]$MaxAttempts = 5,
    [int]$GraceMilliseconds = 400
)

$protectedProcessNames = @(
    "com.docker.backend",
    "wslrelay"
)

function Get-ListeningEntries {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    foreach ($connection in $connections) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        [pscustomobject]@{
            Port = $Port
            Pid = $connection.OwningProcess
            ProcessName = if ($process) { $process.ProcessName } else { "unknown" }
        }
    }
}

$busyPorts = @()

foreach ($port in $Ports) {
    Write-Host "[*] Checking port $port for $Mode mode..."

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $listeners = @(Get-ListeningEntries -Port $port)
        if (-not $listeners) {
            break
        }

        foreach ($listener in $listeners) {
            if ($protectedProcessNames -contains $listener.ProcessName) {
                Write-Host "[!] Port $port is held by protected process $($listener.ProcessName) (PID $($listener.Pid)); skipping force-kill."
                continue
            }

            if ($listener.Pid -gt 0) {
                Write-Host "[!] Attempt ${attempt}/${MaxAttempts}: stopping process tree $($listener.Pid) ($($listener.ProcessName)) on port $port..."
                cmd /c "taskkill /PID $($listener.Pid) /T /F >nul 2>&1"
            }
        }

        Start-Sleep -Milliseconds $GraceMilliseconds
    }

    $remainingListeners = @(Get-ListeningEntries -Port $port)
    if ($remainingListeners) {
        $busyPorts += $port
        foreach ($listener in $remainingListeners) {
            Write-Host "[!] Remaining listener on port $($port): PID=$($listener.Pid) NAME=$($listener.ProcessName)"
        }
        Write-Host "[HATA] Port $port is still busy after cleanup attempts."
        continue
    }

    Write-Host "[OK] Port $port is clean."
}

if ($busyPorts.Count -gt 0) {
    exit 1
}

exit 0
