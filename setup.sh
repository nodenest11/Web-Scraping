#!/bin/bash

# Enhanced Web Scraping API Setup Script
# =====================================

echo "🚀 Enhanced Web Scraping API Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_status "Python $python_version detected"
else
    print_error "Python 3.8+ required. Current version: $python_version"
    exit 1
fi

# Create virtual environment
print_info "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_info "Installing Python dependencies..."
pip install -r requirements.txt

# Install Chrome dependencies for undetected-chromedriver
print_info "Installing Chrome dependencies..."
if command -v apt-get >/dev/null 2>&1; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y wget gnupg
    
    # Add Google Chrome repository
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    
    # Install Google Chrome
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
    
    print_status "Chrome installed successfully"
elif command -v yum >/dev/null 2>&1; then
    # CentOS/RHEL
    sudo yum install -y wget
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    sudo yum localinstall -y google-chrome-stable_current_x86_64.rpm
    rm google-chrome-stable_current_x86_64.rpm
    
    print_status "Chrome installed successfully"
else
    print_warning "Could not auto-install Chrome. Please install Google Chrome manually."
fi

# Install Playwright browsers (fallback option)
print_info "Installing Playwright browsers..."
playwright install chromium

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Environment file created from template"
    print_info "Please edit .env file to configure your settings"
else
    print_warning ".env file already exists"
fi

# Make scripts executable
chmod +x start.sh
chmod +x deploy.sh

print_status "Setup completed successfully!"
echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. Edit .env file to configure your settings:"
echo "   nano .env"
echo ""
echo "2. To use Enhanced Undetected Chrome (recommended):"
echo "   Set USE_UNDETECTED_CHROME=true in .env"
echo ""
echo "3. Add your proxies to .env file (optional but recommended):"
echo "   PROXY_LIST=http://user:pass@proxy1.com:8080,http://proxy2.com:8080"
echo ""
echo "4. Start the API:"
echo "   ./start.sh"
echo "   # OR"
echo "   python main.py"
echo ""
echo "5. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "📚 Documentation:"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Full Guide: README.md"
echo "   - Endpoints: API_ENDPOINTS.md"
echo ""
print_status "Your Enhanced Web Scraping API is ready to use! 🚀"
