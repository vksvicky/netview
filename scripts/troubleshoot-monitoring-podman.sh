#!/bin/bash

echo "🔍 NetView Monitoring Troubleshooting (Podman)"
echo "=============================================="
echo ""

# Check if services are running
echo "1. Checking service status..."

# Check NetView Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ NetView Backend (port 8000): Running"
else
    echo "❌ NetView Backend (port 8000): Not running"
    echo "   Start with: make backend"
fi

# Check Podman machine
if podman machine list | grep -q "Running"; then
    echo "✅ Podman Machine: Running"
else
    echo "❌ Podman Machine: Not running"
    echo "   Start with: podman machine start"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus (port 9090): Running"
else
    echo "❌ Prometheus (port 9090): Not running"
    echo "   Start with: podman-compose -f config/podman-compose.yml up -d"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana (port 3000): Running"
else
    echo "❌ Grafana (port 3000): Not running"
    echo "   Start with: podman-compose -f config/podman-compose.yml up -d"
fi

echo ""
echo "2. Testing Prometheus connectivity..."

# Test Prometheus targets
TARGETS=$(curl -s "http://localhost:9090/api/v1/targets" | jq '.data.activeTargets | length' 2>/dev/null)
if [ "$TARGETS" -gt 0 ]; then
    echo "✅ Prometheus has $TARGETS active targets"
    echo "   Targets:"
    curl -s "http://localhost:9090/api/v1/targets" | jq -r '.data.activeTargets[] | "   - \(.labels.job): \(.health)"' 2>/dev/null
else
    echo "❌ Prometheus has no active targets"
fi

# Test NetView metrics
METRICS=$(curl -s "http://localhost:9090/api/v1/query?query=netview_http_requests_total" | jq '.data.result | length' 2>/dev/null)
if [ "$METRICS" -gt 0 ]; then
    echo "✅ NetView metrics available: $METRICS metrics"
else
    echo "❌ No NetView metrics found"
fi

echo ""
echo "3. Testing Grafana connectivity..."

# Check Grafana data sources
DATASOURCES=$(curl -s "http://admin:admin@localhost:3000/api/datasources" | jq 'length' 2>/dev/null)
if [ "$DATASOURCES" -gt 0 ]; then
    echo "✅ Grafana has $DATASOURCES data source(s)"
    curl -s "http://admin:admin@localhost:3000/api/datasources" | jq -r '.[] | "   - \(.name) (\(.type)): \(.url)"' 2>/dev/null
else
    echo "❌ No Grafana data sources configured"
fi

# Check Grafana dashboards
DASHBOARDS=$(curl -s "http://admin:admin@localhost:3000/api/search?query=netview" | jq 'length' 2>/dev/null)
if [ "$DASHBOARDS" -gt 0 ]; then
    echo "✅ Grafana has $DASHBOARDS NetView dashboard(s)"
    curl -s "http://admin:admin@localhost:3000/api/search?query=netview" | jq -r '.[] | "   - \(.title): \(.url)"' 2>/dev/null
else
    echo "❌ No NetView dashboards found"
fi

echo ""
echo "4. Correct URLs to access:"
echo "   🌐 Prometheus UI: http://localhost:9090"
echo "   🌐 Grafana UI: http://localhost:3000 (admin/admin)"
echo "   🌐 NetView Dashboard: http://localhost:3000/d/91e7c139-78a0-4581-a72d-18e99c09a0a0/netview-network-monitoring"
echo "   🌐 NetView Backend: http://localhost:8000"
echo "   🌐 NetView UI: http://localhost:5170"

echo ""
echo "5. If you see blank screens:"
echo "   • Try refreshing the page (Cmd+R or Ctrl+R)"
echo "   • Check browser console for errors (F12)"
echo "   • Try incognito/private browsing mode"
echo "   • Clear browser cache"
echo "   • Try a different browser"

echo ""
echo "6. Quick fixes:"
echo "   • Restart monitoring: podman-compose -f config/podman-compose.yml down && podman-compose -f config/podman-compose.yml up -d"
echo "   • Re-setup Grafana: ./scripts/setup-grafana.sh"
echo "   • Re-import dashboard: ./scripts/import-dashboard.sh"
echo "   • Restart Podman machine: podman machine stop && podman machine start"
