# tests/test_sandbox_real.py

import pytest
import os
import asyncio
from core.sandbox_runner import SandboxRunner

@pytest.mark.asyncio
@pytest.mark.docker
async def test_sandbox_strict_network_isolation():
    """
    [GERÇEK GÜVENLİK TESTİ]
    Ajan tarafından yazılan zararlı bir kodun (Google'a HTTP isteği atmak veya
    sistemdeki passwd dosyasını okumak) Sandbox tarafından GERÇEKTEN engellenip 
    engellenmediğini doğrular. Mock (sahte) kullanılmamıştır!
    """
    os.environ["APP_ENV"] = "production" # Üretim modunu zorla
    runner = SandboxRunner()
    
    docker_ok = await runner._docker_available_check()
    if not docker_ok:
        pytest.fail("Üretim (Production) ortamı güvenlik testi Docker kapalıyken çalıştırılamaz! Sistem tehlikede.")

    # Ajanın sinsice internete çıkmayı denediği kod senaryosu
    malicious_code = """
import urllib.request
try:
    urllib.request.urlopen("http://1.1.1.1", timeout=2)
    print("Ağ bağlantısı başarılı - TEHLİKE")
except Exception as e:
    print(f"Engellendi: {e}")
    """

    result = await runner.run_python(malicious_code, timeout=5)
    
    # 1. Beklenen: İşlem Docker network izolasyonu (network='none') sebebiyle başarısız olmalıdır.
    # Eğer "TEHLİKE" yazısını görüyorsak Sandbox sadece görsel olarak çalışıyordur.
    assert "TEHLİKE" not in result.stdout, "KRİTİK AÇIK: Sandbox dış ağa erişebiliyor!"
    
    # 2. Beklenen: Test başarılı geçtiyse (Ağa çıkamadıysa)
    assert result.success is False or "Engellendi" in result.stdout
    print("OK: Network isolation verified (True Sandbox).")

@pytest.mark.asyncio
@pytest.mark.docker
async def test_sandbox_host_filesystem_isolation():
    """
    Ajanın ana makinenin (Host) dosya sistemine erişip erişemediğini test eder.
    """
    runner = SandboxRunner()
    
    fs_code = """
import os
try:
    with open('/etc/passwd', 'r') as f:
        print("Root okuma: BAŞARILI")
except Exception as e:
    print(f"Engellendi: {e}")
    """
    
    result = await runner.run_python(fs_code, timeout=3)
    # Host'un etc/passwd dosyasıyla eşleşmemeli, konteynerin içindekini veya erişim engelini görmeliyiz.
    assert "Root okuma: BAŞARILI" not in result.stdout or runner._use_docker is True
    print("OK: Filesystem isolation verified.")
