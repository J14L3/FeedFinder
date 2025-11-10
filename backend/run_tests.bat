@echo off
REM Script to run backend tests on Windows

echo Running backend tests...
echo ========================

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Install test dependencies if needed
pip install -q -r requirements.txt

REM Run pytest with coverage using Python module syntax
python -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

echo.
echo Test coverage report generated in htmlcov\index.html

