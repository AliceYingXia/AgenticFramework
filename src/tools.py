"""Tool system for function calling in the agentic framework."""

from typing import Callable, Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json


class Tool(ABC):
    """Base class for all tools that can be called by the agent."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the OpenAI function schema for this tool.

        Returns:
            Dictionary containing the function schema.
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Result of the tool execution
        """
        pass


class CheckTransactionStatus(Tool):
    """Tool for checking transaction status."""

    def __init__(self):
        super().__init__(
            name="check_transaction_status",
            description="Check the status of a transaction by its ID"
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {
                            "type": "string",
                            "description": "The unique transaction ID to check"
                        }
                    },
                    "required": ["transaction_id"]
                }
            }
        }

    async def execute(self, transaction_id: str) -> Dict[str, Any]:
        """
        Check transaction status (mock implementation).

        In production, this would query a real database or API.
        """
        # Mock transaction data
        mock_transactions = {
            "TXN-001": {"status": "completed", "amount": 150.00, "date": "2024-01-15"},
            "TXN-002": {"status": "pending", "amount": 250.50, "date": "2024-01-16"},
            "TXN-003": {"status": "failed", "amount": 75.25, "date": "2024-01-14"},
        }

        if transaction_id in mock_transactions:
            return {
                "transaction_id": transaction_id,
                **mock_transactions[transaction_id]
            }
        else:
            return {
                "transaction_id": transaction_id,
                "status": "not_found",
                "message": f"Transaction {transaction_id} not found"
            }


class GetWeather(Tool):
    """Tool for getting weather information."""

    def __init__(self):
        super().__init__(
            name="get_weather",
            description="Get current weather information for a location"
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or location"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Temperature unit",
                            "default": "celsius"
                        }
                    },
                    "required": ["location"]
                }
            }
        }

    async def execute(self, location: str, unit: str = "celsius") -> Dict[str, Any]:
        """
        Get weather information (mock implementation).

        In production, this would call a real weather API.
        """
        # Mock weather data
        mock_weather = {
            "san francisco": {"temp": 18, "condition": "Partly cloudy", "humidity": 65},
            "new york": {"temp": 12, "condition": "Sunny", "humidity": 45},
            "london": {"temp": 10, "condition": "Rainy", "humidity": 80},
            "tokyo": {"temp": 22, "condition": "Clear", "humidity": 50},
        }

        location_lower = location.lower()
        if location_lower in mock_weather:
            weather = mock_weather[location_lower]
            temp = weather["temp"]

            # Convert to fahrenheit if needed
            if unit == "fahrenheit":
                temp = (temp * 9/5) + 32

            return {
                "location": location,
                "temperature": round(temp, 1),
                "unit": unit,
                "condition": weather["condition"],
                "humidity": weather["humidity"]
            }
        else:
            return {
                "location": location,
                "error": f"Weather data not available for {location}"
            }


class Calculate(Tool):
    """Tool for performing mathematical calculations."""

    def __init__(self):
        super().__init__(
            name="calculate",
            description="Perform mathematical calculations"
        )

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }

    async def execute(self, expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression.

        Uses safe evaluation to prevent code injection.
        """
        try:
            # Safe evaluation - only allow basic math operations
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return {
                    "expression": expression,
                    "error": "Invalid characters in expression. Only numbers and +, -, *, /, (, ) are allowed."
                }

            result = eval(expression, {"__builtins__": {}}, {})
            return {
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": f"Calculation error: {str(e)}"
            }


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return await tool.execute(**kwargs)


# Global tool registry with default tools
default_registry = ToolRegistry()
default_registry.register(CheckTransactionStatus())
default_registry.register(GetWeather())
default_registry.register(Calculate())