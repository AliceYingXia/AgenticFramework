# Agentic Framework

An OpenAI-powered Q&A system with conversation memory and RESTful API built with FastAPI.

## Features

- **OpenAI Integration**: Leverages OpenAI's GPT models for intelligent Q&A
- **Conversation Memory**: Maintains context across multiple questions in a session
- **RESTful API**: Clean, well-documented API endpoints
- **Session Management**: Multiple concurrent conversation sessions
- **Configurable**: Easy configuration via environment variables
- **Async Support**: Built with async/await for high performance

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd AgenticFramework

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

### 3. Run the API Server

```bash
python -m src.main
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## API Endpoints

### Ask a Question

```bash
POST /api/v1/ask
```

**Request Body:**
```json
{
  "question": "What is Python?",
  "session_id": "optional-session-id",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful assistant."
}
```

**Response:**
```json
{
  "answer": "Python is a high-level programming language...",
  "session_id": "abc-123",
  "model": "gpt-4-turbo-preview",
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 50,
    "total_tokens": 70
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### Get Session History

```bash
GET /api/v1/sessions/{session_id}/history
```

### List All Sessions

```bash
GET /api/v1/sessions
```

### Clear Session

```bash
DELETE /api/v1/sessions/{session_id}
```

### Health Check

```bash
GET /health
```

## Usage Examples

### Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# Ask a question
response = requests.post(
    f"{API_URL}/api/v1/ask",
    json={
        "question": "What is machine learning?",
        "temperature": 0.7
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Session ID: {data['session_id']}")

# Continue the conversation
response = requests.post(
    f"{API_URL}/api/v1/ask",
    json={
        "question": "Can you give me an example?",
        "session_id": data['session_id']  # Use same session
    }
)

print(f"Follow-up Answer: {response.json()['answer']}")
```

### cURL Example

```bash
# Ask a question
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain quantum computing in simple terms",
    "temperature": 0.8
  }'

# Get conversation history
curl -X GET "http://localhost:8000/api/v1/sessions/{session_id}/history"

# List all sessions
curl -X GET "http://localhost:8000/api/v1/sessions"

# Clear a session
curl -X DELETE "http://localhost:8000/api/v1/sessions/{session_id}"
```

## Project Structure

```
AgenticFramework/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application
│   ├── agent.py             # Core agent logic
│   ├── models.py            # Pydantic models
│   └── config.py            # Configuration management
├── tests/
│   ├── __init__.py          # Test package
│   ├── conftest.py          # Pytest fixtures
│   ├── test_agent.py        # Agent unit tests
│   ├── test_models.py       # Model validation tests
│   ├── test_api.py          # API integration tests
│   └── test_config.py       # Configuration tests
├── .env.example             # Example environment variables
├── .env.test                # Test environment configuration
├── .gitignore              # Git ignore rules
├── pytest.ini              # Pytest configuration
├── requirements.txt        # Python dependencies
├── LICENSE                 # Apache 2.0 License
└── README.md              # This file
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4-turbo-preview` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |
| `MAX_CONVERSATION_HISTORY` | Max messages to keep in memory | `10` |
| `DEFAULT_TEMPERATURE` | Default sampling temperature | `0.7` |
| `DEFAULT_MAX_TOKENS` | Default max tokens per response | `1000` |

## Features in Detail

### Conversation Memory

The framework maintains conversation history for each session, allowing for contextual follow-up questions. The agent remembers previous exchanges and uses them to provide more relevant answers.

### Session Management

Each conversation can have a unique session ID. If not provided, the system generates one automatically. This allows for:
- Multiple concurrent conversations
- Conversation history retrieval
- Context preservation across requests

### Configurable Parameters

Each request can override default settings:
- **temperature**: Controls randomness (0.0 = deterministic, 2.0 = very random)
- **max_tokens**: Limits response length
- **system_prompt**: Customizes agent behavior

## Development

### Running Tests

The project includes comprehensive test coverage with unit tests and integration tests.

#### Install Test Dependencies

```bash
pip install -r requirements.txt
```

#### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
# Or: xdg-open htmlcov/index.html  # On Linux
```

#### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests for a specific file
pytest tests/test_agent.py

# Run a specific test
pytest tests/test_agent.py::TestAgent::test_ask_creates_new_session
```

#### Test Structure

- **`test_agent.py`**: Unit tests for agent logic and conversation management
  - ConversationSession creation and message handling
  - Agent initialization and question processing
  - Session management and history trimming

- **`test_models.py`**: Validation tests for Pydantic models
  - Request/response model validation
  - Field constraints and type checking
  - Edge cases and error handling

- **`test_api.py`**: Integration tests for API endpoints
  - HTTP endpoint behavior
  - Request/response validation
  - Error handling and status codes
  - End-to-end conversation flows

- **`test_config.py`**: Configuration management tests
  - Settings validation
  - Environment variable loading
  - Default value handling

#### Writing New Tests

When adding new features, include tests following these patterns:

```python
# Unit test example
def test_feature_name():
    """Test that feature does X."""
    # Arrange
    setup_data = create_test_data()

    # Act
    result = function_under_test(setup_data)

    # Assert
    assert result == expected_value

# Async test example
@pytest.mark.asyncio
async def test_async_feature():
    """Test async feature."""
    result = await async_function()
    assert result is not None
```

#### Test Coverage Goals

We aim for:
- **>90% code coverage** for core business logic
- **100% coverage** for critical paths (authentication, data validation)
- All API endpoints tested with success and error cases

#### Continuous Integration

Tests should pass before merging:

```bash
# Run full test suite with strict coverage
pytest --cov=src --cov-fail-under=90
```

### Code Style

This project follows PEP 8 guidelines. Format code with:

```bash
# Install black (if not already installed)
pip install black

# Format all source code
black src/

# Format tests
black tests/

# Check without modifying
black --check src/
```

## License

Apache License 2.0 - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.