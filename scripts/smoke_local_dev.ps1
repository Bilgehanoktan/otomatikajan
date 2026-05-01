param(
    [string]$BackendOrigin = "http://127.0.0.1:8000",
    [string]$FrontendLocal = "http://localhost:3100",
    [string]$FrontendLoopback = "http://127.0.0.1:3100",
    [string]$FrontendStablePath = "/audit/",
    [string]$DispatchOrigin = "",
    [string]$Email = "admin@sovereign.agi",
    [string]$Password = "admin1234",
    [switch]$SkipWorkflowDispatch
)

$ErrorActionPreference = "Stop"
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

if ([string]::IsNullOrWhiteSpace($DispatchOrigin)) {
    $DispatchOrigin = $BackendOrigin
}

Write-Output "[smoke] canonical local topology: 3100 UI -> /api/v1 proxy, 8000 API/WS backend"
Write-Output ("[smoke] backend origin: {0}" -f $BackendOrigin)
Write-Output ("[smoke] dispatch origin: {0}" -f $DispatchOrigin)
Write-Output ("[smoke] frontend stable path: {0}" -f $FrontendStablePath)

function Invoke-SmokeJson {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [int]$Retries = 0
    )

    for ($attempt = 0; $attempt -le $Retries; $attempt++) {
        $params = @{
            Uri             = $Url
            Method          = $Method
            WebSession      = $session
            UseBasicParsing = $true
            TimeoutSec      = 12
            Headers         = @{ "Content-Type" = "application/json" }
        }

        if ($null -ne $Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 8)
        }

        try {
            $response = Invoke-WebRequest @params
            $payload = $null
            try {
                $payload = $response.Content | ConvertFrom-Json
            } catch {
                $payload = $response.Content
            }

            return [pscustomobject]@{
                Name   = $Name
                Status = $response.StatusCode
                Ok     = $true
                Data   = $payload
            }
        } catch {
            if ($attempt -lt $Retries) {
                Start-Sleep -Seconds ([Math]::Min(2 + $attempt, 4))
                continue
            }

            return [pscustomobject]@{
                Name   = $Name
                Status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
                Ok     = $false
                Data   = $_.Exception.Message
            }
        }
    }
}

$checks = @()
$checks += Invoke-SmokeJson -Name "backend.health" -Url "$BackendOrigin/health"
$checks += Invoke-SmokeJson -Name "backend.dashboard" -Url "$BackendOrigin/api/v1/health/dashboard"
$checks += Invoke-SmokeJson -Name "auth.login" -Url "$BackendOrigin/api/v1/auth/login" -Method "POST" -Body @{
    email    = $Email
    password = $Password
}
$checks += Invoke-SmokeJson -Name "auth.me" -Url "$BackendOrigin/api/v1/auth/me"
$checks += Invoke-SmokeJson -Name "workflow.summary" -Url "$BackendOrigin/api/v1/workflows/stats/summary"
$checks += Invoke-SmokeJson -Name "fleet.metrics" -Url "$BackendOrigin/api/v1/fleet/metrics"
$frontendLocalTarget = $FrontendLocal.TrimEnd("/") + $FrontendStablePath
$frontendLoopbackTarget = $FrontendLoopback.TrimEnd("/") + $FrontendStablePath
$checks += Invoke-SmokeJson -Name "frontend.localhost" -Url $frontendLocalTarget -Retries 2
$checks += Invoke-SmokeJson -Name "frontend.loopback" -Url $frontendLoopbackTarget -Retries 2

$checks | ForEach-Object {
    Write-Output ("[{0}] status={1} ok={2}" -f $_.Name, $_.Status, $_.Ok)
}

$failed = $checks | Where-Object { -not $_.Ok -or $_.Status -lt 200 -or $_.Status -ge 400 }
if ($failed) {
    Write-Output ""
    Write-Output "FAILED CHECKS:"
    $failed | ForEach-Object {
        Write-Output ("- {0}: {1}" -f $_.Name, $_.Data)
    }
    exit 1
}

if (-not $SkipWorkflowDispatch) {
    $loginData = ($checks | Where-Object { $_.Name -eq "auth.login" } | Select-Object -First 1).Data
    $dispatchHeaders = @{ "Content-Type" = "application/json" }
    if ($loginData -and $loginData.access_token) {
        $dispatchHeaders["Authorization"] = "Bearer $($loginData.access_token)"
    }

    if ($DispatchOrigin.TrimEnd("/") -ne $BackendOrigin.TrimEnd("/")) {
        try {
            $dispatchLogin = Invoke-WebRequest -UseBasicParsing -Uri "$DispatchOrigin/api/v1/auth/login/" -Method "POST" -WebSession $session -Headers @{ "Content-Type" = "application/json" } -Body ((@{
                email    = $Email
                password = $Password
            }) | ConvertTo-Json -Depth 8) -TimeoutSec 12
            $dispatchLoginData = $dispatchLogin.Content | ConvertFrom-Json
            if ($dispatchLoginData.access_token) {
                $dispatchHeaders["Authorization"] = "Bearer $($dispatchLoginData.access_token)"
            }
        } catch {
            Write-Output ("[dispatch.login] warning=" + $_.Exception.Message)
        }
    }

    $workflowName = "Smoke Workflow " + ([Guid]::NewGuid().ToString().Substring(0, 8))
    try {
        $workflowCreateResponse = Invoke-WebRequest -UseBasicParsing -Uri "$DispatchOrigin/api/v1/workflows/" -Method "POST" -WebSession $session -Headers $dispatchHeaders -Body ((@{
            title             = $workflowName
            description       = "Local smoke dispatch verification."
            workflow_template = "default"
            quality_profile   = "standard"
            priority          = "medium"
        }) | ConvertTo-Json -Depth 8) -TimeoutSec 12
        $workflowCreate = [pscustomobject]@{
            Name   = "workflow.create"
            Status = $workflowCreateResponse.StatusCode
            Ok     = $true
            Data   = ($workflowCreateResponse.Content | ConvertFrom-Json)
        }
    } catch {
        $workflowCreate = [pscustomobject]@{
            Name   = "workflow.create"
            Status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
            Ok     = $false
            Data   = $_.Exception.Message
        }
    }

    Write-Output ("[{0}] status={1} ok={2}" -f $workflowCreate.Name, $workflowCreate.Status, $workflowCreate.Ok)
    if (-not $workflowCreate.Ok -or $workflowCreate.Status -lt 200 -or $workflowCreate.Status -ge 400) {
        Write-Output ""
        Write-Output ("FAILED CHECKS:`n- {0}: {1}" -f $workflowCreate.Name, ($workflowCreate.Data | Out-String))
        exit 1
    }

    $createdId = $workflowCreate.Data.id
    $dispatchHealthy = $false
    for ($i = 1; $i -le 6; $i++) {
        Start-Sleep -Seconds 2
        try {
            $detailResponse = Invoke-WebRequest -UseBasicParsing -Uri "$DispatchOrigin/api/v1/workflows/$createdId/" -Method "GET" -WebSession $session -Headers $dispatchHeaders -TimeoutSec 12
            $detail = [pscustomobject]@{
                Name   = "workflow.detail"
                Status = $detailResponse.StatusCode
                Ok     = $true
                Data   = ($detailResponse.Content | ConvertFrom-Json)
            }
        } catch {
            $detail = [pscustomobject]@{
                Name   = "workflow.detail"
                Status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
                Ok     = $false
                Data   = $_.Exception.Message
            }
        }

        if (-not $detail.Ok -or $detail.Status -lt 200 -or $detail.Status -ge 400) {
            Write-Output ("[{0}] status={1} ok={2}" -f $detail.Name, $detail.Status, $detail.Ok)
            Write-Output ""
            Write-Output ("FAILED CHECKS:`n- {0}: {1}" -f $detail.Name, ($detail.Data | Out-String))
            exit 1
        }

        $stepCount = @($detail.Data.steps).Count
        $status = [string]$detail.Data.status
        Write-Output ("[workflow.dispatch] poll={0} status={1} steps={2}" -f $i, $status, $stepCount)

        if ($stepCount -gt 0 -or $status -in @("running", "completed", "failed", "waiting_approval", "pending_approval")) {
            $dispatchHealthy = $true
            break
        }
    }

    if (-not $dispatchHealthy) {
        Write-Output ""
        Write-Output "FAILED CHECKS:"
        Write-Output "- workflow.dispatch: newly created workflow stayed pending with 0 steps"
        exit 1
    }
}

Write-Output ""
Write-Output "Local smoke passed."
