# Contributing to Mirror Leech Telegram Bot

Thank you for your interest in contributing! This guide will help you get started.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

---

## 📜 Code of Conduct

Be respectful, inclusive, and constructive. We're building this for the community.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git
- MongoDB & Redis (for local development)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot
git remote add upstream https://github.com/ORIGINAL_OWNER/mirror-leech-telegram-bot.git
```

---

## 🛠️ Development Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
pip install -r config/requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your test credentials
nano .env
```

### 3. Start Development Services

```bash
# Start MongoDB and Redis
docker-compose -f docker-compose.yml up -d mongo redis

# Or use local installations if preferred
```

### 4. Run Development Bot

```bash
# From project root
python -m bot
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_circuit_breaker.py

# Run with coverage
pytest --cov=bot tests/
```

---

## 📁 Project Structure

```
bot/
├── core/               # Core functionality
│   ├── category_b_integration.py
│   ├── circuit_breaker.py
│   ├── smart_retry.py
│   └── priority_queue.py
├── modules/            # Command modules
├── helper/             # Utility functions
└── __main__.py         # Entry point

config/                 # Configuration files
scripts/                # Management scripts
tests/                  # Test suite
docs/                   # Documentation
```

---

## 📝 Coding Standards

### Python Style

- Follow **PEP 8** style guide
- Use **type hints** for function signatures
- Write **docstrings** for all public functions/classes
- Keep functions **focused** and **small**

### Example

```python
from typing import Optional

async def download_file(url: str, max_retries: int = 3) -> Optional[str]:
    """
    Download a file from the given URL.
    
    Args:
        url: The URL to download from
        max_retries: Maximum number of retry attempts
        
    Returns:
        Path to downloaded file, or None if failed
        
    Raises:
        ValueError: If URL is invalid
    """
    # Implementation
    pass
```

### Code Quality

- **Linting:** Use `pylint` or `flake8`
  ```bash
  pylint bot/
  ```

- **Formatting:** Use `black` for automatic formatting
  ```bash
  black bot/ tests/
  ```

- **Type Checking:** Use `mypy` for type validation
  ```bash
  mypy bot/
  ```

---

## 🧪 Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Use `pytest` fixtures for setup/teardown
- Aim for high coverage of critical paths

### Example Test

```python
import pytest
from bot.core.circuit_breaker import CircuitBreaker

@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures():
    """Test that circuit breaker opens after max failures."""
    breaker = CircuitBreaker(max_failures=3, timeout=60)
    
    # Simulate failures
    for _ in range(3):
        await breaker.record_failure()
    
    assert breaker.state == "OPEN"
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_circuit_breaker.py

# With coverage report
pytest --cov=bot --cov-report=html tests/

# Failed tests only
pytest --lf
```

---

## 🔄 Pull Request Process

### 1. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following our style guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add parallel download support

- Implement multi-chunk downloads
- Add progress tracking
- Include tests and documentation"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Formatting, no code change
- `refactor:` Code restructuring
- `test:` Adding tests
- `chore:` Maintenance tasks

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference any related issues
- Screenshots if UI changes
- Test results

### 5. Code Review

- Respond to feedback promptly
- Make requested changes
- Keep discussion constructive

---

## 🐛 Reporting Issues

### Before Submitting

1. **Search existing issues** - It might already be reported
2. **Check documentation** - Issue might be covered
3. **Test latest version** - Bug might be fixed

### Issue Template

```markdown
**Description:**
Clear description of the issue

**Steps to Reproduce:**
1. Step one
2. Step two
3. Expected vs actual behavior

**Environment:**
- OS: Linux/Windows/macOS
- Python version: 3.11
- Docker version: 24.0.0
- Bot version: 3.1.0

**Logs:**
```
Relevant log output
```

**Additional Context:**
Any other relevant information
```

---

## 🎯 Good First Issues

Look for issues labeled `good-first-issue` or `help-wanted` to get started.

---

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if it's already requested
2. Describe the use case clearly
3. Explain why it benefits users
4. Consider implementation complexity

---

## 📞 Getting Help

- **Documentation:** [docs/](docs/)
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Security:** See [SECURITY.md](SECURITY.md) for vulnerabilities

---

## 🏆 Recognition

Contributors will be:
- Listed in project credits
- Mentioned in release notes for significant contributions
- Appreciated by the community!

---

Thank you for contributing! 🙏
