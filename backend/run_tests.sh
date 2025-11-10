#!/bin/bash
# Script to run backend tests

echo "Running backend tests..."
echo "========================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies if needed
pip install -q -r requirements.txt

# Run pytest with coverage
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "Test coverage report generated in htmlcov/index.html"

