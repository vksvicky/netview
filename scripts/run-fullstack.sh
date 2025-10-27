#!/bin/bash

# NetView Full Stack Run Script
# This script runs both backend and frontend servers

clear

set -e  # Exit on any error

echo "🚀 Starting NetView Full Stack..."

# Get the directory of this script
SCRIPT_DIR="$(dirname "$0")"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "🔧 Starting backend server..."
"$SCRIPT_DIR/run-backend.sh" &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🎨 Starting frontend server..."
"$SCRIPT_DIR/run-frontend.sh" &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers are starting..."
echo "🌐 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:5170"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop both servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
