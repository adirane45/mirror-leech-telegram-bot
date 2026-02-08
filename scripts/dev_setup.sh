#!/bin/bash
# Quick setup script for development environment

set -e

echo "🚀 Setting up development environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing production dependencies..."
pip install -r config/requirements.txt

echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data/{backups,certs,downloads,logs,thumbnails,tokens}
mkdir -p clients/{aria2,qbittorrent,sabnzbd}/config

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📝 Quick start commands:"
echo "  source .venv/bin/activate          # Activate virtual environment"
echo "  pre-commit run --all-files         # Run pre-commit checks"
echo "  pytest tests/ -v                   # Run tests"
echo "  black bot/                         # Format code"
echo "  flake8 bot/                        # Lint code"
echo "  mypy bot/                          # Type check"
echo ""
echo "🎯 Phase 1 Quality Gates Implementation:"
echo "  ✅ Pre-commit hooks configured"
echo "  ✅ Code quality tools installed"
echo "  ✅ Security scanning enabled"
echo "  ✅ Dependabot configured"
echo ""
