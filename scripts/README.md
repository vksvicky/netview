# NetView Scripts

This directory contains build, run, and test scripts for the NetView application.

## 📁 Scripts Overview

### Build Scripts
- **`build-backend.sh`** - Builds the backend application (installs dependencies, sets up virtual environment)
- **`build-frontend.sh`** - Builds the frontend application (installs dependencies, creates production build)

### Run Scripts
- **`run-backend.sh`** - Runs the backend server only (http://localhost:8000)
- **`run-frontend.sh`** - Runs the frontend development server only (http://localhost:5170)
- **`run-fullstack.sh`** - Runs both backend and frontend servers simultaneously

### Test Scripts (with Coverage)
- **`test-backend.sh`** - Runs backend tests with coverage reporting
- **`test-frontend.sh`** - Runs frontend tests with coverage reporting
- **`test-fullstack.sh`** - Runs both backend and frontend tests with coverage

### Utility Scripts
- **`kill-ports.sh`** - Kills processes on specified ports (useful for troubleshooting)

## 🚀 Quick Start

### First Time Setup
```bash
# Build both backend and frontend
./scripts/build-backend.sh
./scripts/build-frontend.sh

# Or build everything at once (if you have both environments ready)
./scripts/build-backend.sh && ./scripts/build-frontend.sh
```

### Development
```bash
# Run full stack (recommended for development)
./scripts/run-fullstack.sh

# Or run individually
./scripts/run-backend.sh    # Terminal 1
./scripts/run-frontend.sh   # Terminal 2
```

### Testing
```bash
# Run all tests with coverage
./scripts/test-fullstack.sh

# Or run individually
./scripts/test-backend.sh
./scripts/test-frontend.sh
```

## 🔧 Port Management

All run scripts now automatically handle port conflicts by:
- Checking for existing processes on required ports
- Killing conflicting processes before starting new ones
- Providing clear feedback about port status

### Manual Port Management
```bash
# Kill processes on specific ports
./scripts/kill-ports.sh 8000 5170

# Kill processes on common NetView ports
./scripts/kill-ports.sh
```

### Ports Used
- **Backend**: 8000 (FastAPI)
- **Frontend**: 5170-5173 (Vite development server)

## 📊 Coverage Reports

After running tests, coverage reports are generated:
- **Backend**: `backend/htmlcov/index.html`
- **Frontend**: `ui/coverage/index.html`

## 🔧 Prerequisites

### Backend
- Python 3.8+
- pip

### Frontend
- Node.js 16+
- npm

## 📝 Notes

- All scripts include error handling and will exit on failure
- Scripts automatically handle virtual environment setup for backend
- Scripts automatically handle dependency installation for frontend
- Coverage reports are generated in HTML format for easy viewing
- Full stack scripts run both services and can be stopped with Ctrl+C
- **Port conflicts are automatically resolved** - no more "port already in use" errors!
