#!/bin/bash

# NetView Backend Build Script
# This script builds the backend application

clear

set -e  # Exit on any error

echo "🚀 Building NetView Backend..."

# Change to backend directory
cd "$(dirname "$0")/../backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations (if any)
echo "🗄️  Running database setup..."
python -c "
from app.models import init_db
init_db()
print('Database initialized successfully')
"

# Check if the application can start
echo "✅ Testing application startup..."
python -c "
from app.main import app
print('Application imports successfully')
"

echo "🎉 Backend build completed successfully!"
echo ""
echo "To run the backend:"
echo "  ./scripts/run-backend.sh"
echo ""
echo "To run backend tests:"
echo "  ./scripts/test-backend.sh"
