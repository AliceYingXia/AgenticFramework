#!/bin/bash

# Simple script to run the Agentic Framework API

echo "Starting Agentic Framework API..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found!"
    echo "Please create a .env file from .env.example and add your OpenAI API key."
    echo ""
    echo "Run: cp .env.example .env"
    echo "Then edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the API
python -m src.main