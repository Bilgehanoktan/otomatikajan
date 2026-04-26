# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Makefile â€” AI YazÄ±lÄ±m Åirketi
# KullanÄ±m: make <hedef>
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

.PHONY: help install dev test test-cov lint format security docker-build \
        docker-up docker-down migrate celery clean secret

# VarsayÄ±lan: yardÄ±m
help:
	@echo ""
	@echo "  AI YazÄ±lÄ±m Åirketi â€” GeliÅŸtirici KomutlarÄ±"
	@echo "  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
	@echo "  make install      BaÄŸÄ±mlÄ±lÄ±klarÄ± yÃ¼kle (prod + dev)"
	@echo "  make dev          GeliÅŸtirme sunucusunu baÅŸlat (hot-reload)"
	@echo "  make test         Testleri Ã§alÄ±ÅŸtÄ±r"
	@echo "  make test-cov     Testleri kapsam raporu ile Ã§alÄ±ÅŸtÄ±r"
	@echo "  make lint         Ruff ile kod analizi"
	@echo "  make format       Ruff ile kod biÃ§imlendirme"
	@echo "  make security     Bandit + pip-audit gÃ¼venlik taramasÄ±"
	@echo "  make docker-build Docker imajÄ± oluÅŸtur"
	@echo "  make docker-up    Docker Compose ile servisleri baÅŸlat"
	@echo "  make docker-down  Docker Compose servislerini durdur"
	@echo "  make migrate      Alembic migrasyon uygula"
	@echo "  make celery       Celery worker baÅŸlat"
	@echo "  make secret       GÃ¼venli JWT_SECRET Ã¼ret"
	@echo "  make clean        GeÃ§ici dosyalarÄ± sil"
	@echo ""

# â”€â”€ Kurulum â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

# â”€â”€ GeliÅŸtirme â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
dev:
	uvicorn apps.public_api.main:app --reload --host 0.0.0.0 --port 8000 \
	    --log-level debug

# â”€â”€ Testler â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html:htmlcov

# â”€â”€ Kod Kalitesi â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
lint:
	ruff check . --show-source

format:
	ruff format .
	ruff check . --fix

# â”€â”€ GÃ¼venlik â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
security:
	@echo "=== Bandit GÃ¼venlik TaramasÄ± ==="
	bandit -r . -x tests,alembic -ll || true
	@echo ""
	@echo "=== pip-audit BaÄŸÄ±mlÄ±lÄ±k TaramasÄ± ==="
	pip-audit --require-hashes -r requirements.txt || true

# â”€â”€ Docker â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
docker-build:
	docker build --target production-slim -t ai-yazilim-sirketi:latest .

docker-up:
	docker compose up -d
	@echo "âœ… Servisler baÅŸlatÄ±ldÄ±: http://localhost:8000"
	@echo "   API docs: http://localhost:8000/docs"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f app worker

# â”€â”€ VeritabanÄ± â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
migrate:
	alembic upgrade head

migrate-create:
	@read -p "Migrasyon adÄ±: " name; \
	alembic revision --autogenerate -m "$$name"

migrate-rollback:
	alembic downgrade -1

# â”€â”€ Celery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
celery:
	celery -A workers.workflow_worker.tasks.celery_app worker \
	    --loglevel=info \
	    --queues=critical,default,background \
	    --concurrency=2

celery-beat:
	celery -A workers.workflow_worker.tasks.celery_app beat --loglevel=info

celery-monitor:
	celery -A workers.workflow_worker.tasks.celery_app events

# â”€â”€ YardÄ±mcÄ± â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
secret:
	@echo "Yeni JWT_SECRET (64 byte hex):"
	@python -c "import secrets; print(secrets.token_hex(64))"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "âœ… Temizlendi"

# â”€â”€ Faz 5: Ä°lk Kurulum â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "âœ… .env oluÅŸturuldu â€” dÃ¼zenleyin (JWT_SECRET, ADMIN_SECRET, API key)"; fi
	@echo "Sonraki adÄ±m: make create-admin"

create-admin:
	@python3 -c "\
import asyncio,os,sys; sys.path.insert(0,'.')\n\
async def main():\n\
    try:\n\
        from dotenv import load_dotenv; load_dotenv('.env',override=False)\n\
    except ImportError: pass\n\
    from libs.db.session import AsyncSessionLocal,init_db\n\
    from services.auth.jwt_auth import AuthService\n\
    from libs.db.models.auth_models import Operator\n\
    from sqlalchemy import update\n\
    await init_db()\n\
    email=input('Admin e-posta: ')\n\
    pw=input('Parola (min 8 karakter): ')\n\
    async with AsyncSessionLocal() as db:\n\
        try:\n\
            u=await AuthService().register(db,email,pw)\n\
            await db.execute(update(Operator).where(Operator.id==u.id).values(role='SOVEREIGN_PRIME'))\n\
            await db.commit()\n\
            print(f'âœ… Admin oluÅŸturuldu: {email}')\n\
        except Exception as e: print(f'Hata: {e}')\n\
async def run_it(): asyncio.run(main())\n\
run_it()"

run:
	uvicorn apps.public_api.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	gunicorn apps.public_api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
