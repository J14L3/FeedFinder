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

## Test Best Practices

1. **Unit Tests**: Test individual functions and components in isolation
2. **Integration Tests**: Test API endpoints and component interactions
3. **Mock External Dependencies**: Use mocks for database, API calls, etc.
4. **Test Edge Cases**: Include tests for error conditions and boundary cases
5. **Keep Tests Fast**: Tests should run quickly to enable frequent execution
6. **Clear Test Names**: Use descriptive test names that explain what is being tested

## Troubleshooting

### Backend Tests

- **Import Errors**: Make sure you're running tests from the backend directory
- **Database Connection**: Tests use mocks, so no database connection is needed
- **Module Not Found**: Ensure all dependencies are installed: `pip install -r requirements.txt`

### Frontend Tests

- **Module Not Found**: Run `npm install` to install dependencies
- **jsdom Errors**: Ensure `jsdom` is installed: `npm install -D jsdom`
- **Environment Variables**: Tests use mocked environment variables in `src/test/setup.js`

## Coverage Goals

- **Backend**: Aim for >80% code coverage
- **Frontend**: Aim for >70% code coverage for critical components

## Next Steps

1. Add more integration tests for API endpoints
2. Add end-to-end tests using Playwright or Cypress
3. Set up CI/CD pipeline to run tests automatically
4. Add performance tests for critical paths

