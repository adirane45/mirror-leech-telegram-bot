# Contributing to Mirror-Leech Telegram Bot

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for local testing)
- Git
- Basic knowledge of Python, Telegram Bot API, and async programming

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
   cd mirror-leech-telegram-bot
   ```

2. **Create virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install-dev
   ```

4. **Setup environment**
   ```bash
   make init-env
   # Edit config/.env.production with your credentials
   ```

5. **Start services**
   ```bash
   make up
   ```

## Project Structure

```
src/
├── bot/           # Telegram bot logic & handlers
├── web/           # FastAPI web server
└── api/           # API endpoints

deployment/
├── compose/       # Docker Compose configurations
├── docker/        # Dockerfile & build context
└── scripts/       # Deployment automation

tests/            # Test suite
docs/             # Documentation
requirements/     # Dependency management
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

Follow these principles:
- **Single Responsibility**: Each function/class should do one thing well
- **Async-first**: Use async/await for I/O operations
- **Error Handling**: Handle errors gracefully with proper logging
- **Type Hints**: Use type hints for function signatures (optional for internal logic)
- **Documentation**: Add docstrings to public functions

### 3. Code Quality

Before committing, run:
```bash
make lint       # Check for issues
make format     # Format code automatically
make test       # Run tests
```

### 4. Testing

- Write tests for new features
- Ensure tests pass: `make test`
- Aim for >80% code coverage

```bash
# Run specific test
pytest tests/test_module.py::TestClass::test_method -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### 5. Documentation

- Update README, docs, or CHANGELOG as needed
- Add docstrings using Google style:
  ```python
  def fetch_file(file_id: str, timeout: int = 30) -> bytes:
      """Fetch file from Telegram.
      
      Args:
          file_id: Telegram file ID
          timeout: Request timeout in seconds
          
      Returns:
          File bytes data
          
      Raises:
          FileNotFoundError: If file not found
          TimeoutError: If request exceeds timeout
      """
  ```

### 6. Commit & Push

```bash
git add .
git commit -m "type: description"  # See commit types below
git push origin feature/your-feature-name
```

#### Commit Types
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code formatting (black, isort)
- `refactor:` Code restructuring
- `perf:` Performance improvement
- `test:` Test addition/modification
- `chore:` Build, CI, or dependency updates

### 7. Create Pull Request

- Push your branch to GitHub
- Create PR with clear title and description
- Link related issues: `Closes #123`
- Request review from maintainers

## Code Standards

### Python Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for formatting (100 char line limit)
- Use [isort](https://pycqa.github.io/isort/) for import sorting

### Async Best Practices
- Use `asyncio` for concurrent operations
- Avoid blocking calls in async functions
- Use context managers for resource management

### Error Handling
```python
try:
    result = await some_async_operation()
except SpecificError as e:
    LOGGER.error(f"Operation failed: {e}", exc_info=True)
    raise
except Exception as e:
    LOGGER.exception("Unexpected error")
    raise
```

### Logging
```python
from bot import LOGGER

LOGGER.info("Starting operation")
LOGGER.warning("Potential issue")
LOGGER.error("Error occurred")
LOGGER.debug("Debug information")
```

## Testing Guidelines

**Unit Tests**
- Test individual functions in isolation
- Mock external dependencies
- Use `pytest` with fixtures

**Integration Tests**
- Test components working together
- Use real services (Redis, MongoDB) in containers
- Mark with `@pytest.mark.integration`

**Performance Tests**
- Profile critical paths
- Test with realistic data volumes
- Mark with `@pytest.mark.slow`

Example:
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_download_file():
    """Test file download functionality."""
    with patch('src.bot.clients.aria2') as mock_aria2:
        mock_aria2.add.return_value = "gid-123"
        
        result = await download_file("http://example.com/file.zip")
        
        assert result == "gid-123"
        mock_aria2.add.assert_called_once()
```

## Reporting Issues

When reporting bugs:
1. **Title**: Clear, descriptive
2. **Description**: 
   - What happened
   - What should have happened
   - Steps to reproduce
3. **Environment**:
   - OS version
   - Python version
   - Bot version
4. **Logs**: Relevant error logs or stack traces
5. **Screenshots**: If UI-related

## Documentation

- **README.md**: Project overview, quick start
- **docs/**: Detailed documentation
- **docs/runbooks/**: Operations & troubleshooting
- **CHANGELOG.md**: Version history
- **Code Comments**: Explain *why*, not *what*

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v3.x.x`
4. Push tag: `git push origin v3.x.x`
5. GitHub Actions publishes release automatically

## Questions?

- Check existing [Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues)
- Read [Docs](https://github.com/adirane45/mirror-leech-telegram-bot/blob/main/docs/)
- Ask in [Discussions](https://github.com/adirane45/mirror-leech-telegram-bot/discussions)

Thank you for contributing! 🎉
