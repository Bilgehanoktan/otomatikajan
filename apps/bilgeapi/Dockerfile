FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project context
COPY . .

# Install package
RUN pip install -e .

EXPOSE 8100

# Run migrations and start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn bilgeapi.main:app --host 0.0.0.0 --port 8100"]
