# Testing Guide

This document describes the automated testing setup for the FeedFinder project.

## Overview

The project includes comprehensive automated tests for both backend (Python/Flask) and frontend (React) components.

## Backend Tests

### Setup

1. Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Running Tests

**On Linux/Mac:**
```bash
cd backend
chmod +x run_tests.sh
./run_tests.sh
```

**On Windows:**
```bash
cd backend
run_tests.bat
```

**Or manually:**
```bash
cd backend
pytest tests/ -v
```

### Test Structure

- `tests/test_hash.py` - Password hashing utilities
- `tests/test_csrf.py` - CSRF protection
- `tests/test_file_validator.py` - File upload validation
- `tests/test_auth_middleware.py` - Authentication middleware
- `tests/test_api_auth.py` - Authentication API endpoints
- `tests/test_api_posts.py` - Posts API endpoints
- `tests/test_health.py` - Health check endpoint

### Running Specific Tests

```bash
# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration

# Run only authentication tests
pytest tests/ -v -m auth

# Run a specific test file
pytest tests/test_hash.py -v

# Run a specific test
pytest tests/test_hash.py::TestPasswordHashing::test_hash_password_creates_hash -v
```

### Coverage

Generate coverage report:
```bash
pytest tests/ --cov=app --cov-report=html
```

View coverage report:
```bash
# Open htmlcov/index.html in your browser
```

## Frontend Tests

### Setup

1. Install test dependencies:
```bash
npm install
```

### Running Tests

```bash
# Run tests in watch mode
npm test

# Run tests once
npm test -- --run

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Test Structure

- `src/test/authService.test.js` - Authentication service tests
- `src/test/Login.test.jsx` - Login component tests
- `src/test/Register.test.jsx` - Register component tests

### Writing New Tests

#### Backend Test Example

```python
# tests/test_example.py
import pytest
from app.example import example_function

class TestExample:
    def test_example_function(self):
        result = example_function("input")
        assert result == "expected_output"
```

#### Frontend Test Example

```javascript
// src/test/Example.test.jsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Example from '../Example'

describe('Example Component', () => {
  it('should render correctly', () => {
    render(<Example />)
    expect(screen.getByText('Example')).toBeInTheDocument()
  })
})
```

## Continuous Integration

### Running All Tests

**Backend:**
```bash
cd backend && pytest tests/ -v
```

**Frontend:**
```bash
npm test -- --run
```
