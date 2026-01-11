#!/bin/bash

# SmartHire 2.0 Frontend Startup Script

echo "🎯 Starting SmartHire 2.0 Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo "✅ Dependencies installed!"
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API URL"
fi

# Start the development server
echo "Starting Vite development server..."
npm run dev
