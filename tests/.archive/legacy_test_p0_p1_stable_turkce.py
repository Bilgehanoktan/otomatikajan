"""
P0 ve P1 Düzeltmeleri Doğrulama Testi
------------------------------------
Bu test dosyası yapılan kritik düzeltmeleri (Backdrop Patch Set) doğrular.
1. Specialists endpoint (Zengin metadata)
2. Auth roles (Token içindeki roller)
3. Degrade mode visibility (X-System-Status header)
"""

import os
import sys
import asyncio
import pytest
from fastapi.testclient import TestClient

# Proje kök dizinini ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from apps.api.routers.apps.api.routers.auth.jwt_auth import get_current_user

# --- MOCK USER ---
class MockUser:
    def __init__(self, is_admin=False):
        self.id = "550e8400-e29b-41d4-a716-446655440000"
        self.email = "test@example.com"
        self.is_admin = is_admin
        self.is_active = True

def mock_get_current_user_admin():
    return MockUser(is_admin=True)

def mock_get_current_user_basic():
    return MockUser(is_admin=False)

# --- TESTLER ---

def test_specialists_endpoint_rich_metadata():
    """P1-02: Specialists endpoint'inin zengin metadata ve doğru ID döngüsü testi."""
    with TestClient(app) as client:
        # Auth override
        app.dependency_overrides[get_current_user] = mock_get_current_user_admin
        
        response = client.get("/api/v1/specialists")
        assert response.status_code == 200, "Specialists endpoint hata verdi"
        
        data = response.json()
        assert "specialists" in data, "Yanıt 'specialists' anahtarı içermeli"
        specs = data["specialists"]
        assert isinstance(specs, list), "Yanıt listesi 'specialists' anahtarı altında olmalı"
        assert len(specs) > 0, "En az bir uzman ajan bulunmalı"
        
        # İlk ajanı kontrol et
        agent = specs[0]
        assert "id" in agent, "Ajan ID eksik"
        assert "name" in agent, "Ajan adı eksik"
        assert "color" in agent, "Ajan rengi eksik (P1-02 fail)"
        assert "emoji" in agent, "Ajan emojisi eksik (P1-02 fail)"
        print("\n[OK] Specialists endpoint metadata doğruluğu onaylandı.")

def test_auth_me_roles_inclusion():
    """P1-04: /me endpoint'inde rollerin listelenmesi testi."""
    with TestClient(app) as client:
        # 1. Admin Testi
        app.dependency_overrides[get_current_user] = mock_get_current_user_admin
        response = client.get("/api/v1/auth/me")
        data = response.json()
        assert "roles" in data, "Roles alanı /me yanıtında eksik"
        assert "admin" in data["roles"], "Admin kullanıcısı admin rolüne sahip değil"
        
        # 2. Basic User Testi
        app.dependency_overrides[get_current_user] = mock_get_current_user_basic
        response = client.get("/api/v1/auth/me")
        data = response.json()
        assert "user" in data["roles"], "Normal kullanıcı user rolüne sahip değil"
        print("[OK] Auth roles (/me) doğruluğu onaylandı.")

def test_degrade_mode_visibility_headers():
    """P1-05: X-System-Status header'ının her yanıtta varlığı testi."""
    with TestClient(app) as client:
        app.dependency_overrides[get_current_user] = mock_get_current_user_admin
        
        response = client.get("/api/v1/specialists")
        assert "X-System-Status" in response.headers, "X-System-Status header'ı eksik (P1-05 fail)"
        status = response.headers["X-System-Status"]
        assert status in ["ok", "degraded"], f"Bilinmeyen sistem durumu: {status}"
        
        print(f"[OK] Sistem görünürlük başlığı (X-System-Status: {status}) aktif.")

if __name__ == "__main__":
    # Testleri sırayla çalıştır
    print("\n--- FAZ 12 P0/P1 STABİLİTE DOĞRULAMA ---")
    try:
        test_specialists_endpoint_rich_metadata()
        test_auth_me_roles_inclusion()
        test_degrade_mode_visibility_headers()
        print("\nSONUÇ: Tüm stabilite testleri BAŞARIYLA geçti.")
    except Exception as e:
        print(f"\n[HATA] Testler sırasında sorun oluştu: {e}")
        sys.exit(1)
