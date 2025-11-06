"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models import (
    Message,
    QuestionRequest,
    AnswerResponse,
    ConversationHistory,
    HealthResponse
)


class TestMessage:
    """Tests for Message model."""

    def test_create_valid_message(self):
        """Test creating a valid message."""
        message = Message(
            role="user",
            content="Hello, world!"
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp is None

    def test_create_message_with_timestamp(self):
        """Test creating a message with timestamp."""
        now = datetime.now(timezone.utc)
        message = Message(
            role="assistant",
            content="Hi there!",
            timestamp=now
        )
        assert message.timestamp == now

    def test_invalid_role(self):
        """Test that invalid roles are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role="invalid", content="Test")

        errors = exc_info.value.errors()
        assert any("role" in str(error) for error in errors)

    def test_valid_roles(self):
        """Test all valid roles."""
        valid_roles = ["system", "user", "assistant"]
        for role in valid_roles:
            message = Message(role=role, content="Test")
            assert message.role == role


class TestQuestionRequest:
    """Tests for QuestionRequest model."""

    def test_minimal_valid_request(self):
        """Test creating request with only required fields."""
        request = QuestionRequest(question="What is Python?")
        assert request.question == "What is Python?"
        assert request.session_id is None
        assert request.temperature is None
        assert request.max_tokens is None
        assert request.system_prompt is None

    def test_full_valid_request(self):
        """Test creating request with all fields."""
        request = QuestionRequest(
            question="What is Python?",
            session_id="test-session-123",
            temperature=0.8,
            max_tokens=500,
            system_prompt="You are a helpful assistant."
        )
        assert request.question == "What is Python?"
        assert request.session_id == "test-session-123"
        assert request.temperature == 0.8
        assert request.max_tokens == 500
        assert request.system_prompt == "You are a helpful assistant."

    def test_empty_question_rejected(self):
        """Test that empty questions are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            QuestionRequest(question="")

        errors = exc_info.value.errors()
        assert any("question" in str(error) for error in errors)

    def test_temperature_validation(self):
        """Test temperature bounds validation."""
        # Valid temperatures
        QuestionRequest(question="Test", temperature=0.0)
        QuestionRequest(question="Test", temperature=1.0)
        QuestionRequest(question="Test", temperature=2.0)

        # Invalid: too low
        with pytest.raises(ValidationError):
            QuestionRequest(question="Test", temperature=-0.1)

        # Invalid: too high
        with pytest.raises(ValidationError):
            QuestionRequest(question="Test", temperature=2.1)

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid
        QuestionRequest(question="Test", max_tokens=1)
        QuestionRequest(question="Test", max_tokens=1000)

        # Invalid: zero
        with pytest.raises(ValidationError):
            QuestionRequest(question="Test", max_tokens=0)

        # Invalid: negative
        with pytest.raises(ValidationError):
            QuestionRequest(question="Test", max_tokens=-1)


class TestAnswerResponse:
    """Tests for AnswerResponse model."""

    def test_create_valid_response(self):
        """Test creating a valid response."""
        response = AnswerResponse(
            answer="Python is a programming language.",
            session_id="test-123",
            model="gpt-4",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        )
        assert response.answer == "Python is a programming language."
        assert response.session_id == "test-123"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 30
        assert isinstance(response.timestamp, datetime)

    def test_response_serialization(self):
        """Test that response can be serialized to dict."""
        response = AnswerResponse(
            answer="Test answer",
            session_id="test-123",
            model="gpt-4",
            usage={"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        )
        data = response.model_dump()

        assert data["answer"] == "Test answer"
        assert data["session_id"] == "test-123"
        assert "timestamp" in data


class TestConversationHistory:
    """Tests for ConversationHistory model."""

    def test_create_valid_history(self):
        """Test creating valid conversation history."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!")
        ]
        now = datetime.now(timezone.utc)

        history = ConversationHistory(
            session_id="test-123",
            messages=messages,
            created_at=now,
            updated_at=now
        )

        assert history.session_id == "test-123"
        assert len(history.messages) == 2
        assert history.created_at == now
        assert history.updated_at == now

    def test_empty_messages_allowed(self):
        """Test that empty message list is allowed."""
        now = datetime.now(timezone.utc)
        history = ConversationHistory(
            session_id="test-123",
            messages=[],
            created_at=now,
            updated_at=now
        )
        assert len(history.messages) == 0


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_create_healthy_response(self):
        """Test creating a healthy response."""
        health = HealthResponse(
            status="healthy",
            version="0.1.0",
            openai_configured=True
        )
        assert health.status == "healthy"
        assert health.version == "0.1.0"
        assert health.openai_configured is True

    def test_create_unhealthy_response(self):
        """Test creating an unhealthy response."""
        health = HealthResponse(
            status="unhealthy",
            version="0.1.0",
            openai_configured=False
        )
        assert health.status == "unhealthy"
        assert health.openai_configured is False
