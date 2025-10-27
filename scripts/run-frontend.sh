#!/bin/bash

# NetView Frontend Run Script
# This script runs the frontend development server

clear

set -e  # Exit on any error

echo "🚀 Starting NetView Frontend..."

# Kill any existing processes on port 5170 (Vite default)
echo "🔍 Checking for existing processes on port 5170..."
if lsof -ti:5170 >/dev/null 2>&1; then
    echo "⚠️  Found existing processes on port 5170. Killing them..."
    lsof -ti:5170 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo "✅ Port 5170 is now free"
else
    echo "✅ Port 5170 is available"
fi

# Also check for common Vite ports (5171, 5172, etc.)
for port in 5171 5172 5173; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "⚠️  Found existing processes on port $port. Killing them..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        echo "✅ Port $port is now free"
    fi
done

# Change to frontend directory
cd "$(dirname "$0")/../ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not installed. Please run build-frontend.sh first."
    exit 1
fi

# Start the development server
echo "🌐 Starting Vite development server on http://localhost:5170"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

npm run dev
