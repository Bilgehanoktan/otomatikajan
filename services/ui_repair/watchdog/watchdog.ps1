# ============================================
# Otonom AI Sistemi - Uyku Modu Watchdog
# ============================================
# Bu script sistemi izler ve uyku modundan sonra çökmüş servisleri otomatik kurtarır.
# Kullanım: powershell -ExecutionPolicy Bypass -File watchdog.ps1
# Task Scheduler ile bilgisayar açılışında/uyku sonrası otomatik çalıştırılabilir.

$ProjectDir = "E:\Otomasyon"
$VenvPython = "$ProjectDir\.venv\Scripts\python.exe"
$LogFile = "$ProjectDir\watchdog.log"
$CheckIntervalSeconds = 60

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "$timestamp - $Message"
    Add-Content -Path $LogFile -Value $entry
    Write-Host $entry
}

function Test-DockerRunning {
    try {
        $result = docker info 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Restart-CrashedContainers {
    Write-Log "Docker container durumları kontrol ediliyor..."
    
    # Restart döngüsünde olan container'ları tespit et
    $containers = docker ps -a --format "{{.Names}}:{{.Status}}" 2>&1
    foreach ($line in $containers) {
        if ($line -match "^(.+):(.+)$") {
            $name = $Matches[1]
            $status = $Matches[2]
            
            if ($status -match "Restarting|Exited") {
                Write-Log "⚠️ Sorunlu container tespit edildi: $name ($status)"
                
                # Backend özel durumu - rebuild gerekebilir
                if ($name -eq "otonom-api") {
                    Write-Log "🔄 Backend container yeniden başlatılıyor..."
                    docker-compose -f "$ProjectDir\docker-compose.yml" up -d backend 2>&1
                }
                else {
                    docker restart $name 2>&1
                }
                Write-Log "✅ $name yeniden başlatıldı"
            }
        }
    }
}

function Clean-StaleLocks {
    $lockFile = "$ProjectDir\bot.lock"
    if (Test-Path $lockFile) {
        # Lock dosyasi varsa ama bot calismiyorsa, stale lock
        $botRunning = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | 
        Where-Object { $_.CommandLine -like "*telegram_bot*" }
        
        if (-not $botRunning) {
            Remove-Item $lockFile -Force
            Write-Log "🧹 Stale bot.lock temizlendi"
        }
    }
}

function Start-LocalOrchestrator {
    # Yerel orchestrator calisiyor mu kontrol et
    $orchRunning = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | 
    Where-Object { $_.CommandLine -like "*orchestrator*" -or $_.CommandLine -like "*main:app*" }
    
    if (-not $orchRunning) {
        Write-Log "🚀 Yerel backend/orchestrator çalışmıyor, başlatılıyor..."
        
        # Önce backend API'yi başlat
        if (Test-Path $VenvPython) {
            Start-Process $VenvPython -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000" `
                -WorkingDirectory $ProjectDir -NoNewWindow `
                -RedirectStandardOutput "$ProjectDir\backend_local.log" `
                -RedirectStandardError "$ProjectDir\backend_local_err.log"
            Write-Log "✅ Backend API başlatıldı (port 8000)"
        }
        else {
            Write-Log "❌ Python venv bulunamadı: $VenvPython"
        }
    }
}

function Start-FortressSupervisor {
    # Supervisor calisiyor mu kontrol et
    $supRunning = Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | 
    Where-Object { $_.CommandLine -like "*fortress_supervisor*" }
    
    if (-not $supRunning) {
        Write-Log "[SUPERVISOR] Fortress Supervisor calismiyor, baslatiliyor..."
        
        if (Test-Path $VenvPython) {
            $supScript = "$ProjectDir\backend\services\fortress_supervisor\fortress_supervisor.py"
            if (Test-Path $supScript) {
                Start-Process $VenvPython -ArgumentList $supScript `
                    -WorkingDirectory $ProjectDir -NoNewWindow `
                    -RedirectStandardOutput "$ProjectDir\logs\supervisor_out.log" `
                    -RedirectStandardError "$ProjectDir\logs\supervisor_err.log"
                Write-Log "[OK] Fortress Supervisor baslatildi."
            }
            else {
                Write-Log "[ERROR] Supervisor scripti bulunamadi: $supScript"
            }
        }
        else {
            Write-Log "[ERROR] Python venv bulunamadi: $VenvPython"
        }
    }
}

# ============================================
# Ana Döngü
# ============================================

Write-Log "========================================="
Write-Log "🐕 Watchdog başlatıldı"
Write-Log "Kontrol aralığı: $CheckIntervalSeconds saniye"
Write-Log "========================================="

while ($true) {
    try {
        # 1. Stale lock'ları temizle
        Clean-StaleLocks
        
        # 2. Docker çalışıyorsa container'ları kontrol et
        if (Test-DockerRunning) {
            Restart-CrashedContainers
        }
        else {
            Write-Log "[DOCKER-ALERT] Docker Desktop calismiyor! Baslatilmaya calisiliyor..."
            $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            if (Test-Path $dockerExe) {
                Start-Process $dockerExe
                Write-Log "[DOCKER-START] Docker Desktop baslatma komutu gonderildi. 30 saniye bekleniyor..."
                Start-Sleep -Seconds 30
            }
            else {
                Write-Log "[ERROR] Docker Desktop yurutulebilir dosyasi bulunamadi: $dockerExe"
            }
        }

        # 3. Fortress Supervisor'ı kontrol et
        Start-FortressSupervisor
        
        Write-Log "[OK] Kontrol tamamlandi. Sonraki kontrol $CheckIntervalSeconds saniye sonra."
        
    }
    catch {
        Write-Log "!!! Watchdog hatasi: $_"
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}
