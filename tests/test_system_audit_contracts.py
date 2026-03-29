import os
import pytest

def test_no_secrets_in_repo():
    """P0-1: .env dosyasında gerçek API anahtarı olmamalı (placeholder OK)"""
    env_path = os.path.join(".", ".env")
    if not os.path.exists(env_path):
        return  # Dosya yoksa test geçer
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Gerçek API key kalıplarını kontrol et
    real_key_patterns = ["sk-proj-", "sk-or-v1-", "gsk_", "AIzaSy", "sk-api-"]
    found = [p for p in real_key_patterns if p in content]
    assert not found, f".env dosyasında gerçek API anahtarı kalıpları bulundu: {found}"

def test_docker_compose_worker_env():
    """P1-4: worker servisi .env.local kullanmali"""
    if not os.path.exists("docker-compose.yml"):
        pytest.skip("docker-compose.yml yok")
    with open("docker-compose.yml", "r", encoding="utf-8") as f:
        content = f.read()
    # P1-4: worker: servisi icinde env_file: .env.local olmali
    assert ".env.local" in content

def test_observer_status_error():
    """P1-1: Observer 'error' statusunu taramali"""
    if not os.path.exists("improve/observer.py"):
        pytest.skip("improve/observer.py yok")
    with open("improve/observer.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert 'status="error"' in content
    assert 'limit=50' in content

def test_dashboard_auth_bearer_removal():
    """P1-3: Dashboard code gen kisminda Authorization: Bearer kaldirilmis olmali"""
    if not os.path.exists("dashboard/index.html"):
        pytest.skip("dashboard/index.html yok")
    with open("dashboard/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Code generation fonksiyonlarini bul
    lines = content.split("\n")
    code_gen_start = -1
    for i, line in enumerate(lines):
        if "function viewCodeFile" in line:
            code_gen_start = i
            break
            
    if code_gen_start != -1:
        # Sonraki 100 satirda Bearer token aramasi yap
        chunk = "\n".join(lines[code_gen_start:code_gen_start+100])
        assert "Authorization': `Bearer" not in chunk, "viewCodeFile icinde hala Bearer token bulundu!"

def test_improvement_router_mounted():
    """P1-5: improvement_router startup/routers.py icinde kayitli mi?"""
    # Modülerleştirme sonrası router kaydı startup/routers.py'de
    router_file = os.path.join("startup", "routers.py")
    if not os.path.exists(router_file):
        # Eski yapıda main.py'de olabilir
        router_file = "main.py"
    if not os.path.exists(router_file):
        pytest.skip("Router dosyası bulunamadı")
    with open(router_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "improvement_router" in content
    assert "include_router(improvement_router" in content
