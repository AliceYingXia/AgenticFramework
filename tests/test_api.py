"""Integration tests for API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def mock_agent():
    """Mock agent for testing API endpoints."""
    with patch("src.main.agent") as mock:
        # Configure mock agent methods
        mock.ask = AsyncMock(return_value=(
            "This is a test answer.",
            "test-session-123",
            {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        ))
        mock.get_session_history = MagicMock(return_value=None)
        mock.list_sessions = MagicMock(return_value=[])
        mock.clear_session = MagicMock(return_value=True)
        yield mock


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self):
        """Test that root endpoint returns API information."""
        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Agentic Framework API"
        assert "version" in data
        assert "endpoints" in data


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health check endpoint."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "openai_configured" in data


class TestAskEndpoint:
    """Tests for /api/v1/ask endpoint."""

    def test_ask_minimal_request(self, mock_agent):
        """Test asking with minimal request."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={"question": "What is Python?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a test answer."
        assert data["session_id"] == "test-session-123"
        assert data["usage"]["total_tokens"] == 30

    def test_ask_with_session_id(self, mock_agent):
        """Test asking with existing session ID."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "Follow-up question",
                "session_id": "existing-session"
            }
        )

        assert response.status_code == 200
        mock_agent.ask.assert_called_once()
        call_kwargs = mock_agent.ask.call_args.kwargs
        assert call_kwargs["session_id"] == "existing-session"

    def test_ask_with_all_parameters(self, mock_agent):
        """Test asking with all optional parameters."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is Python?",
                "session_id": "test-123",
                "temperature": 0.8,
                "max_tokens": 500,
                "system_prompt": "You are a Python expert."
            }
        )

        assert response.status_code == 200
        mock_agent.ask.assert_called_once()
        call_kwargs = mock_agent.ask.call_args.kwargs
        assert call_kwargs["temperature"] == 0.8
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["system_prompt"] == "You are a Python expert."

    def test_ask_empty_question_rejected(self, mock_agent):
        """Test that empty questions are rejected."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={"question": ""}
        )

        assert response.status_code == 422  # Validation error

    def test_ask_invalid_temperature_rejected(self, mock_agent):
        """Test that invalid temperature is rejected."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "Test",
                "temperature": 3.0  # Out of range
            }
        )

        assert response.status_code == 422

    def test_ask_missing_question_rejected(self, mock_agent):
        """Test that request without question is rejected."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={}
        )

        assert response.status_code == 422

    def test_ask_agent_error_handling(self, mock_agent):
        """Test error handling when agent raises exception."""
        mock_agent.ask.side_effect = Exception("OpenAI API error")

        client = TestClient(app)
        response = client.post(
            "/api/v1/ask",
            json={"question": "Test"}
        )

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


class TestSessionHistoryEndpoint:
    """Tests for /api/v1/sessions/{session_id}/history endpoint."""

    def test_get_existing_session_history(self, mock_agent):
        """Test getting history for existing session."""
        from src.models import ConversationHistory, Message
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        mock_history = ConversationHistory(
            session_id="test-123",
            messages=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi!")
            ],
            created_at=now,
            updated_at=now
        )
        mock_agent.get_session_history.return_value = mock_history

        client = TestClient(app)
        response = client.get("/api/v1/sessions/test-123/history")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-123"
        assert len(data["messages"]) == 2

    def test_get_nonexistent_session_history(self, mock_agent):
        """Test getting history for non-existent session."""
        mock_agent.get_session_history.return_value = None

        client = TestClient(app)
        response = client.get("/api/v1/sessions/nonexistent/history")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestListSessionsEndpoint:
    """Tests for /api/v1/sessions endpoint."""

    def test_list_empty_sessions(self, mock_agent):
        """Test listing when no sessions exist."""
        mock_agent.list_sessions.return_value = []

        client = TestClient(app)
        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_multiple_sessions(self, mock_agent):
        """Test listing multiple sessions."""
        session_ids = ["session-1", "session-2", "session-3"]
        mock_agent.list_sessions.return_value = session_ids

        client = TestClient(app)
        response = client.get("/api/v1/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert set(data) == set(session_ids)


class TestClearSessionEndpoint:
    """Tests for DELETE /api/v1/sessions/{session_id} endpoint."""

    def test_clear_existing_session(self, mock_agent):
        """Test clearing an existing session."""
        mock_agent.clear_session.return_value = True

        client = TestClient(app)
        response = client.delete("/api/v1/sessions/test-123")

        assert response.status_code == 200
        data = response.json()
        assert "cleared successfully" in data["message"].lower()
        assert data["session_id"] == "test-123"

    def test_clear_nonexistent_session(self, mock_agent):
        """Test clearing a non-existent session."""
        mock_agent.clear_session.return_value = False

        client = TestClient(app)
        response = client.delete("/api/v1/sessions/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCORSConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses."""
        client = TestClient(app)
        response = client.options("/health")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers


class TestEndToEndConversation:
    """End-to-end tests for full conversation flow."""

    def test_full_conversation_flow(self, mock_agent):
        """Test a complete conversation flow."""
        # Mock different responses for each call
        responses = [
            ("Python is a programming language.", "session-abc", {"total_tokens": 30}),
            ("Sure! Here's an example.", "session-abc", {"total_tokens": 25}),
        ]
        mock_agent.ask.side_effect = responses

        client = TestClient(app)

        # First question
        response1 = client.post(
            "/api/v1/ask",
            json={"question": "What is Python?"}
        )
        assert response1.status_code == 200
        session_id = response1.json()["session_id"]

        # Follow-up question with same session
        response2 = client.post(
            "/api/v1/ask",
            json={
                "question": "Can you give an example?",
                "session_id": session_id
            }
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Verify agent.ask was called twice
        assert mock_agent.ask.call_count == 2