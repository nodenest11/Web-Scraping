#!/bin/bash

# Enhanced Cloud deployment startup script

echo "🚀 Starting Enhanced Universal Web Scraping API..."

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "📋 Loading configuration from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Set environment variables for cloud deployment
export ENVIRONMENT=${ENVIRONMENT:-production}
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Enhanced anti-detection settings
export USE_UNDETECTED_CHROME=${USE_UNDETECTED_CHROME:-true}

# Memory and performance optimizations for cloud
export NODE_OPTIONS="--max-old-space-size=4096"
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-/ms-playwright}

# Create necessary directories
mkdir -p /tmp/chrome-user-data
mkdir -p /tmp/playwright
chmod 755 /tmp/chrome-user-data /tmp/playwright 2>/dev/null || true

echo "🛡️ Enhanced Anti-Detection Mode: ${USE_UNDETECTED_CHROME}"
echo "🌐 Proxy Support: $([ -n "$PROXY_LIST" ] && echo "Enabled" || echo "Disabled")"

# Start the application with cloud-optimized settings
exec /home/kali/Desktop/CrawlAPI/.venv/bin/python -m uvicorn main:app \
    --host ${HOST:-0.0.0.0} \
    --port ${PORT:-8000} \
    --workers 1 \
    --timeout-keep-alive 65 \
    --access-log \
    --log-level ${LOG_LEVEL:-info}
