
# Function Calling Guide

Complete guide to using function calling (tools) in the Agentic Framework.

## Overview

Function calling allows the AI agent to use tools to perform specific tasks like:
- Checking transaction status
- Getting weather information
- Performing calculations
- And any custom tools you create

The agent automatically decides when to use tools based on the user's question.

## Quick Start

### 1. Basic Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "Check the status of transaction TXN-001",
        "enable_tools": True  # Enable function calling
    }
)

data = response.json()
print(data["answer"])
print(data["tool_calls"])  # See which tools were used
```

### 2. cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the weather in Tokyo?",
    "enable_tools": true
  }'
```

## Available Tools

### 1. check_transaction_status

Check the status of a transaction by ID.

**Parameters:**
- `transaction_id` (string, required): The transaction ID to check

**Example:**
```json
{
  "question": "What's the status of transaction TXN-002?",
  "enable_tools": true
}
```

**Response:**
```json
{
  "transaction_id": "TXN-002",
  "status": "pending",
  "amount": 250.50,
  "date": "2024-01-16"
}
```

### 2. get_weather

Get current weather information for a location.

**Parameters:**
- `location` (string, required): City name
- `unit` (string, optional): "celsius" or "fahrenheit" (default: "celsius")

**Example:**
```json
{
  "question": "What's the weather in New York in fahrenheit?",
  "enable_tools": true
}
```

**Response:**
```json
{
  "location": "New York",
  "temperature": 53.6,
  "unit": "fahrenheit",
  "condition": "Sunny",
  "humidity": 45
}
```

### 3. calculate

Perform mathematical calculations.

**Parameters:**
- `expression` (string, required): Math expression to evaluate

**Example:**
```json
{
  "question": "Calculate 125 * 48 + 67",
  "enable_tools": true
}
```

**Response:**
```json
{
  "expression": "125 * 48 + 67",
  "result": 6067
}
```

## Advanced Usage

### List Available Tools

```python
response = requests.get("http://localhost:8000/api/v1/tools")
tools = response.json()

for tool in tools["tools"]:
    print(f"{tool['name']}: {tool['description']}")
```

### Enable Specific Tools Only

```python
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "Check transaction TXN-001 and calculate 50 + 50",
        "enable_tools": True,
        "tool_names": ["check_transaction_status"]  # Only this tool
    }
)
```

### Disable All Tools

```python
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "What is 2 + 2?",
        "enable_tools": False  # Agent will answer without using tools
    }
)
```

### Multiple Tools in One Request

The agent can automatically use multiple tools to answer complex questions:

```python
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "Check transaction TXN-001, tell me the weather in London, and calculate 100 * 5",
        "enable_tools": True
    }
)

# The agent will call all three tools automatically
tool_calls = response.json()["tool_calls"]
print(f"Used {len(tool_calls)} tools")
```

## Creating Custom Tools

### Step 1: Create a Tool Class

```python
from src.tools import Tool
from typing import Dict, Any

class MyCustomTool(Tool):
    """Custom tool description."""

    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="What this tool does"
        )

    def get_schema(self) -> Dict[str, Any]:
        """Define the tool schema for OpenAI."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Parameter description"
                        },
                        "param2": {
                            "type": "number",
                            "description": "Another parameter"
                        }
                    },
                    "required": ["param1"]
                }
            }
        }

    async def execute(self, param1: str, param2: float = 0.0) -> Dict[str, Any]:
        """Execute the tool logic."""
        # Your custom logic here
        result = f"Processed {param1} with {param2}"
        return {
            "result": result,
            "param1": param1,
            "param2": param2
        }
```

### Step 2: Register the Tool

```python
from src.tools import default_registry

# Register your custom tool
custom_tool = MyCustomTool()
default_registry.register(custom_tool)
```

### Step 3: Use It

```python
response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "Use my custom tool with param1='test'",
        "enable_tools": True
    }
)
```

## Tool Response Format

When tools are used, the response includes a `tool_calls` array:

```json
{
  "answer": "The transaction TXN-001 is completed...",
  "session_id": "abc-123",
  "model": "gpt-4-turbo-preview",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 75,
    "total_tokens": 225
  },
  "tool_calls": [
    {
      "tool_name": "check_transaction_status",
      "arguments": {
        "transaction_id": "TXN-001"
      },
      "result": {
        "transaction_id": "TXN-001",
        "status": "completed",
        "amount": 150.00,
        "date": "2024-01-15"
      }
    }
  ],
  "timestamp": "2024-01-16T10:30:00Z"
}
```

## Best Practices

### 1. Clear Tool Descriptions

Make tool descriptions clear so the AI knows when to use them:

```python
Tool(
    name="send_email",
    description="Send an email to a recipient with subject and body"
)
```

### 2. Validate Inputs

Always validate inputs in your tool's `execute` method:

```python
async def execute(self, email: str, **kwargs):
    if "@" not in email:
        return {"error": "Invalid email format"}
    # ... rest of logic
```

### 3. Handle Errors Gracefully

Return error information instead of raising exceptions:

```python
async def execute(self, **kwargs):
    try:
        result = perform_operation()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4. Keep Tools Focused

Each tool should do one thing well:

- ✅ Good: `check_transaction_status` - checks one transaction
- ❌ Bad: `manage_all_transactions` - too broad

### 5. Use Descriptive Parameter Names

```python
# Good
"transaction_id": "The unique ID of the transaction to check"

# Bad
"id": "An ID"
```

## Examples

### Example 1: Transaction Lookup

**Request:**
```python
requests.post(url, json={
    "question": "What's the status of TXN-003?",
    "enable_tools": True
})
```

**Response:**
```
The transaction TXN-003 has failed. It was for an amount of $75.25 on 2024-01-14.
```

### Example 2: Weather Query

**Request:**
```python
requests.post(url, json={
    "question": "Is it warm in San Francisco right now?",
    "enable_tools": True
})
```

**Response:**
```
Yes, it's quite pleasant in San Francisco. The current temperature is 18°C (64°F)
with partly cloudy conditions and 65% humidity.
```

### Example 3: Calculation

**Request:**
```python
requests.post(url, json={
    "question": "If I buy 15 items at $12.50 each, what's the total?",
    "enable_tools": True
})
```

**Response:**
```
The total would be $187.50 (15 × 12.50 = 187.5).
```

## Troubleshooting

### Tools Not Being Called

**Problem:** Agent doesn't use tools even when appropriate.

**Solutions:**
1. Check `enable_tools` is `true` in request
2. Make tool descriptions more specific
3. Ask questions that clearly need the tool
4. Verify tool is registered: `GET /api/v1/tools`

### Tool Execution Errors

**Problem:** Tool returns errors or unexpected results.

**Solutions:**
1. Check tool's `execute` method handles all parameter combinations
2. Add input validation
3. Return descriptive error messages
4. Test tool independently before integration

### Wrong Tool Called

**Problem:** Agent uses incorrect tool for the question.

**Solutions:**
1. Improve tool description clarity
2. Make parameter descriptions more specific
3. Use `tool_names` to restrict available tools
4. Rephrase the question to be more explicit

## API Reference

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | string | required | The question to ask |
| `enable_tools` | boolean | `true` | Enable/disable function calling |
| `tool_names` | array[string] | `null` | Specific tools to enable (null = all) |
| `session_id` | string | auto | Session ID for context |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_tokens` | integer | 1000 | Max tokens in response |

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | The agent's final answer |
| `session_id` | string | Session ID for this conversation |
| `model` | string | Model used |
| `usage` | object | Token usage statistics |
| `tool_calls` | array | Tools that were called |
| `timestamp` | datetime | Response timestamp |

## Performance Considerations

- **Token Usage**: Each tool call adds to token count
- **Latency**: Multiple tool calls increase response time
- **Rate Limits**: Consider OpenAI API rate limits

## Security

- **Input Validation**: Always validate tool parameters
- **Sandboxing**: Tools should be sandboxed if executing code
- **Access Control**: Implement authentication for sensitive tools
- **Audit Logging**: Log all tool executions for security auditing

## See Also

- [Main README](README.md) - General framework documentation
- [Testing Guide](TESTING.md) - Testing function calling
- [API Documentation](http://localhost:8000/docs) - Interactive API docs