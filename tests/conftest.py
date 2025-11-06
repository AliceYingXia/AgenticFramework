"""Pytest configuration and fixtures."""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from src.agent import Agent, ConversationSession
from src.main import app


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response from the AI."
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30
    return mock_response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock AsyncOpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return mock_client


@pytest.fixture
def agent_with_mock_client(mock_openai_client):
    """Create an Agent instance with mocked OpenAI client."""
    agent = Agent()
    agent.client = mock_openai_client
    return agent


@pytest.fixture
def conversation_session():
    """Create a basic conversation session."""
    return ConversationSession(
        session_id="test-session-123",
        system_prompt="You are a helpful assistant."
    )


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "What is Python?"


@pytest.fixture
def sample_questions():
    """Multiple questions for conversation testing."""
    return [
        "What is Python?",
        "Can you give me an example?",
        "What are its main features?"
    ]