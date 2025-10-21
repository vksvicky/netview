#!/bin/bash

# Setup Grafana to connect to Prometheus
echo "Setting up Grafana data source..."

# Wait for Grafana to be ready
echo "Waiting for Grafana to be ready..."
until curl -s http://localhost:3000/api/health > /dev/null; do
    echo "Waiting for Grafana..."
    sleep 2
done

echo "Grafana is ready! Setting up Prometheus data source..."

# Create Prometheus data source
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://host.docker.internal:9090",
    "access": "proxy",
    "isDefault": true,
    "jsonData": {
      "httpMethod": "POST"
    }
  }' \
  http://admin:admin@localhost:3000/api/datasources

echo ""
echo "✅ Grafana setup complete!"
echo ""
echo "🌐 Access your monitoring stack:"
echo "   • Prometheus UI: http://localhost:9090"
echo "   • Grafana UI: http://localhost:3000 (admin/admin)"
echo "   • NetView Backend: http://localhost:8000"
echo "   • NetView UI: http://localhost:5170"
echo ""
echo "📊 Try these Prometheus queries in Grafana:"
echo "   • netview_http_requests_total"
echo "   • rate(netview_http_requests_total[5m])"
echo "   • netview_discovered_devices_total"
