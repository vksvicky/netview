#!/bin/bash

# NetView Full Stack Test Script with Coverage
# This script runs both backend and frontend tests with coverage

set -e  # Exit on any error

echo "🧪 Running NetView Full Stack Tests with Coverage..."

# Get the directory of this script
SCRIPT_DIR="$(dirname "$0")"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Cleaning up..."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🔧 Running backend tests..."
"$SCRIPT_DIR/test-backend.sh"

echo ""
echo "🎨 Running frontend tests..."
"$SCRIPT_DIR/test-frontend.sh"

echo ""
echo "✅ All tests completed!"
echo ""
echo "📊 Coverage Reports:"
echo "  Backend: backend/htmlcov/index.html"
echo "  Frontend: ui/coverage/index.html"
echo ""
echo "📈 Test Summary:"
echo "  Backend tests: Check output above"
echo "  Frontend tests: Check output above"
