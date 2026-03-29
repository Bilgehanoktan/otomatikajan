# ─── Aşama 1: Bağımlılık builder ─────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Sistem bağımlılıkları (derleme için)
RUN apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
    gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılıkları kur
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip --retries 5 \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt --retries 5


# ─── Aşama 2: Temel Çalışma Zamanı (Base Runtime) ────────
FROM python:3.12-slim AS base-runtime

# Güvenlik: root olmayan kullanıcı
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home appuser

WORKDIR /app
RUN chown appuser:appgroup /app

# Temel sistem kütüphaneleri (PostgreSQL istemcisi ve Curl)
RUN apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Builder'dan bağımlılıkları kopyala
COPY --from=builder /install /usr/local
COPY . .

# Temizlik
RUN rm -f .env .env.local *.zip *.pyc


# ─── Aşama 3: Üretim Slim (App & Beat için) ──────────────
FROM base-runtime AS production-slim
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", \
    "alembic upgrade head && \
     gunicorn main:app \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers ${WORKERS:-2} \
        --bind 0.0.0.0:8000 \
        --timeout 120 \
        --access-logfile -"]


# ─── Aşama 4: Üretim Worker (Full Browser Support) ───────
FROM base-runtime AS production-worker

# Root yetkisiyle tarayıcı ve Docker bağımlılıklarını kur
USER root
RUN apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
    docker.io \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Playwright browser'larını kur (Sadece worker için)
# Cache'i korumak için ayrı katman
RUN playwright install chromium

USER appuser
CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info", "--queues=critical,default,background", "--concurrency=2"]
