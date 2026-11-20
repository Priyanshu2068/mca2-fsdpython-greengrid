# ==============================================================================
# GreenGrid Multi-Stage Production Dockerfile
# Stage 1: Build React SPA Frontend
# Stage 2: Python 3.11+ Django REST Framework Backend + Serving
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:20-alpine AS frontend-builder
WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci --no-audit || npm install

COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Backend Image ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (netcat for DB healthcheck, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./backend/

# Copy compiled React frontend assets from Stage 1 into frontend/dist
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist/

# Copy default environment template
COPY .env.example .env

# Expose Django port
EXPOSE 8000

# Copy and set entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

# Run Gunicorn production WSGI server
CMD ["gunicorn", "--chdir", "backend", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]

