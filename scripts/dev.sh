#!/bin/bash
set -e
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Job Hunting AI — Development Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Ensure Docker is running
echo ""
echo "[1/5] Starting Docker..."
open -a Docker 2>/dev/null || true
for i in $(seq 1 20); do
  docker info &>/dev/null && break
  sleep 2
done
echo "  Docker ready."

# 2. Stop conflicting local postgres, start Docker services
echo "[2/5] Starting PostgreSQL + Redis..."
brew services stop postgresql@18 2>/dev/null || true
brew services stop postgresql@16 2>/dev/null || true
cd "$(dirname "$0")/.."
docker compose -f docker/docker-compose.yml up -d postgres redis 2>&1
sleep 2
echo "  Services ready."

# 3. Run migrations
echo "[3/5] Running database migrations..."
uv run alembic upgrade head 2>&1
echo "  Migrations complete."

# 4. Start backend
echo "[4/5] Starting API server (port 8000)..."
pkill -f uvicorn 2>/dev/null || true
nohup uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/uvicorn.log 2>&1 &
sleep 3
echo "  Backend: http://localhost:8000"

# 5. Start frontend
echo "[5/5] Starting dashboard (port 3000)..."
pkill -f "next dev" 2>/dev/null || true
cd frontend
nohup npm run dev > /tmp/nextjs.log 2>&1 &
sleep 5
cd ..
echo "  Frontend: http://localhost:3000"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  All services running!"
echo "  Dashboard:  http://localhost:3000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  Health:     http://localhost:8000/api/v1/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
