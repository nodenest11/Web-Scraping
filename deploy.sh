#!/bin/bash

# DigitalOcean Deployment Script for Universal Web Scraping API

set -e

echo "🚀 DigitalOcean Deployment Script for Universal Web Scraping API"
echo "================================================================"

# Function to print colored output
print_status() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[1;34mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_info "Starting deployment process..."

# Create necessary directories
print_info "Creating directories..."
mkdir -p logs
mkdir -p /tmp/chrome-user-data
chmod 755 logs /tmp/chrome-user-data

# Stop existing containers if running
print_info "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Pull latest images
print_info "Pulling latest images..."
docker-compose pull nginx || true

# Build the application
print_info "Building Universal Web Scraping API..."
docker-compose build scraper-api

# Start the services
print_info "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 30

# Check health
print_info "Checking service health..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "API is healthy and running!"
        break
    else
        print_warning "Waiting for API to be ready... (attempt $i/10)"
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ API failed to start properly. Check logs:"
        echo "docker-compose logs scraper-api"
        exit 1
    fi
done

# Display status
echo ""
echo "🎉 Deployment Complete!"
echo "======================="
print_status "Universal Web Scraping API is running successfully!"
echo ""
echo "📡 API Endpoints:"
echo "   - Health Check: http://$(curl -s ipinfo.io/ip):8000/health"
echo "   - API Docs: http://$(curl -s ipinfo.io/ip):8000/docs"
echo "   - Status: http://$(curl -s ipinfo.io/ip):8000/status"
echo ""
echo "🔧 Management Commands:"
echo "   - View logs: docker-compose logs -f scraper-api"
echo "   - Restart: docker-compose restart scraper-api"
echo "   - Stop: docker-compose down"
echo "   - Update: docker-compose pull && docker-compose up -d"
echo ""
echo "📊 Monitor with:"
echo "   - docker-compose ps"
echo "   - docker stats"
echo ""
print_status "Your Universal Web Scraping API is ready for production use! 🚀"
