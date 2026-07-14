#!/bin/bash
set -e

echo "Running tests with coverage..."
pytest tests/ -v --cov=backend --cov-report=term-missing
