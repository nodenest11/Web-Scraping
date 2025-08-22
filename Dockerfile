FROM python:3.11-slim

# Environment variables for cloud deployment
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV USE_UNDETECTED_CHROME=true

# Install system dependencies for cloud deployment
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libnss3 \
    libxkbcommon0 \
    xvfb \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r scraper && useradd -r -g scraper -d /app -s /bin/bash scraper

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install chromium --with-deps

# Create directories with proper permissions
RUN mkdir -p /tmp/chrome-user-data /app/logs /tmp/playwright /ms-playwright && \
    chmod 755 /tmp/chrome-user-data /app/logs /tmp/playwright /ms-playwright && \
    chown -R scraper:scraper /app /tmp/chrome-user-data /tmp/playwright /ms-playwright

# Copy application code
COPY --chown=scraper:scraper . .

# Switch to non-root user
USER scraper

# Expose port
EXPOSE 8000

# Health check for DigitalOcean
HEALTHCHECK --interval=60s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["./start.sh"]
