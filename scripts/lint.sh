#!/bin/bash
set -e

echo "Running linter and type checker..."
uv run ruff check .
uv run ruff format --check .
uv run mypy backend/
echo "All checks passed."
