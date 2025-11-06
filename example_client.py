"""Example client for testing the Agentic Framework API."""

import requests
import json
from typing import Optional


class AgentClient:
    """Simple client for interacting with the Agentic Framework API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.current_session_id: Optional[str] = None

    def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        new_session: bool = False
    ) -> dict:
        """
        Ask a question to the agent.

        Args:
            question: The question to ask
            session_id: Optional session ID (uses current session if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt
            new_session: If True, starts a new session

        Returns:
            Response dictionary with answer and metadata
        """
        if new_session:
            self.current_session_id = None

        payload = {
            "question": question,
            "session_id": session_id or self.current_session_id
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if system_prompt is not None:
            payload["system_prompt"] = system_prompt

        response = requests.post(
            f"{self.base_url}/api/v1/ask",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        self.current_session_id = data["session_id"]
        return data

    def get_history(self, session_id: Optional[str] = None) -> dict:
        """Get conversation history for a session."""
        sid = session_id or self.current_session_id
        if not sid:
            raise ValueError("No session ID provided or available")

        response = requests.get(
            f"{self.base_url}/api/v1/sessions/{sid}/history"
        )
        response.raise_for_status()
        return response.json()

    def list_sessions(self) -> list:
        """List all active sessions."""
        response = requests.get(f"{self.base_url}/api/v1/sessions")
        response.raise_for_status()
        return response.json()

    def clear_session(self, session_id: Optional[str] = None) -> dict:
        """Clear a session's history."""
        sid = session_id or self.current_session_id
        if not sid:
            raise ValueError("No session ID provided or available")

        response = requests.delete(
            f"{self.base_url}/api/v1/sessions/{sid}"
        )
        response.raise_for_status()

        if sid == self.current_session_id:
            self.current_session_id = None

        return response.json()

    def health_check(self) -> dict:
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the client."""
    print("=== Agentic Framework Client Example ===\n")

    # Initialize client
    client = AgentClient()

    # Health check
    print("1. Health Check:")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}")
    print(f"   OpenAI Configured: {health['openai_configured']}\n")

    # Ask first question (new session)
    print("2. Asking first question:")
    response = client.ask(
        "What is Python and why is it popular?",
        system_prompt="You are a helpful programming tutor.",
        new_session=True
    )
    print(f"   Session ID: {response['session_id']}")
    print(f"   Answer: {response['answer'][:100]}...")
    print(f"   Tokens used: {response['usage']['total_tokens']}\n")

    # Follow-up question (same session)
    print("3. Follow-up question (maintaining context):")
    response = client.ask("Can you give me a simple example?")
    print(f"   Answer: {response['answer'][:100]}...\n")

    # Get conversation history
    print("4. Conversation History:")
    history = client.get_history()
    print(f"   Messages in conversation: {len(history['messages'])}")
    for i, msg in enumerate(history['messages'], 1):
        role = msg['role'].upper()
        content = msg['content'][:50]
        print(f"   {i}. [{role}] {content}...")
    print()

    # List all sessions
    print("5. Active Sessions:")
    sessions = client.list_sessions()
    print(f"   Total sessions: {len(sessions)}")
    for sid in sessions:
        print(f"   - {sid}")
    print()

    # Clear session
    print("6. Clearing session:")
    result = client.clear_session()
    print(f"   {result['message']}\n")

    print("=== Example Complete ===")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server.")
        print("Make sure the server is running: python -m src.main")
    except Exception as e:
        print(f"Error: {e}")