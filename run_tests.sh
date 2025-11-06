#!/bin/bash

# Test runner script for Agentic Framework

set -e  # Exit on error

echo "=== Agentic Framework Test Suite ==="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: No virtual environment detected."
    echo "It's recommended to run tests in a virtual environment."
    echo ""
    if [ -d "venv" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    fi
fi

# Set test environment
export ENV_FILE=".env.test"

# Parse command line arguments
if [ "$1" == "--coverage" ]; then
    echo "Running tests with coverage report..."
    pytest --cov=src --cov-report=term-missing --cov-report=html -v
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
elif [ "$1" == "--unit" ]; then
    echo "Running unit tests only..."
    pytest -m unit -v
elif [ "$1" == "--integration" ]; then
    echo "Running integration tests only..."
    pytest -m integration -v
elif [ "$1" == "--fast" ]; then
    echo "Running tests (fast mode, no coverage)..."
    pytest -v
elif [ "$1" == "--strict" ]; then
    echo "Running tests with strict coverage requirements..."
    pytest --cov=src --cov-fail-under=90 -v
else
    echo "Running all tests..."
    pytest -v
fi

echo ""
echo "=== Tests Complete ==="