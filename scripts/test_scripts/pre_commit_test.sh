#!/bin/bash
# Pre-commit hooks test runner
# Run this to test your changes before committing

set -e

echo "🧪 Running Pre-commit Checks..."
echo "================================"

source .venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate"
    exit 1
}

echo ""
echo "📝 Stage 1: Code Formatting"
echo "----------------------------"
black --check bot/ && echo "✅ Black: Code is formatted" || {
    echo "⚠️  Black: Formatting needed, auto-fixing..."
    black bot/
}

isort --check-only bot/ && echo "✅ isort: Imports sorted" || {
    echo "⚠️  isort: Fixing import order..."
    isort bot/
}

echo ""
echo "🔍 Stage 2: Code Quality"
echo "------------------------"
flake8 bot/ && echo "✅ flake8: No linting errors" || echo "❌ flake8: Issues found"

echo ""
echo "🔐 Stage 3: Security Scan"
echo "-------------------------"
bandit -r bot/ -ll -q && echo "✅ Bandit: No security issues" || echo "⚠️  Bandit: Security warnings"

echo ""
echo "📊 Stage 4: Type Checking"
echo "-------------------------"
mypy bot/ --ignore-missing-imports --no-error-summary && echo "✅ mypy: Type checks passed" || echo "⚠️  mypy: Type issues found"

echo ""
echo "🧪 Stage 5: Run Tests"
echo "---------------------"
pytest tests/ -v --tb=short -q && echo "✅ Tests: All passed" || echo "❌ Tests: Some failed"

echo ""
echo "📈 Stage 6: Coverage Check"
echo "--------------------------"
pytest tests/ --cov=bot --cov-report=term-missing --cov-fail-under=70 -q && echo "✅ Coverage: Above 70%" || echo "⚠️  Coverage: Below 70%"

echo ""
echo "═══════════════════════════════════"
echo "✅ Pre-commit checks complete!"
echo "═══════════════════════════════════"
echo ""
echo "Next steps:"
echo "  git add ."
echo "  git commit -m \"Your commit message\""
echo ""
