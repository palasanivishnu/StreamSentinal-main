#!/usr/bin/env bash
# ============================================================
# StreamSentinel — One-Command Deployment & Update Script
# ============================================================
set -e

echo "============================================================"
echo "🛡️ Deploying StreamSentinel Production Container Stack"
echo "============================================================"

# Navigate to project root
cd "$(dirname "$0")/.."

# Pull latest changes if in git repo
if [ -d .git ]; then
    echo "📥 Pulling latest code..."
    git pull origin main || git pull || true
fi

# Build and restart containers
echo "🔨 Building Docker images..."
docker compose build

echo "🚀 Restarting stack..."
docker compose down
docker compose up -d

echo "⏳ Waiting 10 seconds for services to initialize..."
sleep 10

echo "📊 Container Process Status:"
docker compose ps

echo "🏥 Testing API Health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ FastAPI Server is HEALTHY!"
else
    echo "⚠️ Health check warning — check logs with: docker compose logs -f"
fi

echo "============================================================"
echo "🎉 Deployment Completed!"
echo "FastAPI API: http://localhost:8000/docs"
echo "React UI:    http://localhost:5173"
echo "Grafana:     http://localhost:3000"
echo "Prometheus:  http://localhost:9090"
echo "============================================================"
