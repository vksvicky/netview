#!/bin/bash

# NetView Backend Test Script with Coverage
# This script runs backend tests with coverage reporting

clear

set -e  # Exit on any error

echo "🧪 Running NetView Backend Tests with Coverage..."

# Change to backend directory
cd "$(dirname "$0")/../backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run build-backend.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install coverage if not already installed
if ! python -c "import coverage" 2>/dev/null; then
    echo "📥 Installing coverage..."
    pip install coverage
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run tests with coverage
echo "🔍 Running tests with coverage..."
coverage run -m pytest tests/ -v

# Generate coverage report
echo "📊 Generating coverage report..."
coverage report

# Generate HTML coverage report
echo "📄 Generating HTML coverage report..."
coverage html

echo ""
echo "✅ Backend tests completed!"
echo "📊 Coverage report: backend/htmlcov/index.html"
echo "📈 Coverage summary displayed above"
