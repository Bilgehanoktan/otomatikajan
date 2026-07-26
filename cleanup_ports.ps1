$ports = @(8000, 3100)
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Host "Port $port temizlendi."
    }
}
