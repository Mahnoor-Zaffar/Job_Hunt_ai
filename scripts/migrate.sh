#!/bin/bash
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head
echo "Migrations complete."
