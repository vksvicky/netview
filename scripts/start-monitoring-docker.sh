#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🐳 Starting NetView monitoring with Docker..."

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Desktop first"
    exit 1
fi

# Start the monitoring stack
echo "📊 Starting Prometheus and Grafana with Docker..."
cd "$PROJECT_ROOT"
docker-compose -f config/docker-compose.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Setup Grafana
echo "🔧 Setting up Grafana data source..."
"$SCRIPT_DIR/setup-grafana.sh"

# Import dashboard
echo "📈 Importing NetView dashboard..."
"$SCRIPT_DIR/import-dashboard.sh"

echo ""
echo "✅ NetView monitoring stack started with Docker!"
echo ""
echo "🌐 Access your monitoring stack:"
echo "   • Prometheus UI: http://localhost:9090"
echo "   • Grafana UI: http://localhost:3000 (admin/admin)"
echo "   • NetView Dashboard: http://localhost:3000/d/netview-network-monitoring"
echo "   • NetView Backend: http://localhost:8000"
echo "   • NetView UI: http://localhost:5170"
echo ""
echo "🛑 To stop monitoring:"
echo "   docker-compose -f config/docker-compose.yml down"
