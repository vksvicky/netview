# NetView - Local Network Monitoring and Topology Visualization

A web-based local network monitoring tool that discovers network devices via SNMP and visualizes the topology using interactive graphs.

## Features

- **Network Discovery**: SNMP v2c/v3 discovery using LLDP-MIB, BRIDGE-MIB, IF-MIB, Q-BRIDGE-MIB
- **Topology Visualization**: Interactive network graph with vis-network
- **Real-time Monitoring**: Interface counters, errors, discards with Prometheus metrics
- **Device Management**: Search, filter, and inspect devices and interfaces
- **REST API**: Full API for integration with external tools
- **TDD/BDD**: Comprehensive test coverage with pytest 8.4.2 and vitest 3.2.4

## Architecture

- **Backend**: Python 3.11+, FastAPI 0.119.1, SQLAlchemy 2.0.44 (SQLite), APScheduler 3.11.0, Prometheus Client 0.23.1
- **Frontend**: React 19.2.0, Vite 7.1.11, vis-network 10.0.2 for graph visualization
- **Time Series**: Prometheus scrape endpoint (VictoriaMetrics recommended)
- **Discovery**: SNMP polling with fallback to ARP tables and CDP

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (tested with Node.js 20+)
- Network access to SNMP-enabled devices

### Installation

1. **Clone and setup backend:**
   ```bash
   git clone <repository>
   cd netview
   make venv
   ```

2. **Setup frontend:**
   ```bash
   cd ui
   npm install
   cd ..
   ```

### Running the Application

1. **Start backend (Terminal 1):**
   ```bash
   make backend
   ```
   - API available at: http://localhost:8000
   - Prometheus metrics: http://localhost:8000/metrics
   - API docs: http://localhost:8000/docs

2. **Start frontend (Terminal 2):**
   ```bash
   make ui
   ```
   - UI available at: http://localhost:5170

3. **Start Prometheus monitoring (Optional - Terminal 3):**
   ```bash
   docker-compose -f config/docker-compose.yml up -d
   ./scripts/setup-grafana.sh
   ./scripts/import-dashboard.sh
   ```
   - Prometheus UI: http://localhost:9090
   - Grafana UI: http://localhost:3000 (admin/admin)
   - NetView Dashboard: http://localhost:3000/d/netview-network-monitoring

### Monitoring Tools

**Quick diagnostics:**
```bash
./scripts/troubleshoot-monitoring.sh  # Complete service diagnostics
./scripts/open-monitoring.sh         # Open all monitoring URLs
open scripts/monitoring-test.html    # Browser-based connectivity test
```

### Testing

**Backend tests:**
```bash
make test
```

**Frontend tests:**
```bash
cd ui && npm test
```

## Configuration

### Environment Variables

```bash
# Optional Basic Auth
export NETVIEW_BASIC_AUTH_ENABLED=true
export NETVIEW_BASIC_AUTH_USERNAME=admin
export NETVIEW_BASIC_AUTH_PASSWORD=secret

# Polling intervals (seconds)
export NETVIEW_DISCOVERY_INTERVAL_SEC=300  # 5 minutes
export NETVIEW_POLLING_INTERVAL_SEC=60     # 1 minute
```

### SNMP Configuration

Configure SNMP community strings and credentials in the discovery service:
- Default: SNMP v2c with community "public"
- Support for SNMP v3 with authentication and privacy

## API Endpoints

- `GET /topology` - Network topology graph (nodes/edges)
- `POST /topology/discover` - Trigger manual discovery
- `GET /devices` - List all discovered devices
- `GET /devices/{id}` - Get device details
- `GET /interfaces` - List all interfaces
- `GET /interfaces/{device_id}` - List device interfaces
- `GET /interfaces/{device_id}/{if_index}` - Get interface details
- `GET /metrics/{device_id}/{if_index}` - Get interface metrics (JSON)
- `GET /metrics` - Prometheus metrics endpoint
- `GET /alerts` - List active alerts

## Data Model

**Devices:**
- id, hostname, mgmt_ip, vendor, model, status, last_seen

**Interfaces:**
- id, device_id, if_index, name, speed, mac, admin_status, oper_status, last_counters

**Edges:**
- id, src_device_id, src_if_index, dst_device_id, dst_if_index, link_type, vlan_tags, confidence

## Current Library Versions

### Backend Dependencies
- **FastAPI**: 0.119.1 - Modern, fast web framework for building APIs
- **Uvicorn**: 0.38.0 - ASGI server for FastAPI
- **SQLAlchemy**: 2.0.44 - SQL toolkit and ORM
- **APScheduler**: 3.11.0 - Advanced Python Scheduler
- **Prometheus Client**: 0.23.1 - Prometheus metrics client
- **Pydantic**: 2.12.3 - Data validation using Python type annotations
- **pytest**: 8.4.2 - Testing framework
- **httpx**: 0.28.1 - HTTP client for testing

### Frontend Dependencies
- **React**: 19.2.0 - UI library
- **Vite**: 7.1.11 - Build tool and dev server
- **vis-network**: 10.0.2 - Network visualization library
- **vitest**: 3.2.4 - Testing framework
- **TypeScript**: Latest - Type safety and development experience

## Development

### Project Structure

```
netview/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   └── metrics.py       # Prometheus metrics
│   ├── tests/               # Backend tests
│   └── requirements.txt
├── ui/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── api.ts           # API client
│   │   └── App.test.tsx     # UI tests
│   └── package.json
├── config/                  # Configuration files
│   ├── docker-compose.yml   # Prometheus & Grafana setup
│   ├── prometheus.yml       # Prometheus configuration
│   └── netview-dashboard.json # Grafana dashboard
├── scripts/                 # Utility scripts
│   ├── setup-grafana.sh    # Grafana data source setup
│   ├── import-dashboard.sh # Dashboard import
│   ├── open-monitoring.sh  # Open monitoring URLs
│   ├── troubleshoot-monitoring.sh # Diagnostics
│   ├── monitoring-test.html # Browser connectivity test
│   └── test-cors.html      # CORS testing
└── Makefile                 # Development commands
```

### Adding SNMP Discovery

Replace mock implementations in `backend/app/services/snmp.py`:

```python
from pysnmp.hlapi import *

async def discover_devices(self) -> List[Dict[str, Any]]:
    # Implement SNMP walks for:
    # - LLDP-MIB lldpRemTable
    # - BRIDGE-MIB dot1dBasePortTable  
    # - IF-MIB ifTable
    # - Q-BRIDGE-MIB for VLANs
    pass
```

### Customizing UI

The frontend uses vis-network for graph visualization. Customize:
- Node/edge styling in `ui/src/App.tsx`
- Layout algorithms via vis-network options
- Add new sidebar panels for additional metrics

## Security

- **Default**: Local-only access (no authentication)
- **Optional**: Basic Auth via environment variables
- **Network**: SNMP credentials should be secured
- **Database**: SQLite file permissions should be restricted

## Monitoring Integration

### Prometheus

The backend exposes Prometheus metrics at `/metrics`:

```
# Interface counters
netview_if_in_octets{device_id="switch1", if_index="1"}
netview_if_out_octets{device_id="switch1", if_index="1"}
netview_if_in_errors{device_id="switch1", if_index="1"}

# Device metrics
netview_discovered_devices_total
netview_device_cpu_utilization_percent{device_id="switch1"}
```

### Prometheus Server Setup

**Option 1: Using Docker Compose (Recommended)**

1. **Start Prometheus and Grafana:**
   ```bash
   docker-compose -f config/docker-compose.yml up -d
   ./scripts/setup-grafana.sh
   ./scripts/import-dashboard.sh
   ```

2. **Access the services:**
   - Prometheus UI: http://localhost:9090
   - Grafana UI: http://localhost:3000 (admin/admin)
   - NetView Dashboard: http://localhost:3000/d/netview-network-monitoring

3. **Query NetView metrics in Prometheus:**
   - `netview_http_requests_total` - Total HTTP requests
   - `rate(netview_http_requests_total[5m])` - Request rate
   - `netview_discovered_devices_total` - Discovered devices count

**Option 2: Manual Prometheus Installation**

1. **Download and run Prometheus:**
   ```bash
   # Download Prometheus
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvfz prometheus-*.tar.gz
   cd prometheus-*
   
   # Start Prometheus
   ./prometheus --config.file=prometheus.yml
   ```

2. **Configure prometheus.yml:**
   ```yaml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'netview'
       static_configs:
         - targets: ['localhost:8000']
   ```

### VictoriaMetrics

For time series storage, configure VictoriaMetrics to scrape:
```yaml
scrape_configs:
  - job_name: 'netview'
    static_configs:
      - targets: ['localhost:8000']
```

## Troubleshooting

**Backend won't start:**
- Check Python version (3.11+)
- Verify virtual environment: `source backend/.venv/bin/activate`
- Install dependencies: `pip install -r backend/requirements.txt`

**Frontend won't start:**
- Check Node.js version (18+)
- Install dependencies: `cd ui && npm install`

**No devices discovered:**
- Verify SNMP community strings
- Check network connectivity to devices
- Review discovery service logs

**Graph not rendering:**
- Check browser console for errors
- Verify API connectivity: `curl http://localhost:8000/topology`
- Ensure vis-network is properly mocked in tests

**Prometheus UI shows blank screen:**
- Run queries in the UI: `netview_http_requests_total`
- Check if metrics are available: `curl http://localhost:8000/metrics`
- Verify Prometheus is scraping: `curl http://localhost:9090/api/v1/targets`
- Use troubleshooting script: `./scripts/troubleshoot-monitoring.sh`

**Grafana shows no data:**
- Verify Prometheus data source is configured
- Check data source URL: `http://host.docker.internal:9090`
- Re-run setup: `./scripts/setup-grafana.sh`

## License

MIT License - see LICENSE file for details.


