"""Unit tests for the Agent class."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.agent import Agent, ConversationSession
from src.config import settings


class TestConversationSession:
    """Tests for ConversationSession class."""

    def test_create_session_without_system_prompt(self):
        """Test creating a session without system prompt."""
        session = ConversationSession(session_id="test-123")
        assert session.session_id == "test-123"
        assert len(session.messages) == 0
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_create_session_with_system_prompt(self):
        """Test creating a session with system prompt."""
        system_prompt = "You are a helpful assistant."
        session = ConversationSession(session_id="test-123", system_prompt=system_prompt)

        assert len(session.messages) == 1
        assert session.messages[0].role == "system"
        assert session.messages[0].content == system_prompt

    def test_add_message(self):
        """Test adding messages to a session."""
        session = ConversationSession(session_id="test-123")

        session.add_message("user", "Hello")
        assert len(session.messages) == 1
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Hello"

        session.add_message("assistant", "Hi there!")
        assert len(session.messages) == 2
        assert session.messages[1].role == "assistant"
        assert session.messages[1].content == "Hi there!"

    def test_message_history_trimming(self):
        """Test that message history is trimmed when exceeding max length."""
        session = ConversationSession(
            session_id="test-123",
            system_prompt="You are helpful."
        )

        # Add more messages than max_conversation_history
        max_history = settings.max_conversation_history
        for i in range(max_history + 5):
            session.add_message("user", f"Question {i}")
            session.add_message("assistant", f"Answer {i}")

        # Should keep system message + most recent messages up to max
        assert len(session.messages) <= max_history

        # System message should still be there
        assert session.messages[0].role == "system"

    def test_get_messages_for_api(self):
        """Test converting messages to OpenAI API format."""
        session = ConversationSession(
            session_id="test-123",
            system_prompt="You are helpful."
        )
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")

        api_messages = session.get_messages_for_api()

        assert len(api_messages) == 3
        assert api_messages[0] == {"role": "system", "content": "You are helpful."}
        assert api_messages[1] == {"role": "user", "content": "Hello"}
        assert api_messages[2] == {"role": "assistant", "content": "Hi!"}

    def test_to_history(self):
        """Test converting session to ConversationHistory model."""
        session = ConversationSession(
            session_id="test-123",
            system_prompt="You are helpful."
        )
        session.add_message("user", "Hello")

        history = session.to_history()

        assert history.session_id == "test-123"
        assert len(history.messages) == 2
        assert isinstance(history.created_at, datetime)
        assert isinstance(history.updated_at, datetime)


class TestAgent:
    """Tests for Agent class."""

    @pytest.mark.asyncio
    async def test_ask_creates_new_session(self, agent_with_mock_client):
        """Test that asking without session_id creates a new session."""
        agent = agent_with_mock_client

        answer, session_id, usage = await agent.ask("What is Python?")

        assert answer == "This is a test response from the AI."
        assert session_id is not None
        assert session_id in agent.sessions
        assert usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_ask_reuses_existing_session(self, agent_with_mock_client):
        """Test that providing session_id reuses the session."""
        agent = agent_with_mock_client

        # First question
        _, session_id_1, _ = await agent.ask("What is Python?")

        # Second question with same session
        _, session_id_2, _ = await agent.ask(
            "Can you elaborate?",
            session_id=session_id_1
        )

        assert session_id_1 == session_id_2
        assert len(agent.sessions[session_id_1].messages) == 4  # 2 user + 2 assistant

    @pytest.mark.asyncio
    async def test_ask_with_custom_parameters(self, agent_with_mock_client):
        """Test asking with custom temperature and max_tokens."""
        agent = agent_with_mock_client

        await agent.ask(
            "What is Python?",
            temperature=0.9,
            max_tokens=500
        )

        # Verify the mock was called with correct parameters
        call_args = agent.client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.9
        assert call_args.kwargs["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_ask_with_system_prompt(self, agent_with_mock_client):
        """Test asking with a custom system prompt."""
        agent = agent_with_mock_client
        system_prompt = "You are a Python expert."

        _, session_id, _ = await agent.ask(
            "What is Python?",
            system_prompt=system_prompt
        )

        session = agent.sessions[session_id]
        assert session.messages[0].role == "system"
        assert session.messages[0].content == system_prompt

    @pytest.mark.asyncio
    async def test_conversation_context_maintained(self, agent_with_mock_client):
        """Test that conversation context is maintained across questions."""
        agent = agent_with_mock_client

        # Ask first question
        _, session_id, _ = await agent.ask("What is Python?")

        # Ask follow-up question
        await agent.ask("What are its features?", session_id=session_id)

        # Verify messages were sent to API with full context
        call_args = agent.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        assert len(messages) == 4  # 2 user questions + 2 assistant responses

    def test_get_session_history_existing(self, agent_with_mock_client):
        """Test getting history for an existing session."""
        agent = agent_with_mock_client
        session = ConversationSession(session_id="test-123")
        session.add_message("user", "Hello")
        agent.sessions["test-123"] = session

        history = agent.get_session_history("test-123")

        assert history is not None
        assert history.session_id == "test-123"
        assert len(history.messages) == 1

    def test_get_session_history_nonexistent(self, agent_with_mock_client):
        """Test getting history for a non-existent session."""
        agent = agent_with_mock_client
        history = agent.get_session_history("nonexistent")
        assert history is None

    def test_clear_session_existing(self, agent_with_mock_client):
        """Test clearing an existing session."""
        agent = agent_with_mock_client
        session = ConversationSession(session_id="test-123")
        agent.sessions["test-123"] = session

        result = agent.clear_session("test-123")

        assert result is True
        assert "test-123" not in agent.sessions

    def test_clear_session_nonexistent(self, agent_with_mock_client):
        """Test clearing a non-existent session."""
        agent = agent_with_mock_client
        result = agent.clear_session("nonexistent")
        assert result is False

    def test_list_sessions_empty(self, agent_with_mock_client):
        """Test listing sessions when there are none."""
        agent = agent_with_mock_client
        sessions = agent.list_sessions()
        assert sessions == []

    def test_list_sessions_multiple(self, agent_with_mock_client):
        """Test listing multiple sessions."""
        agent = agent_with_mock_client

        # Create multiple sessions
        session_ids = ["session-1", "session-2", "session-3"]
        for sid in session_ids:
            agent.sessions[sid] = ConversationSession(session_id=sid)

        listed_sessions = agent.list_sessions()

        assert len(listed_sessions) == 3
        assert set(listed_sessions) == set(session_ids)