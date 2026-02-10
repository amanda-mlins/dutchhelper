#!/bin/bash

# Quick script to run backend tests

set -e  # Exit on error

echo "=========================================="
echo "Running DutchHelper Backend Tests"
echo "=========================================="

cd "$(dirname "$0")"

# Get python path
PYTHON_PATH="/Users/alins/dutchhelper/backend/bin/python"

echo ""
echo "✓ Running all tests..."
$PYTHON_PATH -m pytest tests/ -v --tb=short

echo ""
echo "=========================================="
echo "✓ All tests passed!"
echo "=========================================="

# Optional: Run with coverage
if [ "$1" == "--coverage" ]; then
    echo ""
    echo "Generating coverage report..."
    $PYTHON_PATH -m pytest tests/ --cov=app --cov-report=html
    echo "Coverage report generated in htmlcov/index.html"
fi
