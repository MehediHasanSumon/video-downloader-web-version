# ====================================================================
#  Universal Video Downloader Pro - Multi-Stage Production Dockerfile
# ====================================================================

# --------------------------------------------------------------------
# Stage 1: Build React 19 Frontend
# --------------------------------------------------------------------
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# --------------------------------------------------------------------
# Stage 2: Python Backend Runtime with FFmpeg
# --------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# Install system dependencies & official static FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY server/requirements.txt ./server/
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server code
COPY server/ ./server/

# Copy compiled frontend production assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create downloads and log directory
RUN mkdir -p /app/server/downloads

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    FILE_RETENTION_SECONDS=900

EXPOSE 5000

CMD ["python3", "server/main.py", "--host", "0.0.0.0", "--port", "5000", "--no-browser"]
