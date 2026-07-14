#!/bin/bash
set -e

echo "Running linter and type checker..."
ruff check .
ruff format --check .
mypy backend/
echo "All checks passed."
