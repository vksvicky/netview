#!/bin/bash

# NetView Frontend Build Script
# This script builds the frontend application

clear

set -e  # Exit on any error

echo "🚀 Building NetView Frontend..."

# Change to frontend directory
cd "$(dirname "$0")/../ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "📥 Updating dependencies..."
    npm install
fi

# Build the application
echo "🔨 Building application..."
npm run build

# Check if build was successful
if [ -d "dist" ]; then
    echo "✅ Build completed successfully!"
    echo "📁 Build output: ui/dist/"
    echo ""
    echo "To preview the build:"
    echo "  ./scripts/run-frontend.sh"
    echo ""
    echo "To run frontend tests:"
    echo "  ./scripts/test-frontend.sh"
else
    echo "❌ Build failed!"
    exit 1
fi
