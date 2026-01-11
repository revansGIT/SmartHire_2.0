#!/bin/bash

# SmartHire 2.0 Backend Startup Script

echo "🎯 Starting SmartHire 2.0 Backend..."

# Navigate to backend directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/.dependencies_installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    touch .venv/.dependencies_installed
    echo "✅ Dependencies installed!"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Start the backend server
echo "Starting Flask server..."
cd src
python app.py
