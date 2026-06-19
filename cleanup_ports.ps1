# Power-up Port Clean-up script for Sovereign AGI
$ports = @(8000, 8100, 3100)
foreach ($port in $ports) {
    Write-Host "[*] Checking port $port..."
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $pid = $conn.OwningProcess
            if ($pid -gt 0) {
                Write-Host "[!] Found process $pid listening on port $port. Terminating aggressively..."
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 200
            }
        }
    }
    
    # Second check (any state connection for complete cleanup)
    $allConns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($allConns) {
        $pids = $allConns | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $pids) {
            if ($pid -gt 0) {
                Write-Host "[!] Terminating related process $pid on port $port..."
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Write-Host "[OK] Port $port is clean."
}
