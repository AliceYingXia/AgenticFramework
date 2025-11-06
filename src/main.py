"""FastAPI application for the agentic Q&A framework."""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional

from src.agent import Agent
from src.config import settings
from src.models import (
    QuestionRequest,
    AnswerResponse,
    ConversationHistory,
    HealthResponse,
    ToolInfo,
    ToolsListResponse
)
from src.tools import default_registry
from src import __version__


# Global agent instance
agent: Optional[Agent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    global agent
    # Startup: Initialize the agent
    agent = Agent()
    print(f"Agent initialized with model: {settings.openai_model}")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down agent...")


# Create FastAPI app
app = FastAPI(
    title="Agentic Framework API",
    description="An OpenAI-powered Q&A system with conversation memory",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agentic Framework API",
        "version": __version__,
        "description": "OpenAI-powered Q&A system",
        "endpoints": {
            "health": "/health",
            "ask": "/api/v1/ask",
            "history": "/api/v1/sessions/{session_id}/history",
            "sessions": "/api/v1/sessions",
            "clear": "/api/v1/sessions/{session_id}"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        openai_configured=bool(settings.openai_api_key)
    )


@app.post("/api/v1/ask", response_model=AnswerResponse, status_code=status.HTTP_200_OK)
async def ask_question(request: QuestionRequest):
    """
    Ask a question to the agent with optional function calling.

    This endpoint accepts a question and returns an AI-generated answer.
    The agent can use tools (function calling) to provide accurate information.

    Tools can be enabled/disabled and filtered via parameters.
    """
    try:
        answer, session_id, usage, tool_calls = await agent.ask(
            question=request.question,
            session_id=request.session_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt,
            enable_tools=request.enable_tools,
            tool_names=request.tool_names
        )

        return AnswerResponse(
            answer=answer,
            session_id=session_id,
            model=settings.openai_model,
            usage=usage,
            tool_calls=tool_calls
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@app.get("/api/v1/sessions/{session_id}/history", response_model=ConversationHistory)
async def get_session_history(session_id: str):
    """
    Get conversation history for a specific session.

    Returns all messages exchanged in the conversation.
    """
    history = agent.get_session_history(session_id)

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return history


@app.get("/api/v1/sessions", response_model=List[str])
async def list_sessions():
    """
    List all active session IDs.

    Returns a list of session IDs that have conversation history.
    """
    return agent.list_sessions()


@app.delete("/api/v1/sessions/{session_id}", response_model=dict)
async def clear_session(session_id: str):
    """
    Clear conversation history for a specific session.

    This permanently deletes all messages for the given session.
    """
    success = agent.clear_session(session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    return {
        "message": f"Session {session_id} cleared successfully",
        "session_id": session_id
    }


@app.get("/api/v1/tools", response_model=ToolsListResponse)
async def list_tools():
    """
    List all available tools (functions) that the agent can call.

    Returns information about each tool including its name, description, and schema.
    """
    tools = default_registry.get_all_tools()
    tool_infos = [
        ToolInfo(
            name=tool.name,
            description=tool.description,
            schema=tool.get_schema()
        )
        for tool in tools
    ]

    return ToolsListResponse(
        tools=tool_infos,
        count=len(tool_infos)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )