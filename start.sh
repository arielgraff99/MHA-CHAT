#!/bin/bash

# TimelineNarrator Startup Script

echo "🚀 Starting TimelineNarrator..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running again"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Download spaCy model if not available
echo "🧠 Checking spaCy model..."
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo "📥 Downloading spaCy English model..."
    python -m spacy download en_core_web_sm
}

# Initialize database
echo "🗄️  Initializing database..."
python -c "from backend.models.database import create_tables; create_tables()" || {
    echo "⚠️  Database initialization failed. Check your DATABASE_URL in .env"
}

# Build frontend
echo "🏗️  Building frontend..."
npm run build

# Start the application
echo "🌟 Starting TimelineNarrator backend server..."
echo "📍 Backend API: http://localhost:8000"
echo "📍 Frontend: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

python run_backend.py