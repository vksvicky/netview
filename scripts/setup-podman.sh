#!/bin/bash

# Setup Podman for NetView monitoring
echo "🐳 Setting up Podman for NetView monitoring..."

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Installing via Homebrew..."
    brew install podman
fi

# Check if podman-compose is installed
if ! command -v podman-compose &> /dev/null; then
    echo "❌ podman-compose is not installed. Installing via pipx..."
    if ! command -v pipx &> /dev/null; then
        brew install pipx
        pipx ensurepath
    fi
    pipx install podman-compose
fi

# Initialize podman machine if it doesn't exist
if ! podman machine list | grep -q "podman-machine-default"; then
    echo "🔧 Initializing Podman machine..."
    podman machine init
fi

# Start podman machine if it's not running
if ! podman machine list | grep -q "Running"; then
    echo "🚀 Starting Podman machine..."
    podman machine start
fi

echo ""
echo "✅ Podman setup complete!"
echo ""
echo "🌐 To start monitoring with Podman:"
echo "   podman-compose -f config/podman-compose.yml up -d"
echo "   ./scripts/setup-grafana.sh"
echo "   ./scripts/import-dashboard.sh"
echo ""
echo "🔧 Podman machine status:"
podman machine list
