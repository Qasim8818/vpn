#!/bin/bash
# Setup script for Local Agentic Workflow
# Installs all dependencies and configures the system

set -e

echo "🚀 Setting up Local Agentic Workflow..."
echo "========================================\n"

# Check Python version
echo "✓ Checking Python installation..."
python3 --version

# Create virtual environment (optional but recommended)
echo "\n✓ Creating Python virtual environment (optional)..."
if ! python3 -m venv venv; then
    echo "Note: Virtual environment creation failed. Using system Python."
fi

# Activate virtual environment if it was created
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install Python dependencies
echo "\n✓ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "\n✓ Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not installed. Visit https://ollama.com to install."
    echo "    After installation, pull models with:"
    echo "    ollama pull deepseek-r1:14b"
    echo "    ollama pull nomic-embed-text"
else
    ollama --version
    
    # Pull models if not already present
    echo "\n✓ Ensuring models are available..."
    ollama pull deepseek-r1:14b || echo "Model already exists"
    ollama pull nomic-embed-text || echo "Model already exists"
fi

echo "\n✓ Checking Docker for Qdrant..."
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not installed. Visit https://docker.com to install."
    echo "    After installation, run:"
    echo "    docker run -d -p 6333:6333 qdrant/qdrant"
else
    docker --version
    
    # Start Qdrant if not already running
    echo "\n✓ Starting Qdrant vector database..."
    docker run -d -p 6333:6333 --name qdrant qdrant/qdrant 2>/dev/null || echo "Qdrant already running"
fi

echo "\n========================================"
echo "✓ Setup complete!"
echo "========================================\n"

echo "📚 Next steps:"
echo "  1. Interactive mode:  python3 agent_cli.py"
echo "  2. Daemon mode:       python3 agent_daemon.py"
echo "  3. Examples:          python3 examples.py"
echo "  4. Health check:      python3 -c 'from local_agent import LocalAgent; LocalAgent().show_status()'"
echo "\nEnjoy your private, self-learning AI agent! 🤖\n"
