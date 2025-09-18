# Production-ready Dockerfile for job matching batch processing system
FROM python:3.11-slim as base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    build-essential \
    libpq-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/logs /app/data/imports /app/data/exports \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Environment variables for the application
ENV APP_ENV=production \
    LOG_LEVEL=INFO \
    WORKERS=2 \
    HOST=0.0.0.0 \
    PORT=8000

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Default command for web service
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "120", "--keepalive", "2", "app.main:app"]

# Multi-stage build for batch processing
FROM base as batch-processor

# Additional dependencies for batch processing
RUN pip install --no-cache-dir \
    apscheduler==3.10.4 \
    prometheus-client==0.19.0

# Batch-specific environment variables
ENV BATCH_MODE=true \
    BATCH_MEMORY_LIMIT=1024 \
    BATCH_TIMEOUT=3600 \
    PROMETHEUS_PORT=8001

# Health check for batch processor
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=2 \
    CMD python -c "import requests; requests.get('http://localhost:8001/metrics')" || exit 1

# Batch process entry point
CMD ["python", "-m", "app.batch.scheduler"]

# Multi-stage build for monitoring
FROM base as monitoring

# Install additional monitoring dependencies
RUN pip install --no-cache-dir \
    grafana-api==1.0.3 \
    prometheus-client==0.19.0

# Monitoring-specific configuration
ENV MONITORING_MODE=true \
    METRICS_PORT=8002

EXPOSE ${METRICS_PORT}

CMD ["python", "-m", "app.monitoring.server"]