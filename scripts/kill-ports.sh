#!/bin/bash

# NetView Port Management Script
# This script kills processes on specified ports

set -e  # Exit on any error

echo "🔧 NetView Port Management Tool"
echo ""

# Function to kill processes on a port
kill_port() {
    local port=$1
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "⚠️  Found processes on port $port:"
        lsof -ti:$port | while read pid; do
            ps -p $pid -o pid,ppid,command 2>/dev/null || true
        done
        echo "🔪 Killing processes on port $port..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        if lsof -ti:$port >/dev/null 2>&1; then
            echo "❌ Failed to kill all processes on port $port"
        else
            echo "✅ Port $port is now free"
        fi
    else
        echo "✅ Port $port is already free"
    fi
    echo ""
}

# If specific ports are provided as arguments
if [ $# -gt 0 ]; then
    for port in "$@"; do
        kill_port $port
    done
    exit 0
fi

# Default behavior: kill common NetView ports
echo "🔍 Checking common NetView ports..."

# Backend port
kill_port 8000

# Frontend ports (Vite commonly uses these)
for port in 5170 5171 5172 5173; do
    kill_port $port
done

echo "🎉 Port cleanup complete!"
echo ""
echo "Usage: $0 [port1] [port2] ..."
echo "Example: $0 8000 5170"
