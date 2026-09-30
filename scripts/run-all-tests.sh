#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "=== Running Full Test Suite ==="
python3 -m pytest tests/ -v --tb=short

echo ""
echo "=== Test Coverage Report ==="
python3 -m pytest tests/ --cov=wiz_central_toolkit --cov-report=term-missing

echo ""
echo "=== All Tests Passed ==="
