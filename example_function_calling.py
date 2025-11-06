"""Example demonstrating function calling with the Agentic Framework."""

import requests
import json


def main():
    """Demonstrate function calling features."""
    API_URL = "http://localhost:8000"

    print("=== Agentic Framework - Function Calling Demo ===\n")

    # 1. List available tools
    print("1. Listing Available Tools:")
    print("-" * 50)
    response = requests.get(f"{API_URL}/api/v1/tools")
    tools_data = response.json()

    print(f"Available tools: {tools_data['count']}\n")
    for tool in tools_data['tools']:
        print(f"  • {tool['name']}: {tool['description']}")
    print()

    # 2. Check transaction status
    print("2. Asking about transaction status:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "Can you check the status of transaction TXN-001?",
            "enable_tools": True
        }
    )

    data = response.json()
    print(f"Question: Can you check the status of transaction TXN-001?")
    print(f"Answer: {data['answer']}")

    if data['tool_calls']:
        print(f"\nTools used:")
        for tool_call in data['tool_calls']:
            print(f"  • {tool_call['tool_name']}")
            print(f"    Arguments: {json.dumps(tool_call['arguments'], indent=6)}")
            print(f"    Result: {json.dumps(tool_call['result'], indent=6)}")
    print()

    # 3. Get weather information
    print("3. Asking about weather:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "What's the weather like in San Francisco?",
            "enable_tools": True
        }
    )

    data = response.json()
    print(f"Question: What's the weather like in San Francisco?")
    print(f"Answer: {data['answer']}")

    if data['tool_calls']:
        print(f"\nTools used:")
        for tool_call in data['tool_calls']:
            print(f"  • {tool_call['tool_name']}")
            print(f"    Result: {json.dumps(tool_call['result'], indent=6)}")
    print()

    # 4. Perform calculation
    print("4. Asking for calculation:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "What is 125 * 48 + 67?",
            "enable_tools": True
        }
    )

    data = response.json()
    print(f"Question: What is 125 * 48 + 67?")
    print(f"Answer: {data['answer']}")

    if data['tool_calls']:
        print(f"\nTools used:")
        for tool_call in data['tool_calls']:
            print(f"  • {tool_call['tool_name']}")
            print(f"    Expression: {tool_call['arguments']['expression']}")
            print(f"    Result: {tool_call['result']['result']}")
    print()

    # 5. Multiple tools in one conversation
    print("5. Using multiple tools:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "Check transaction TXN-002 and also tell me the weather in Tokyo",
            "enable_tools": True
        }
    )

    data = response.json()
    print(f"Question: Check transaction TXN-002 and also tell me the weather in Tokyo")
    print(f"Answer: {data['answer']}")

    if data['tool_calls']:
        print(f"\nTools used: {len(data['tool_calls'])}")
        for tool_call in data['tool_calls']:
            print(f"  • {tool_call['tool_name']}: {list(tool_call['arguments'].keys())}")
    print()

    # 6. Disable tools
    print("6. Same question without tools:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "Check transaction TXN-001",
            "enable_tools": False  # Disable function calling
        }
    )

    data = response.json()
    print(f"Question: Check transaction TXN-001")
    print(f"Answer: {data['answer']}")
    print(f"Tools used: {len(data['tool_calls'])}")
    print()

    # 7. Use specific tools only
    print("7. Using only specific tools:")
    print("-" * 50)
    response = requests.post(
        f"{API_URL}/api/v1/ask",
        json={
            "question": "What's 50 + 50 and what's the weather in London?",
            "enable_tools": True,
            "tool_names": ["calculate"]  # Only allow calculate tool
        }
    )

    data = response.json()
    print(f"Question: What's 50 + 50 and what's the weather in London?")
    print(f"Answer: {data['answer']}")
    print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
    print()

    print("=== Demo Complete ===")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server.")
        print("Make sure the server is running: python -m src.main")
    except Exception as e:
        print(f"Error: {e}")