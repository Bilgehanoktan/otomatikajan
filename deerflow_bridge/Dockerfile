# ─── Aşama 1: Builder ─────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Sistem bağımlılıkları (derleme için)
RUN apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Pip güncellenmiş tut
RUN pip install --no-cache-dir --upgrade pip --retries 5

# Önce ağır bağımlılıkları yükle (Cache için ayrı katman)
RUN pip install --no-cache-dir --prefix=/install \
    numpy \
    pandas \
    onnxruntime \
    duckdb \
    packaging \
    --retries 5

# Bridge gereksinimlerini kopyala ve kur
COPY ./deerflow_bridge/requirements.txt /tmp/requirements.txt
RUN sed -i '/deer-flow/d' /tmp/requirements.txt && \
    pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt --retries 5

# Local harness paketini kopyala ve kur
COPY ./vendor/deer-flow/backend/packages/harness ./harness
RUN pip install --no-cache-dir --prefix=/install ./harness --retries 5


# ─── Aşama 2: Runtime ─────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Sadece gerekli sistem kütüphaneleri
RUN apt-get -o Acquire::Retries=3 update && apt-get -o Acquire::Retries=3 install -y \
    curl \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Default home directory
RUN mkdir -p /app/.deer-flow && chmod 777 /app/.deer-flow

# Builder'dan kurulan paketleri kopyala
COPY --from=builder /install /usr/local

# Bu modüller bridge tarafından kullanılır, bridge klasörünün dışında oldukları için açıkça kopyalanmalıdır.
COPY ./observability /app/observability
COPY ./core /app/core
COPY ./config.py /app/config.py
COPY ./schemas.py /app/schemas.py

# Bridge kodunu kopyala
COPY ./deerflow_bridge .

EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]
