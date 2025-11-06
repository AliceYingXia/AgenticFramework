"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any, Dict
from datetime import datetime, timezone


class Message(BaseModel):
    """A single message in a conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    timestamp: Optional[datetime] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # For tool messages


class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str = Field(..., description="The question to ask the agent", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens in response")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to guide the agent")
    enable_tools: bool = Field(True, description="Enable function calling tools")
    tool_names: Optional[List[str]] = Field(None, description="Specific tools to enable (None = all)")


class ToolCall(BaseModel):
    """Information about a tool call made by the agent."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any


class AnswerResponse(BaseModel):
    """Response model for agent answers."""
    answer: str = Field(..., description="The agent's answer")
    session_id: str = Field(..., description="Session ID for this conversation")
    model: str = Field(..., description="Model used for the response")
    usage: dict = Field(..., description="Token usage information")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools called during processing")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationHistory(BaseModel):
    """Full conversation history for a session."""
    session_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    openai_configured: bool


class ToolInfo(BaseModel):
    """Information about an available tool."""
    name: str
    description: str
    schema: Dict[str, Any]


class ToolsListResponse(BaseModel):
    """Response with list of available tools."""
    tools: List[ToolInfo]
    count: int