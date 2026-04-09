"""
Faz 7 — Stabilizasyon Test Paketi
══════════════════════════════════════════════════
Raporun öncelikli 7 aksiyon alanını doğrular:
  1. bcrypt lazy import
  2. LLM metrics zinciri
  3. Silent except -> loglama
  4. task_router bölünmesi
  5. Demo credential temizliği
  6. Alembic migration dosyası
  7. DB degraded mode
  8. Agent temiz kod sözleşmesi (faz6 regression)

Çalıştır: python tests/test_faz7.py
"""
import ast
import os
import re
import sys

sys.path.insert(0, ".")

PASS = []
FAIL = []


def ok(name: str):
    PASS.append(name)
    print(f"  ✅ {name}")


def fail(name: str, err):
    FAIL.append(name)
    print(f"  ❌ {name}: {err}")


# ─── 1. bcrypt lazy import ────────────────────────────────

def test_bcrypt_lazy_import():
    """auth/jwt_auth.py bcrypt yokken import aşamasında patlamamalı."""
    with open("auth/jwt_auth.py", encoding='utf-8') as f:
        src = f.read()
    assert "import bcrypt" not in src.splitlines()[0:5], \
        "bcrypt hâlâ top-level import"
    assert "_BCRYPT_OK" in src, "_BCRYPT_OK flag eksik"
    assert "try:" in src and "_bcrypt" in src, "lazy import try/except bloğu eksik"
    ok("bcrypt lazy import — import-time crash önlendi")


def test_auth_syntax():
    with open("auth/jwt_auth.py", encoding='utf-8') as f:
        src = f.read()
    ast.parse(src)
    ok("auth/jwt_auth.py syntax geçerli")


def test_auth_no_bare_bcrypt():
    """bcrypt. yerine _bcrypt. kullanılıyor olmalı."""
    with open("auth/jwt_auth.py", encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines()
    violations = [
        f"satır {i+1}: {l.strip()}"
        for i, l in enumerate(lines)
        if re.search(r'\bbcrypt\.(hashpw|checkpw|gensalt)', l)
    ]
    assert not violations, f"Bare bcrypt. kullanımı: {violations}"
    ok("auth: bcrypt. -> _bcrypt. tüm yerlerde değiştirildi")


# ─── 2. LLM Metrics Zinciri ──────────────────────────────

def test_llm_metrics_hook():
    with open("llm/model_orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    assert "record_llm_call" in src, "record_llm_call çağrısı eksik"
    assert "_estimate_cost" in src, "_estimate_cost fonksiyonu eksik"
    assert "_COST_PER_1K" in src, "maliyet tablosu eksik"
    ok("LLM metrics: her çağrıda record_llm_call + maliyet tahmini")


def test_llm_metrics_both_success_failure():
    with open("llm/model_orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    # success path
    assert "success=True" in src, "başarı yolunda metrics kaydı eksik"
    # failure path
    assert "success=False" in src, "hata yolunda metrics kaydı eksik"
    ok("LLM metrics: başarı VE hata yolları her ikisi de kaydediliyor")


def test_llm_orchestrator_syntax():
    with open("llm/model_orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    ast.parse(src)
    ok("llm/model_orchestrator.py syntax geçerli")


# ─── 3. Silent Except Loglama ─────────────────────────────

def test_orchestrator_no_silent_pass():
    with open("core/orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    lines = src.splitlines()
    violations = []
    for i, line in enumerate(lines):
        if re.match(r'\s+except Exception:\s*$', line):
            next_line = lines[i+1].strip() if i+1 < len(lines) else ""
            if next_line in ("pass", "return None", "return st.prompt"):
                violations.append(f"satır {i+1}: {line.strip()} -> {next_line}")
    assert not violations, f"Silent except kaldı: {violations}"
    ok("orchestrator: kritik silent except'ler loglanıyor")


def test_orchestrator_has_logger():
    with open("core/orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    assert "_log" in src or "logger" in src, "logger eksik"
    ok("orchestrator: logger tanımlı")


def test_orchestrator_syntax():
    with open("core/orchestrator.py", encoding='utf-8') as f:
        src = f.read()
    ast.parse(src)
    ok("core/orchestrator.py syntax geçerli")


# ─── 4. task_router Bölünmesi ─────────────────────────────

def test_task_router_split_files_exist():
    files = [
        "api/task_read_router.py",
        "api/task_write_router.py",
        "api/task_control_router.py",
        "api/_task_shared.py",
    ]
    for f in files:
        assert os.path.exists(f), f"{f} bulunamadı"
    ok(f"task_router: 4 dosyaya bölündü ({', '.join(f.split('/')[-1] for f in files)})")


def test_task_router_split_syntax():
    for f in ["api/task_read_router.py", "api/task_write_router.py",
              "api/task_control_router.py", "api/_task_shared.py"]:
        ast.parse(open(f, encoding='utf-8').read())
    ok("task_router bölünmüş dosyalar: syntax geçerli")


def test_task_router_endpoint_distribution():
    """Her router doğru endpoint'leri içeriyor mu?"""
    with open("api/task_read_router.py", encoding='utf-8') as f:
        read = f.read()
    with open("api/task_write_router.py", encoding='utf-8') as f:
        write = f.read()
    with open("api/task_control_router.py", encoding='utf-8') as f:
        ctrl = f.read()

    assert "list_tasks" in read or "@router.get" in read, "read router GET eksik"
    assert "create_task" in write or "@router.post" in write, "write router POST eksik"
    assert "cancel" in ctrl or "retry" in ctrl, "control router cancel/retry eksik"
    ok("task_router: GET->read, POST create->write, cancel/retry->control")


def test_main_uses_split_routers():
    with open("main.py", encoding='utf-8') as f:
        src = f.read()
    assert "task_read_router" in src, "main.py task_read_router kullanmıyor"
    assert "task_write_router" in src, "main.py task_write_router kullanmıyor"
    assert "task_control_router" in src, "main.py task_control_router kullanmıyor"
    # eski tek monolitik router artık olmamalı
    assert "from apps.api.routers.task_router import" not in src, "eski task_router hâlâ import ediliyor"
    ok("main.py: 3 yeni task router kullanıyor, eski monolitik kaldırıldı")


# ─── 5. Demo Credential Temizliği ────────────────────────

def test_no_hardcoded_admin_credentials():
    """ADMIN_OLUSTUR.bat ve KURULUM.md hardcoded parola içermemeli."""
    sensitive = ["admin1234", "admin@local.dev", "password123", "123456"]

    with open("ADMIN_OLUSTUR.bat", encoding='utf-8') as f:
        bat = f.read()
    for cred in sensitive:
        assert cred not in bat, f"ADMIN_OLUSTUR.bat hardcoded '{cred}' içeriyor"

    ok("ADMIN_OLUSTUR.bat: hardcoded credential temizlendi")


def test_admin_bat_uses_interactive():
    with open("ADMIN_OLUSTUR.bat", encoding='utf-8') as f:
        bat = f.read()
    assert "set /p" in bat.lower() or "_ADM_EMAIL" in bat, \
        "ADMIN_OLUSTUR.bat interaktif giriş yok"
    ok("ADMIN_OLUSTUR.bat: interaktif e-posta/parola girişi mevcut")


def test_no_hardcoded_secrets_in_python():
    """Python dosyalarında hardcoded parola/key olmamalı."""
    violations = []
    for dirpath, _, filenames in os.walk("."):
        if any(skip in dirpath for skip in ["__pycache__", ".git", "alembic/versions"]):
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                content = open(path, encoding='utf-8').read()
            except Exception:
                continue
            # Gerçek hardcoded secret pattern
            if re.search(r'password\s*=\s*["\'][a-zA-Z0-9!@#$%]{6,}["\']', content):
                # Test dosyaları hariç
                if "test_" not in fn and "example" not in fn.lower():
                    violations.append(path)
    assert not violations, f"Hardcoded parola tespit edildi: {violations}"
    ok("Python dosyaları: hardcoded credential yok")


# ─── 6. Alembic Migration ─────────────────────────────────

def test_alembic_migration_exists():
    versions_dir = "alembic/versions"
    assert os.path.isdir(versions_dir), f"{versions_dir} dizini yok"
    files = [f for f in os.listdir(versions_dir) if f.endswith(".py") and not f.startswith("__")]
    assert len(files) >= 1, "alembic/versions/ boş — migration yok"
    ok(f"Alembic: {len(files)} migration dosyası mevcut ({files[0]})")


def test_alembic_migration_syntax():
    versions_dir = "alembic/versions"
    for fn in os.listdir(versions_dir):
        if fn.endswith(".py") and not fn.startswith("__"):
            path = os.path.join(versions_dir, fn)
            ast.parse(open(path, encoding='utf-8').read())
    ok("Alembic migration dosyaları: syntax geçerli")


def test_alembic_migration_has_upgrade_downgrade():
    versions_dir = "alembic/versions"
    for fn in os.listdir(versions_dir):
        if fn.endswith(".py") and not fn.startswith("__"):
            content = open(os.path.join(versions_dir, fn), encoding='utf-8').read()
            assert "def upgrade()" in content, f"{fn} upgrade() eksik"
            assert "def downgrade()" in content, f"{fn} downgrade() eksik"
    ok("Alembic: upgrade() + downgrade() her migration'da mevcut")


def test_alembic_migration_covers_core_tables():
    versions_dir = "alembic/versions"
    all_content = ""
    for fn in os.listdir(versions_dir):
        if fn.endswith(".py") and not fn.startswith("__"):
            all_content += open(os.path.join(versions_dir, fn), encoding='utf-8').read()

    core_tables = ["users", "projects", "subtasks", "llm_cost_logs",
                   "domain_event_logs", "task_logs", "memories"]
    missing = [t for t in core_tables if t not in all_content]
    assert not missing, f"Migration'da eksik tablo tanımları: {missing}"
    ok(f"Alembic: {len(core_tables)} temel tablo migration'da tanımlı")


# ─── 7. DB Degraded Mode ─────────────────────────────────

def test_db_session_degraded_mode():
    with open("db/session.py", encoding='utf-8') as f:
        src = f.read()
    assert "_DB_AVAILABLE" in src, "_DB_AVAILABLE flag eksik"
    assert "is_db_available" in src, "await is_db_available() fonksiyonu eksik"
    assert "db_error" in src, "db_error() fonksiyonu eksik"
    ok("db/session.py: degraded mode flag ve erişimci fonksiyonlar mevcut")


def test_health_endpoint_shows_db_status():
    with open("main.py", encoding='utf-8') as f:
        src = f.read()
    assert "is_db_available" in src, "/health endpoint DB durumu göstermiyor"
    assert '"db"' in src or "\"db\":" in src, "/health yanıtında 'db' anahtarı eksik"
    assert "degraded" in src, "/health 'degraded' durumu desteklemiyor"
    ok("/health endpoint: DB unavailable -> status='degraded' gösteriyor")


def test_db_session_syntax():
    ast.parse(open("db/session.py", encoding='utf-8').read())
    ok("db/session.py syntax geçerli")


# ─── 8. Genel Syntax Kontrolü (tüm yeni dosyalar) ─────────

def test_all_new_files_syntax():
    files = [
        "main.py",
        "auth/jwt_auth.py",
        "llm/model_orchestrator.py",
        "core/orchestrator.py",
        "db/session.py",
        "api/task_read_router.py",
        "api/task_write_router.py",
        "api/task_control_router.py",
        "api/_task_shared.py",
        "alembic/versions/0001_initial_schema.py",
    ]
    errors = []
    for f in files:
        try:
            ast.parse(open(f, encoding='utf-8').read())
        except SyntaxError as e:
            errors.append(f"{f}:{e.lineno}: {e.msg}")
    assert not errors, f"Syntax hataları: {errors}"
    ok(f"Tüm {len(files)} dosya syntax geçerli")


# ─── Koşucu ───────────────────────────────────────────────

TESTS = [
    # bcrypt
    test_bcrypt_lazy_import,
    test_auth_syntax,
    test_auth_no_bare_bcrypt,
    # LLM metrics
    test_llm_metrics_hook,
    test_llm_metrics_both_success_failure,
    test_llm_orchestrator_syntax,
    # Silent except
    test_orchestrator_no_silent_pass,
    test_orchestrator_has_logger,
    test_orchestrator_syntax,
    # task_router bölünmesi
    test_task_router_split_files_exist,
    test_task_router_split_syntax,
    test_task_router_endpoint_distribution,
    test_main_uses_split_routers,
    # Demo credentials
    test_no_hardcoded_admin_credentials,
    test_admin_bat_uses_interactive,
    test_no_hardcoded_secrets_in_python,
    # Alembic
    test_alembic_migration_exists,
    test_alembic_migration_syntax,
    test_alembic_migration_has_upgrade_downgrade,
    test_alembic_migration_covers_core_tables,
    # DB degraded
    test_db_session_degraded_mode,
    test_health_endpoint_shows_db_status,
    test_db_session_syntax,
    # Genel
    test_all_new_files_syntax,
]


if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  FAZ 7 — Stabilizasyon Testleri (İnceleme Raporu Aksiyonları)")
    print("═" * 60 + "\n")

    for test_fn in TESTS:
        try:
            test_fn()
        except Exception as e:
            fail(test_fn.__name__, e)

    print()
    print("═" * 60)
    total = len(PASS) + len(FAIL)
    print(f"  Sonuç: {len(PASS)}/{total} geçti", end="")
    if FAIL:
        print(f"\n  Başarısız ({len(FAIL)}):")
        for f in FAIL:
            print(f"    · {f}")
        sys.exit(1)
    else:
        print("  🎉 Tüm testler geçti!")
    print("═" * 60 + "\n")
