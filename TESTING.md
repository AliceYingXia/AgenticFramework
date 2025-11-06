# Testing Guide

Comprehensive testing documentation for the Agentic Framework.

## Overview

The Agentic Framework includes a complete test suite with:
- **Unit tests** for core components
- **Integration tests** for API endpoints
- **Mocked dependencies** for isolated testing
- **Coverage reporting** to track test coverage

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
./run_tests.sh --coverage

# Run specific test file
pytest tests/test_agent.py
```

## Test Structure

### Test Files

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── test_agent.py         # Agent logic tests (17 tests)
├── test_models.py        # Pydantic model tests (11 tests)
├── test_api.py           # API endpoint tests (15 tests)
└── test_config.py        # Configuration tests (4 tests)
```

### Total: 47+ Test Cases

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation:

#### `test_agent.py` - Agent Logic Tests

**ConversationSession Tests:**
- ✓ Create session without system prompt
- ✓ Create session with system prompt
- ✓ Add messages to session
- ✓ Message history trimming when exceeding max
- ✓ Convert messages to OpenAI API format
- ✓ Convert session to ConversationHistory model

**Agent Tests:**
- ✓ Ask creates new session automatically
- ✓ Ask reuses existing session
- ✓ Ask with custom temperature and max_tokens
- ✓ Ask with custom system prompt
- ✓ Conversation context maintained across questions
- ✓ Get history for existing session
- ✓ Get history for non-existent session returns None
- ✓ Clear existing session
- ✓ Clear non-existent session returns False
- ✓ List sessions when empty
- ✓ List multiple sessions

#### `test_models.py` - Pydantic Model Tests

**Message Model:**
- ✓ Create valid message
- ✓ Create message with timestamp
- ✓ Reject invalid roles
- ✓ Accept all valid roles (system, user, assistant)

**QuestionRequest Model:**
- ✓ Minimal valid request (question only)
- ✓ Full valid request (all fields)
- ✓ Reject empty questions
- ✓ Temperature validation (0.0 to 2.0)
- ✓ Max tokens validation (> 0)

**AnswerResponse Model:**
- ✓ Create valid response
- ✓ Response serialization

**ConversationHistory Model:**
- ✓ Create valid history
- ✓ Allow empty messages list

**HealthResponse Model:**
- ✓ Create healthy response
- ✓ Create unhealthy response

#### `test_config.py` - Configuration Tests

- ✓ Create settings with all fields
- ✓ Use default values when not provided
- ✓ Require API key (validation error if missing)
- ✓ Case-insensitive environment variables

### Integration Tests

Integration tests verify the complete API behavior:

#### `test_api.py` - API Endpoint Tests

**Root Endpoint:**
- ✓ Returns API information

**Health Endpoint:**
- ✓ Returns health status

**Ask Endpoint:**
- ✓ Minimal request (question only)
- ✓ Request with session ID
- ✓ Request with all parameters
- ✓ Reject empty questions
- ✓ Reject invalid temperature
- ✓ Reject missing question
- ✓ Handle agent errors gracefully

**Session History Endpoint:**
- ✓ Get existing session history
- ✓ Return 404 for non-existent session

**List Sessions Endpoint:**
- ✓ List empty sessions
- ✓ List multiple sessions

**Clear Session Endpoint:**
- ✓ Clear existing session
- ✓ Return 404 for non-existent session

**End-to-End:**
- ✓ Full conversation flow with context

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Run specific file
pytest tests/test_agent.py

# Run specific test
pytest tests/test_agent.py::TestAgent::test_ask_creates_new_session

# Run specific class
pytest tests/test_models.py::TestQuestionRequest
```

### Using the Test Runner Script

```bash
# Run all tests with verbose output
./run_tests.sh

# Run with coverage report
./run_tests.sh --coverage

# Run only unit tests
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration

# Fast mode (no coverage)
./run_tests.sh --fast

# Strict mode (fail if coverage < 90%)
./run_tests.sh --strict
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View in browser (macOS)
open htmlcov/index.html

# View in browser (Linux)
xdg-open htmlcov/index.html

# Terminal coverage report
pytest --cov=src --cov-report=term-missing
```

## Test Fixtures

Defined in `conftest.py`:

### `mock_openai_response`
Mock OpenAI API response with predefined content and token usage.

### `mock_openai_client`
Mock AsyncOpenAI client for testing without API calls.

### `agent_with_mock_client`
Agent instance with mocked OpenAI client for unit testing.

### `conversation_session`
Basic conversation session for testing.

### `client`
FastAPI TestClient for API integration tests.

### `sample_question` / `sample_questions`
Predefined questions for test consistency.

## Writing New Tests

### Unit Test Template

```python
def test_feature_name():
    """Test that feature does X."""
    # Arrange - Set up test data
    data = create_test_data()

    # Act - Execute the code
    result = function_under_test(data)

    # Assert - Verify the result
    assert result == expected_value
    assert result.property == expected_property
```

### Async Test Template

```python
import pytest

@pytest.mark.asyncio
async def test_async_feature():
    """Test async feature."""
    # Arrange
    agent = create_agent()

    # Act
    result = await agent.async_method()

    # Assert
    assert result is not None
```

### API Test Template

```python
def test_api_endpoint(client):
    """Test API endpoint behavior."""
    # Act
    response = client.post(
        "/api/v1/endpoint",
        json={"key": "value"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "expected"
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=term-missing
    --cov-report=html
```

### Test Environment

Tests use `.env.test` instead of `.env` to avoid using real API keys:

```bash
OPENAI_API_KEY=test-api-key-12345
OPENAI_MODEL=gpt-4-turbo-preview
```

## Coverage Goals

| Component | Goal | Current |
|-----------|------|---------|
| Core Logic (agent.py) | 95%+ | ✓ |
| Models (models.py) | 100% | ✓ |
| API Endpoints (main.py) | 90%+ | ✓ |
| Configuration (config.py) | 85%+ | ✓ |
| **Overall** | **>90%** | **Target** |

## Continuous Integration

### Pre-commit Checks

```bash
# Run before committing
pytest --cov=src --cov-fail-under=90
```

### CI Pipeline Recommendations

```yaml
# Example for GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-fail-under=90 --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Make sure you're in the project root
cd /path/to/AgenticFramework

# Install in development mode
pip install -e .
```

**OpenAI API Calls in Tests:**
- Tests should NEVER make real API calls
- All tests use mocked clients
- Check that fixtures are properly applied

**Fixture Not Found:**
```bash
# Ensure conftest.py is in tests/ directory
# Fixtures are automatically discovered by pytest
```

**Coverage Too Low:**
```bash
# Identify uncovered lines
pytest --cov=src --cov-report=term-missing

# Focus on critical paths first
```

## Best Practices

1. **Always mock external dependencies** (OpenAI API, databases, etc.)
2. **Test both success and failure cases**
3. **Use descriptive test names** that explain what's being tested
4. **Keep tests independent** - no test should depend on another
5. **Use fixtures** to reduce code duplication
6. **Test edge cases** (empty inputs, null values, boundary conditions)
7. **Verify error handling** explicitly

## Adding Tests for New Features

When adding a new feature:

1. **Write tests first** (TDD approach recommended)
2. **Cover happy path** - normal usage scenario
3. **Cover edge cases** - unusual inputs, boundaries
4. **Cover error cases** - invalid inputs, exceptions
5. **Update this documentation** if needed

Example:
```python
# Feature: Add rate limiting

# tests/test_rate_limiting.py
class TestRateLimiting:
    """Tests for rate limiting feature."""

    def test_allows_requests_within_limit(self):
        """Test that requests within limit are allowed."""
        pass

    def test_blocks_requests_exceeding_limit(self):
        """Test that requests exceeding limit are blocked."""
        pass

    def test_resets_after_time_window(self):
        """Test that limit resets after time window."""
        pass
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Testing](https://docs.pydantic.dev/latest/concepts/testing/)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)