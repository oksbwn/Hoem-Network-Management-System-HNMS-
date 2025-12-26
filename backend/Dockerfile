FROM python:3.12-slim

# System deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap && \
    rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Install Python deps first (better cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app
COPY .env .env
COPY app/schema.sql app/schema.sql

# Expose API port
EXPOSE 8000

# Environment (override in docker-compose if needed)
ENV DB_PATH=/data/network_scanner.duckdb \
    DB_SCHEMA_PATH=app/schema.sql \
    DB_INIT_MODE=create

# Create volume mount point for DB
VOLUME ["/data"]

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
