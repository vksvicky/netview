#!/bin/bash

echo "🌐 Opening NetView Monitoring Stack..."
echo ""

# Check if services are running
echo "Checking services..."

if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is running"
else
    echo "❌ Grafana is not running - start with: docker-compose up -d"
    exit 1
fi

if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is running"
else
    echo "❌ Prometheus is not running - start with: docker-compose up -d"
    exit 1
fi

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ NetView Backend is running"
else
    echo "❌ NetView Backend is not running - start with: make backend"
    exit 1
fi

echo ""
echo "🚀 Opening monitoring interfaces..."

# Open Grafana dashboard
echo "Opening Grafana NetView Dashboard..."
open "http://localhost:3000/d/91e7c139-78a0-4581-a72d-18e99c09a0a0/netview-network-monitoring" 2>/dev/null || echo "Please open: http://localhost:3000/d/91e7c139-78a0-4581-a72d-18e99c09a0a0/netview-network-monitoring"

# Open Prometheus
echo "Opening Prometheus UI..."
open "http://localhost:9090" 2>/dev/null || echo "Please open: http://localhost:9090"

# Open NetView UI
echo "Opening NetView UI..."
open "http://localhost:5170" 2>/dev/null || echo "Please open: http://localhost:5170"

echo ""
echo "📊 Monitoring URLs:"
echo "   • Grafana Dashboard: http://localhost:3000/d/91e7c139-78a0-4581-a72d-18e99c09a0a0/netview-network-monitoring"
echo "   • Grafana Home: http://localhost:3000 (admin/admin)"
echo "   • Prometheus: http://localhost:9090"
echo "   • NetView UI: http://localhost:5170"
echo "   • NetView Backend: http://localhost:8000"
echo ""
echo "💡 If you see 'Dashboard not found', try:"
echo "   1. Go to http://localhost:3000"
echo "   2. Login with admin/admin"
echo "   3. Click 'Browse' in the left menu"
echo "   4. Look for 'NetView Network Monitoring'"
