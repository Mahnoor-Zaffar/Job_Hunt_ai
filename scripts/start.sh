#!/bin/bash
set -e

echo "Starting Job Hunting AI..."
docker compose -f docker/docker-compose.yml up --build
