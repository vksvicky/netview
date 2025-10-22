#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🐳 Starting NetView monitoring with Podman..."

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please run ./scripts/setup-podman.sh first"
    exit 1
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo "❌ podman-compose is not installed. Please run ./scripts/setup-podman.sh first"
    exit 1
fi

# Check if podman machine is running
if ! podman machine list | grep -q "Running"; then
    echo "🚀 Starting Podman machine..."
    podman machine start
fi

# Start the monitoring stack
echo "📊 Starting Prometheus and Grafana with Podman..."
cd "$PROJECT_ROOT"
podman-compose -f config/podman-compose.yml up -d

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
echo "✅ NetView monitoring stack started with Podman!"
echo ""
echo "🌐 Access your monitoring stack:"
echo "   • Prometheus UI: http://localhost:9090"
echo "   • Grafana UI: http://localhost:3000 (admin/admin)"
echo "   • NetView Dashboard: http://localhost:3000/d/netview-network-monitoring"
echo "   • NetView Backend: http://localhost:8000"
echo "   • NetView UI: http://localhost:5170"
echo ""
echo "🛑 To stop monitoring:"
echo "   podman-compose -f config/podman-compose.yml down"
