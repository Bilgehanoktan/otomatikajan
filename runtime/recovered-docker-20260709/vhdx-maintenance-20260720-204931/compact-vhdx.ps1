$ErrorActionPreference = "Stop"

$vhdxPath = Join-Path $env:LOCALAPPDATA "Docker\wsl\disk\docker_data.vhdx"
$resultPath = "E:\ai_company_faz12.1\runtime\recovered-docker-20260709\vhdx-maintenance-20260720-204931\compact-result.json"
$startedAt = Get-Date
$beforeBytes = $null

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$identity
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "Optimize-VHD requires an elevated PowerShell process."
    }

    $runningDocker = Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessName -in @("Docker Desktop", "com.docker.backend", "com.docker.proxy") }
    if ($runningDocker) {
        throw "Docker Desktop backend processes are still running."
    }

    & wsl.exe --shutdown
    if ($LASTEXITCODE -ne 0) {
        throw "wsl --shutdown failed with exit code $LASTEXITCODE."
    }
    Start-Sleep -Seconds 3

    $stream = [System.IO.File]::Open(
        $vhdxPath,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
    $stream.Close()

    $beforeBytes = (Get-Item -LiteralPath $vhdxPath).Length
    Import-Module Hyper-V -ErrorAction Stop
    Optimize-VHD -Path $vhdxPath -Mode Full -ErrorAction Stop
    $afterBytes = (Get-Item -LiteralPath $vhdxPath).Length

    [ordered]@{
        status = "success"
        is_admin = $isAdmin
        path = $vhdxPath
        mode = "Full"
        before_bytes = $beforeBytes
        after_bytes = $afterBytes
        reclaimed_bytes = $beforeBytes - $afterBytes
        started_at = $startedAt.ToString("o")
        completed_at = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
    exit 0
}
catch {
    [ordered]@{
        status = "failed"
        path = $vhdxPath
        mode = "Full"
        before_bytes = $beforeBytes
        error = $_.Exception.Message
        started_at = $startedAt.ToString("o")
        completed_at = (Get-Date).ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding UTF8
    exit 1
}
