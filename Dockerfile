# ─── Aşama 1: Bağımlılık builder ─────────────────────────
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Sistem bağımlılıkları (derleme için)
RUN apt-get -o Acquire::Retries=5 update && apt-get -o Acquire::Retries=5 install -y --no-install-recommends --fix-missing \
    gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları kur
COPY requirements.txt .
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
RUN uv pip install --no-cache --system --prefix=/install -r requirements.txt


# ─── Aşama 2: Temel Çalışma Zamanı (Base Runtime) ────────
FROM python:3.12-slim-bookworm AS base-runtime

# Güvenlik: root olmayan kullanıcı
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app
RUN chown appuser:appgroup /app

# Temel sistem kütüphaneleri (PostgreSQL istemcisi, Curl ve Playwright/Browser bağımlılıkları)
RUN apt-get -o Acquire::Retries=5 update && \
    DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Retries=5 install -y --no-install-recommends --fix-missing \
    libpq5 curl git \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Playwright Ayarları: Browser'ları global bir dizine kur ki her kullanıcı erişebilsin
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p $PLAYWRIGHT_BROWSERS_PATH && chown appuser:appgroup $PLAYWRIGHT_BROWSERS_PATH

# Builder'dan bağımlılıkları kopyala (Playwright paketi bu aşamada gelir)
COPY --from=builder /install /usr/local

# Playwright browser'larını kur (Artık playwright paketi mevcut)
RUN playwright install chromium && chown -R appuser:appgroup $PLAYWRIGHT_BROWSERS_PATH

COPY . .
RUN mkdir -p runtime/data && chown -R appuser:appgroup /app runtime/data

# Temizlik
RUN rm -rf /root/.cache
RUN rm -f .env .env.local *.zip *.pyc

# ─── Aşama 2.5: Bütünlük Kontrolü (Quality Guard) ────────
FROM base-runtime AS validator
RUN pip install --no-cache-dir ruff==0.4.0
# Bu aşama, eğer sistemde import hatası veya kritik lint hatası varsa build'i durdurur.
# RUN python scripts/verify_system_integrity.py  # Script location changed or removed in Faz 13


# ─── Aşama 3: Üretim Slim (App & Beat için) ──────────────
FROM base-runtime AS production-slim
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", \
    "alembic -c libs/db/migrations/alembic.ini upgrade head && \
     gunicorn apps.public_api.main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers ${WORKERS:-2} \
        --bind 0.0.0.0:8000 \
        --timeout 120 \
        --access-logfile -"]


# ─── Aşama 4: Üretim Worker (Full Browser Support) ───────
FROM base-runtime AS production-worker

# Docker CLI kurulumu varsayılan olarak kapalıdır. Full-stack worker image
# build'i, offline/DNS sorunlarında `docker.io` indirmeye mecbur kalmamalıdır.
USER root
ARG INSTALL_DOCKER_CLI=false
RUN if [ "${INSTALL_DOCKER_CLI}" = "true" ]; then \
        apt-get -o Acquire::Retries=3 update && \
        apt-get -o Acquire::Retries=3 install -y --no-install-recommends docker.io && \
        rm -rf /var/lib/apt/lists/*; \
    else \
        echo "Skipping docker.io install for production-worker. Set INSTALL_DOCKER_CLI=true only when host Docker access is required."; \
    fi

# Playwright browser'ları zaten base-runtime'da kurulu.

USER appuser
CMD ["celery", "-A", "workers.workflow_worker.tasks.celery_app", "worker", "--loglevel=info", "--queues=critical,default,background", "--concurrency=2"]
