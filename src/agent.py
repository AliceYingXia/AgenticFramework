"""Core agent implementation with OpenAI integration."""

import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from openai import AsyncOpenAI
from src.config import settings
from src.models import Message, ConversationHistory, ToolCall
from src.tools import ToolRegistry, default_registry


class ConversationSession:
    """Manages a single conversation session with history."""

    def __init__(self, session_id: str, system_prompt: Optional[str] = None):
        self.session_id = session_id
        self.messages: List[Message] = []
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Add system prompt if provided
        if system_prompt:
            self.add_message("system", system_prompt)

    def add_message(
        self,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> None:
        """Add a message to the conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name
        )
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

        # Trim history if it exceeds max length
        if len(self.messages) > settings.max_conversation_history:
            # Keep system message if it exists
            system_messages = [m for m in self.messages if m.role == "system"]
            other_messages = [m for m in self.messages if m.role != "system"]

            # Keep the most recent messages
            self.messages = system_messages + other_messages[-(settings.max_conversation_history - len(system_messages)):]

    def get_messages_for_api(self) -> List[dict]:
        """Convert messages to OpenAI API format."""
        api_messages = []
        for msg in self.messages:
            message_dict = {"role": msg.role}

            if msg.content is not None:
                message_dict["content"] = msg.content
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message_dict["tool_call_id"] = msg.tool_call_id
            if msg.name:
                message_dict["name"] = msg.name

            api_messages.append(message_dict)
        return api_messages

    def to_history(self) -> ConversationHistory:
        """Convert to ConversationHistory model."""
        return ConversationHistory(
            session_id=self.session_id,
            messages=self.messages,
            created_at=self.created_at,
            updated_at=self.updated_at
        )


class Agent:
    """Main agent class for handling Q&A with OpenAI."""

    def __init__(self):
        """Initialize the agent with OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.sessions: Dict[str, ConversationSession] = {}

    def _get_or_create_session(
        self,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> ConversationSession:
        """Get existing session or create a new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]

        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        session = ConversationSession(new_session_id, system_prompt)
        self.sessions[new_session_id] = session
        return session

    async def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
        tool_names: Optional[List[str]] = None,
        tool_registry: Optional[ToolRegistry] = None
    ) -> tuple[str, str, dict, List[ToolCall]]:
        """
        Ask a question to the agent with optional function calling.

        Args:
            question: The question to ask
            session_id: Optional session ID for conversation continuity
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt (only used for new sessions)
            enable_tools: Enable function calling tools
            tool_names: Specific tools to enable (None = all)
            tool_registry: Custom tool registry (defaults to global registry)

        Returns:
            Tuple of (answer, session_id, usage_info, tool_calls)
        """
        # Use default registry if none provided
        registry = tool_registry or default_registry

        # Get or create session
        session = self._get_or_create_session(session_id, system_prompt)

        # Add user question to history
        session.add_message("user", question)

        # Prepare API parameters
        temp = temperature if temperature is not None else settings.default_temperature
        max_tok = max_tokens if max_tokens is not None else settings.default_max_tokens

        # Prepare tools if enabled
        tools = None
        if enable_tools:
            tool_schemas = registry.get_tool_schemas()
            if tool_names:
                # Filter to specific tools
                tool_schemas = [
                    schema for schema in tool_schemas
                    if schema["function"]["name"] in tool_names
                ]
            if tool_schemas:
                tools = tool_schemas

        # Track tool calls
        executed_tools: List[ToolCall] = []

        # Call OpenAI API (may involve multiple rounds for tool execution)
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        while True:
            # Call OpenAI API
            api_params = {
                "model": settings.openai_model,
                "messages": session.get_messages_for_api(),
                "temperature": temp,
                "max_tokens": max_tok
            }
            if tools:
                api_params["tools"] = tools

            response = await self.client.chat.completions.create(**api_params)

            # Accumulate usage
            total_usage["prompt_tokens"] += response.usage.prompt_tokens
            total_usage["completion_tokens"] += response.usage.completion_tokens
            total_usage["total_tokens"] += response.usage.total_tokens

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # Check if the model wants to call tools
            if finish_reason == "tool_calls" and message.tool_calls:
                # Add assistant message with tool calls
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
                session.add_message(
                    "assistant",
                    content=message.content,
                    tool_calls=tool_calls_data
                )

                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    # Execute the tool
                    try:
                        result = await registry.execute_tool(tool_name, **arguments)
                        result_str = json.dumps(result)
                    except Exception as e:
                        result = {"error": str(e)}
                        result_str = json.dumps(result)

                    # Track the tool call
                    executed_tools.append(ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result
                    ))

                    # Add tool result to conversation
                    session.add_message(
                        "tool",
                        content=result_str,
                        tool_call_id=tool_call.id,
                        name=tool_name
                    )

                # Continue the loop to get final response
                continue

            else:
                # Final response received
                answer = message.content or ""

                # Add assistant response to history
                session.add_message("assistant", answer)

                return answer, session.session_id, total_usage, executed_tools

    def get_session_history(self, session_id: str) -> Optional[ConversationHistory]:
        """Get conversation history for a session."""
        if session_id in self.sessions:
            return self.sessions[session_id].to_history()
        return None

    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self.sessions.keys())