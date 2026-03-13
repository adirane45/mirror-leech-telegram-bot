# Template: Test Generation

Generate comprehensive pytest tests for:

Module: [MODULE_NAME]
Class/Function to test:
```python
[PASTE CODE TO TEST - include docstrings, 40-80 lines]
```

Requirements:
- pytest + pytest-asyncio (if async)
- Mock external dependencies: [LIST DEPENDENCIES]
- Test coverage target: >80%
- Test cases:
  * Happy path
  * Edge cases: [LIST]
  * Error scenarios: [LIST]
- Use fixtures for: [COMMON SETUP]

Output: tests/[unit|integration]/test_[NAME].py

Include:
- Fixture definitions
- Parametrized tests where applicable
- Explanatory comments
- Mock setup examples
