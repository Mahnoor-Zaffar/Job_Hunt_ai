#!/bin/bash
set -e

echo "Starting Job Hunting AI..."

if docker compose version &>/dev/null && docker info &>/dev/null 2>&1; then
    echo "Docker detected — starting full stack..."
    docker compose -f docker/docker-compose.yml up --build
else
    echo "Docker not available — starting API server directly..."
    echo "Backend: http://localhost:8000"
    echo "API docs: http://localhost:8000/docs"
    uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi
