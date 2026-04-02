# ─────────────────────────────────────────────────────────
# Makefile — AI Yazılım Şirketi
# Kullanım: make <hedef>
# ─────────────────────────────────────────────────────────

.PHONY: help install dev test test-cov lint format security docker-build \
        docker-up docker-down migrate celery clean secret

# Varsayılan: yardım
help:
	@echo ""
	@echo "  AI Yazılım Şirketi — Geliştirici Komutları"
	@echo "  ─────────────────────────────────────────"
	@echo "  make install      Bağımlılıkları yükle (prod + dev)"
	@echo "  make dev          Geliştirme sunucusunu başlat (hot-reload)"
	@echo "  make test         Testleri çalıştır"
	@echo "  make test-cov     Testleri kapsam raporu ile çalıştır"
	@echo "  make lint         Ruff ile kod analizi"
	@echo "  make format       Ruff ile kod biçimlendirme"
	@echo "  make security     Bandit + pip-audit güvenlik taraması"
	@echo "  make docker-build Docker imajı oluştur"
	@echo "  make docker-up    Docker Compose ile servisleri başlat"
	@echo "  make docker-down  Docker Compose servislerini durdur"
	@echo "  make migrate      Alembic migrasyon uygula"
	@echo "  make celery       Celery worker başlat"
	@echo "  make secret       Güvenli JWT_SECRET üret"
	@echo "  make clean        Geçici dosyaları sil"
	@echo ""

# ── Kurulum ────────────────────────────────────────────────
install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

# ── Geliştirme ─────────────────────────────────────────────
dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000 \
	    --log-level debug

# ── Testler ────────────────────────────────────────────────
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov

# ── Kod Kalitesi ───────────────────────────────────────────
lint:
	ruff check . --show-source

format:
	ruff format .
	ruff check . --fix

# ── Güvenlik ───────────────────────────────────────────────
security:
	@echo "=== Bandit Güvenlik Taraması ==="
	bandit -r . -x tests,alembic -ll || true
	@echo ""
	@echo "=== pip-audit Bağımlılık Taraması ==="
	pip-audit --require-hashes -r requirements.txt || true

# ── Docker ─────────────────────────────────────────────────
docker-build:
	docker build --target production-slim -t ai-yazilim-sirketi:latest .

docker-up:
	docker compose up -d
	@echo "✅ Servisler başlatıldı: http://localhost:8000"
	@echo "   API docs: http://localhost:8000/docs"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f app worker

# ── Veritabanı ─────────────────────────────────────────────
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migrasyon adı: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-rollback:
	alembic downgrade -1

# ── Celery ─────────────────────────────────────────────────
celery:
	celery -A tasks.celery_app worker \
	    --loglevel=info \
	    --queues=critical,default,background \
	    --concurrency=2

celery-beat:
	celery -A tasks.celery_app beat --loglevel=info

celery-monitor:
	celery -A tasks.celery_app events

# ── Yardımcı ───────────────────────────────────────────────
secret:
	@echo "Yeni JWT_SECRET (64 byte hex):"
	@python -c "import secrets; print(secrets.token_hex(64))"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Temizlendi"

# ── Faz 5: İlk Kurulum ─────────────────────────────────────
setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "✅ .env oluşturuldu — düzenleyin (JWT_SECRET, ADMIN_SECRET, API key)"; fi
	@echo "Sonraki adım: make create-admin"

create-admin:
	@python3 -c "\
import asyncio,os,sys; sys.path.insert(0,'.')\n\
async def main():\n\
    try:\n\
        from dotenv import load_dotenv; load_dotenv('.env',override=False)\n\
    except ImportError: pass\n\
    from db.session import AsyncSessionLocal,init_db\n\
    from auth.jwt_auth import AuthService\n\
    from db.models import User\n\
    from sqlalchemy import update\n\
    await init_db()\n\
    email=input('Admin e-posta: ')\n\
    pw=input('Parola (min 8 karakter): ')\n\
    async with AsyncSessionLocal() as db:\n\
        try:\n\
            u=await AuthService().register(db,email,pw)\n\
            await db.execute(update(User).where(User.id==u.id).values(is_admin=True))\n\
            await db.commit()\n\
            print(f'✅ Admin oluşturuldu: {email}')\n\
        except Exception as e: print(f'Hata: {e}')\n\
asyncio.run(main())"

run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
