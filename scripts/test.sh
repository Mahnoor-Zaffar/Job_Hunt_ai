#!/bin/bash
set -e

echo "Running unit tests..."
uv run pytest tests/test_scrapers/ tests/test_core/ tests/test_models.py tests/test_services.py -v

echo ""
echo "All unit tests passed."
echo ""
echo "To run integration tests (requires PostgreSQL + Redis):"
echo "  ./scripts/test.sh --integration"
