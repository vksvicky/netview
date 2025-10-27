#!/bin/bash

# NetView Frontend Run Script
# This script runs the frontend development server

clear

set -e  # Exit on any error

echo "🚀 Starting NetView Frontend..."

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
