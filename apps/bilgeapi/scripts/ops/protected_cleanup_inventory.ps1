param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$protectedPatterns = @(
    '^\.env($|\.)',
    '\.db$',
    '\.db-shm$',
    '\.db-wal$',
    '\.log$',
    '^\.deer-flow[\\/]',
    '^runtime[\\/]data[\\/]',
    '^data[\\/].*\.db',
    '^agent_checkpoints\.db$',
    '^artifacts[\\/]',
    '^repair_outputs[\\/]'
)

$safeGeneratedPatterns = @(
    '(^|[\\/])__pycache__[\\/]',
    '\.pyc$',
    '^tmp[\\/]',
    '(^|[\\/])\.pytest_cache[\\/]',
    '^apps[\\/]refine_control_plane[\\/]\.next[\\/]',
    '^apps[\\/]refine_control_plane[\\/]\.playwright-browsers[\\/]'
)

$reviewArtifactPatterns = @(
    '^runtime[\\/]live-',
    '^repair_outputs[\\/]',
    '^artifacts[\\/]'
)

function Test-AnyPattern {
    param(
        [string]$Path,
        [string[]]$Patterns
    )
    foreach ($pattern in $Patterns) {
        if ($Path -match $pattern) {
            return $true
        }
    }
    return $false
}

$items = git status --short | ForEach-Object {
    $line = $_
    if ($line.Length -lt 4) {
        return
    }
    $status = $line.Substring(0, 2)
    $path = $line.Substring(3).Trim('"')
    $normalized = $path -replace '\\', '/'

    $classification = "SOURCE_OR_INTEGRATION"
    if (Test-AnyPattern -Path $normalized -Patterns $protectedPatterns) {
        $classification = "PROTECT_DATA"
    } elseif (Test-AnyPattern -Path $normalized -Patterns $safeGeneratedPatterns) {
        $classification = "SAFE_GENERATED"
    } elseif (Test-AnyPattern -Path $normalized -Patterns $reviewArtifactPatterns) {
        $classification = "REVIEW_ARTIFACT"
    }

    [PSCustomObject]@{
        status = $status
        path = $path
        classification = $classification
    }
}

$summary = $items | Group-Object classification | Sort-Object Name | ForEach-Object {
    [PSCustomObject]@{
        classification = $_.Name
        count = $_.Count
    }
}

$report = [PSCustomObject]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    repo_root = $repoRoot
    policy = "inventory_only_no_delete_no_move"
    summary = $summary
    items = $items
}

$json = $report | ConvertTo-Json -Depth 5

if ($OutputPath) {
    $resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
    $outputRoot = [System.IO.Path]::GetFullPath($resolvedOutput)
    if (-not $outputRoot.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "OutputPath must stay inside repo root: $OutputPath"
    }
    $parent = Split-Path -Parent $outputRoot
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $json | Set-Content -Path $outputRoot -Encoding UTF8
    Write-Output "WROTE $outputRoot"
} else {
    $json
}
