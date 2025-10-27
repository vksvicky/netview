#!/bin/bash

# NetView Frontend Test Script with Coverage
# This script runs frontend tests with coverage reporting

set -e  # Exit on any error

echo "🧪 Running NetView Frontend Tests with Coverage..."

clear

# Change to frontend directory
cd "$(dirname "$0")/../ui"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not installed. Please run build-frontend.sh first."
    exit 1
fi

# Install coverage dependencies if not already installed
if ! npm list @vitest/coverage-v8 >/dev/null 2>&1; then
    echo "📥 Installing coverage dependencies..."
    npm install --save-dev @vitest/coverage-v8@^3.2.4 --legacy-peer-deps
fi

# Update vite config to include coverage
echo "🔧 Configuring coverage..."
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5170,
    host: true
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/vitest.setup.ts'
      ]
    }
  }
})
EOF

# Run tests with coverage
echo "🔍 Running tests with coverage..."
npm run test -- --coverage --run

echo ""
echo "✅ Frontend tests completed!"
echo "📊 Coverage report: ui/coverage/index.html"
echo "📈 Coverage summary displayed above"
