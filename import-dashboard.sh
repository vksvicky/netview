#!/bin/bash

# Import NetView dashboard into Grafana
echo "Importing NetView dashboard into Grafana..."

# Wait for Grafana to be ready
until curl -s http://localhost:3000/api/health > /dev/null; do
    echo "Waiting for Grafana..."
    sleep 2
done

echo "Importing dashboard..."

# Import the dashboard
curl -X POST \
  -H "Content-Type: application/json" \
  -d @netview-dashboard.json \
  http://admin:admin@localhost:3000/api/dashboards/db

echo ""
echo "✅ Dashboard imported successfully!"
echo ""
echo "🌐 Access your monitoring stack:"
echo "   • Grafana Dashboard: http://localhost:3000/d/netview-network-monitoring"
echo "   • Prometheus UI: http://localhost:9090"
echo "   • NetView Backend: http://localhost:8000"
echo "   • NetView UI: http://localhost:5170"
