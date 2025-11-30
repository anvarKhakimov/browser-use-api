# Multi-stage build for Browser-Use API Service
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    IN_DOCKER=true \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-liberation \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-liberation2 \
    fonts-thai-tlwg \
    fonts-indic \
    fontconfig \
    libappindicator3-1 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Copy dependency files first (for better caching)
COPY --chown=appuser:appuser pyproject.toml ./

# Install Python dependencies as root (for system packages)
USER root
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser docs ./docs

# Create necessary directories
RUN mkdir -p /app/logs /app/browser_data && \
    chown -R appuser:appuser /app/logs /app/browser_data

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]