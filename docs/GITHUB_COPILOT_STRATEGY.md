# GitHub Copilot Strategy for Code Improvements

**Purpose**: Maximize GitHub Copilot effectiveness during the 10-week improvement process  
**Goal**: Complete tasks faster with AI assistance while maintaining quality

---

## 🎯 Core Principles

### 1. **Chat Session Management**
- **New chat for new context**: Open new chat when switching domains/modules
- **Token limit awareness**: ~4K-8K tokens per session (≈3K-6K words)
- **Session duration**: Keep focused sessions <30 minutes
- **Context refresh**: Start new chat if losing coherence

### 2. **Prompt Engineering Best Practices**
- **Be specific**: Include file paths, function names, exact requirements
- **Provide context**: Share relevant code snippets, error messages
- **Incremental requests**: Break large tasks into smaller chunks
- **Iterative refinement**: Start broad, then narrow down

### 3. **When to Use Chat vs Inline Suggestions**
- **Use Chat for**: Architecture decisions, refactoring plans, debugging complex issues
- **Use Inline for**: Code completion, simple functions, repetitive patterns
- **Use both**: Review inline suggestions in chat for complex patterns

---

## 📋 Week-by-Week Copilot Strategy

### Week 1: Architecture Audit & Planning

#### Session 1: Module Analysis
**Goal**: Understand current architecture  
**New Chat**: Yes (fresh start)

```
Prompt Template:
"I'm analyzing the src/bot/core/ directory which has 154 Python files. 
I need to consolidate these into domain-based modules. 

Context:
- Project: Telegram bot for file mirroring/leeching
- Current structure: Flat directory with many managers
- Files: [paste ls output]

Task: Help me categorize these files into domains:
1. Download management
2. Storage/caching
3. Monitoring/alerting
4. API/web interface
5. Security
6. Task management

For each file, suggest which domain it belongs to and identify merge candidates."
```

**Expected Output**: Categorization plan  
**Token Usage**: ~2K tokens  
**Follow-up**: Continue in same chat for initial planning

#### Session 2: Consolidation Planning
**New Chat**: No (continue from Session 1)

```
Prompt:
"Based on the categorization, let's plan the first consolidation:

Files to merge:
- cache_manager.py (500 lines)
- advanced_cache.py (800 lines)  
- file_cache_manager.py (300 lines)

Goal: Merge into src/bot/core/storage/cache_system.py

Questions:
1. What's the best way to structure the unified module?
2. Which classes should be kept vs merged?
3. How to handle backward compatibility for imports?

Provide a step-by-step refactoring plan."
```

**Token Usage**: +1.5K tokens (cumulative: 3.5K)  
**Timeline**: 15-20 minutes

#### Session 3: Implementation Assistance
**New Chat**: Yes (different focus - actual code)

```
Prompt:
"I'm refactoring cache modules into a unified system.

Current files:
1. src/bot/core/cache_manager.py:
```python
[paste CacheManager class code - first 50 lines]
```

2. src/bot/core/advanced_cache.py:
```python
[paste key classes/functions]
```

Task: Create a unified CacheManager with:
- Hierarchical caching (L1: memory, L2: Redis, L3: disk)
- Backward compatible API
- Type hints (Python 3.11+)
- Async/await support

Show me the new cache_system.py structure with main classes."
```

**Token Strategy**: Paste only relevant code (not entire files)  
**Expected**: Class structure outline  
**Follow-up**: Iterate on implementation details in same chat

---

### Week 2: Type Safety & Testing

#### Session 4: Type Hint Addition
**New Chat**: Yes (new topic)

```
Prompt:
"I need to add strict type hints to this Python module:

File: src/bot/core/storage/cache_system.py

Current code (without types):
```python
[paste 30-50 lines of untyped code]
```

Requirements:
- Add full type hints (Python 3.11+)
- Use typing.Protocol for interfaces
- Pass mypy --strict
- Document complex types

Show me the typed version with explanations."
```

**Pro Tip**: Include mypy error messages if already run  
**Token-saving trick**: Focus on one class/function at a time

#### Session 5: Unit Test Generation
**New Chat**: Yes (testing context)

```
Prompt:
"Generate comprehensive unit tests for this class:

```python
class CacheManager:
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve from L1 → L2 → L3 cache hierarchy"""
        [paste method implementation]
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Store in all cache levels"""
        [paste method implementation]
```

Requirements:
- Use pytest + pytest-asyncio
- Mock Redis and disk I/O
- Test cache hierarchy fallback
- Test TTL expiration
- Test error handling
- Target: >80% coverage

Generate tests/unit/test_cache_system.py"
```

**Expected**: Complete test file  
**Token Usage**: ~3K tokens  
**Follow-up**: Ask for edge cases if needed

---

### Week 3-4: Refactoring & Consolidation

#### Session 6: Complex Refactoring
**New Chat**: Yes (major refactoring)

```
Prompt:
"I'm consolidating 4 failover-related modules into one:

Current structure:
1. failover_manager.py - Main coordinator (600 lines)
2. failover_cascade_detector.py - Cascade prevention (300 lines)
3. failover_recovery_executor.py - Recovery logic (400 lines)
4. failover_models.py - Data models (200 lines)

Goals:
- Merge into monitoring/failover_system.py
- Use modern Python patterns (dataclasses, protocols)
- Maintain all functionality
- Improve testability

Step 1: Design the unified module structure
Show me:
1. Class hierarchy
2. Public API
3. Internal organization
4. Migration path for existing code"
```

**Token Management**: Start with design, implement in follow-up chats  
**Best Practice**: Save Copilot's response, use in new chat for implementation

#### Session 7: Import Updates (Bulk Changes)
**New Chat**: Yes (different task type)

```
Prompt:
"I've moved cache_manager.py to storage/cache_system.py

Old import: from src.bot.core.cache_manager import CacheManager
New import: from src.bot.core.storage.cache_system import CacheManager

Task: Generate a script to update all imports across the codebase

Requirements:
- Find all import statements
- Update to new paths
- Handle variations (import X, from X import Y, import X as Z)
- Dry-run mode to preview changes
- Backup option

Show me a Python script: scripts/update_imports.py"
```

**Output**: Automated refactoring script  
**Token-saving**: Focus on script logic, not manual updates

---

### Week 5-6: Async Optimization

#### Session 8: Blocking I/O Detection
**New Chat**: Yes (performance focus)

```
Prompt:
"Audit this module for blocking I/O operations:

File: src/bot/helper/ext_utils/download_utils.py

```python
[paste relevant sections - 50-100 lines]
```

Find:
1. Synchronous I/O (requests, open(), time.sleep)
2. Missing async/await
3. Blocking database calls
4. Thread-unsafe operations

For each issue:
- Line number
- Current code
- Async replacement
- Required imports"
```

**Expected**: Detailed audit report  
**Follow-up**: Same chat for specific rewrites

#### Session 9: Async Conversion
**New Chat**: No (continue from Session 8)

```
Prompt:
"Convert this function to async:

```python
def download_file(url: str, dest: str) -> int:
    response = requests.get(url, stream=True)
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return os.path.getsize(dest)
```

Requirements:
- Use httpx for async HTTP
- Use aiofiles for file I/O
- Add proper error handling
- Add type hints
- Add progress callback support
- Write corresponding unit test"
```

**Pro Tip**: Request tests in same prompt for context  
**Token Usage**: ~2K tokens

---

### Week 7-8: Documentation & Quality

#### Session 10: Docstring Generation
**New Chat**: Yes (documentation focus)

```
Prompt:
"Generate Google-style docstrings for this module:

```python
[paste class/function signatures - 40-60 lines]
```

Requirements:
- Google docstring format
- Document all parameters with types
- Include return types
- Add usage examples
- Note exceptions raised
- Add 'See Also' sections for related functions"
```

**Batch Strategy**: Group related functions (5-10 at a time)  
**Token-saving**: Paste signatures only, not full implementations

#### Session 11: Architecture Diagrams
**New Chat**: Yes (visual documentation)

```
Prompt:
"Create Mermaid diagrams for this system:

Components:
1. Download Manager (handles aria2, qbittorrent, yt-dlp)
2. Cache System (L1/L2/L3 hierarchy)
3. Upload Manager (Google Drive, Rclone)
4. Task Coordinator (Celery-based)
5. API Gateway (FastAPI)

Show me:
1. Component diagram (high-level architecture)
2. Sequence diagram (download → cache → upload flow)
3. Class diagram (main classes and relationships)

Use Mermaid syntax for all diagrams."
```

**Output**: Ready-to-use diagrams for docs  
**Token Usage**: ~2-3K tokens

---

### Week 9-10: Testing & Polish

#### Session 12: Integration Test Scenarios
**New Chat**: Yes (complex testing)

```
Prompt:
"Design integration tests for the download pipeline:

Flow:
1. User submits download request via Telegram
2. System validates URL and checks quota
3. Task queued in Celery
4. Download manager selects client (aria2/qbittorrent)
5. File cached during download
6. Upload to Google Drive/Rclone
7. Notification sent to user

Create:
1. Test scenario outlines (Given/When/Then)
2. Mock strategy for external services
3. pytest fixtures needed
4. Assertion points
5. Sample test code for 2-3 key scenarios"
```

**Complex Request**: Break into sub-prompts if response incomplete  
**Token Management**: ~4K tokens, may need follow-up chat

---

## 🎓 Advanced Copilot Techniques

### Technique 1: Context Preservation
**Problem**: Losing context between chats  
**Solution**: Create context files

```python
# .copilot-context/refactoring-plan.md
"""
Current Task: Consolidating cache modules
Started: 2026-03-08
Status: In progress

Decisions Made:
- Using hierarchical cache (L1/L2/L3)
- Redis for L2, disk for L3
- Backward compatible imports with deprecation warnings

Next Steps:
1. Complete CacheManager implementation
2. Update all imports
3. Add tests
"""
```

**Usage**: Paste this context at start of new chat  
**Benefit**: Maintains continuity across sessions

### Technique 2: Prompt Templates
**Create reusable templates for common tasks**

```markdown
# Template: Class Refactoring

I'm refactoring [CLASS_NAME] in [FILE_PATH].

Current code:
```python
[PASTE CODE]
```

Goals:
- [GOAL_1]
- [GOAL_2]
- [GOAL_3]

Requirements:
- Type hints (Python 3.11+)
- Async/await support
- Unit testable
- [OTHER_REQUIREMENTS]

Provide:
1. Refactored class
2. Migration guide for existing usage
3. Unit test skeleton
```

**Save templates** in: `.copilot-context/templates/`

### Technique 3: Iterative Refinement
**Start broad, then zoom in**

```
Chat Flow:
┌─────────────────────────────────────┐
│ Prompt 1: "Design cache system"    │
│ → Get architecture overview         │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Prompt 2: "Detail CacheManager"    │
│ → Get class structure               │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ Prompt 3: "Implement get() method" │
│ → Get specific implementation       │
└─────────────────────────────────────┘
```

**Token Efficiency**: Each prompt builds on previous  
**When to new chat**: After 3-4 iterations or when switching focus

### Technique 4: Error-Driven Development
**Use Copilot to fix errors**

```
Prompt:
"Running mypy --strict gives this error:

```
src/bot/core/cache_manager.py:45: error: 
  Missing return statement [return]
src/bot/core/cache_manager.py:52: error: 
  Argument 1 has incompatible type "str"; expected "bytes" [arg-type]
```

Current code:
```python
[paste problematic section - 10 lines before/after error]
```

Fix these errors while maintaining functionality."
```

**Best Practice**: Include 10 lines of context around error  
**Token-saving**: Only show relevant errors (not all 50+)

### Technique 5: Diff-Based Updates
**For large files, use diff format**

```
Prompt:
"Apply this refactoring to cache_manager.py:

Change: Add type hints to all methods

Show me as a unified diff:
- Only changed lines
- Keep unchanged context minimal (3 lines)
- Include line numbers

Current method signature:
```python
def get(self, key, default=None):
    ...
```

Target:
```python
async def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
    ...
```

Show diff for all 8 methods in the class."
```

**Output**: Easy to review and apply  
**Token-saving**: Diff format is compact

---

## 🚫 Common Pitfalls to Avoid

### Pitfall 1: Information Overload
❌ **Bad**: Paste entire 1000-line file
```
"Refactor this file: [paste entire file]"
```

✅ **Good**: Paste relevant sections
```
"Refactor the CacheManager class (lines 50-150):
```python
[paste just the class]
```
```

### Pitfall 2: Vague Requests
❌ **Bad**: "Make this better"
```
"Improve this code: [paste code]"
```

✅ **Good**: Specific improvements
```
"Improve this code by:
1. Adding type hints
2. Converting to async/await
3. Adding error handling for Redis connection failures
4. Reducing cyclomatic complexity below 10

[paste code]"
```

### Pitfall 3: Not Reviewing Suggestions
❌ **Bad**: Blindly accepting all code

✅ **Good**: Critical review
```
Copilot suggests [code]
↓
Ask: "Explain why you chose this approach vs [alternative]?"
↓
Verify: Run tests, check types, review logic
↓
Iterate: "This fails for edge case X, how to handle?"
```

### Pitfall 4: Ignoring Token Limits
❌ **Bad**: Marathon 2-hour chat session with 50 prompts

✅ **Good**: Focused sessions
```
Session 1: Design (5-6 prompts, 30 min)
[Save output to file]

Session 2: Implementation (5-6 prompts, 30 min)
[Reference previous output]

Session 3: Testing (5-6 prompts, 30 min)
```

### Pitfall 5: No Documentation of Decisions
❌ **Bad**: Lose context between days

✅ **Good**: Document in ADRs
```
After each major decision in Copilot:
1. Save the recommendation to docs/architecture/adr/
2. Include Copilot's reasoning
3. Note alternatives considered
4. Reference in future prompts
```

---

## 📊 Session Planning Guide

### Session Types & Token Budgets

| Session Type | Duration | Prompts | Token Budget | New Chat? |
|--------------|----------|---------|--------------|-----------|
| **Architecture Design** | 30-45 min | 6-8 | 4-6K | Yes |
| **Code Implementation** | 20-30 min | 5-7 | 3-4K | Yes (per module) |
| **Testing** | 20-30 min | 4-6 | 2-3K | Yes |
| **Debugging** | 15-25 min | 3-5 | 2-3K | Yes |
| **Documentation** | 15-20 min | 3-4 | 2K | Yes |
| **Quick Questions** | 5-10 min | 1-2 | <1K | Reuse existing |

### When to Start New Chat

✅ **Start new chat when**:
- Switching to different module/domain
- Previous chat >30 min old
- Copilot responses become generic/repetitive
- Context shifts significantly (e.g., code → docs)
- After implementing major changes
- Error messages indicate context loss

❌ **Don't start new chat when**:
- Asking follow-up questions on same topic
- Iterating on same code section
- Within same 30-minute focused session
- Just got confused response (try rephrasing first)

### Sample Daily Schedule

**Day 1: Cache Module Consolidation**

```
09:00-09:30 | Chat 1: Architecture planning
            | "Design unified cache system..."
            | Output: Design doc
            
09:30-10:00 | Chat 2: CacheManager implementation
            | "Implement CacheManager with [design]..."
            | Output: Core class
            
10:00-10:30 | Chat 3: Helper classes
            | "Implement L1Cache, L2Cache based on..."
            | Output: Supporting classes
            
-- Break --

11:00-11:30 | Chat 4: Unit tests
            | "Generate tests for CacheManager..."
            | Output: test_cache_system.py
            
11:30-12:00 | Chat 5: Import updates
            | "Create script to update imports..."
            | Output: Migration script
            
12:00-12:15 | Chat 6: Documentation
            | "Add docstrings to cache_system.py..."
            | Output: Documented code
```

**Total**: 6 chats, ~2.5 hours, complete one consolidation

---

## 🎯 Prompt Library

### Starting a Refactoring Session
```
"I'm refactoring [MODULE] as part of consolidating [DOMAIN] modules.

Context:
- Project: [PROJECT_TYPE]
- Current: [CURRENT_STATE]
- Goal: [TARGET_STATE]
- Constraints: [PYTHON_VERSION, FRAMEWORKS, ETC]

Files involved:
1. [FILE_1] - [PURPOSE]
2. [FILE_2] - [PURPOSE]

Task: [SPECIFIC_ASK]

Provide: [EXPECTED_OUTPUT_FORMAT]"
```

### Adding Type Hints
```
"Add strict type hints to this [CLASS/FUNCTION]:

```python
[PASTE CODE - 30-50 lines]
```

Requirements:
- Python 3.11+ type syntax
- Pass mypy --strict
- Use typing.Protocol for interfaces
- Document complex types
- Use TypedDict for dict structures

Show before/after diff."
```

### Generating Tests
```
"Generate pytest tests for:

```python
[PASTE CODE TO TEST]
```

Requirements:
- pytest + pytest-asyncio (if async)
- Mock external dependencies: [LIST]
- Test cases: happy path, edge cases, errors
- Target coverage: >80%
- Use fixtures for: [COMMON_SETUP]

Output: Complete test file with explanatory comments."
```

### Performance Optimization
```
"Optimize this [FUNCTION/CLASS] for performance:

Current implementation:
```python
[PASTE CODE]
```

Current performance: [METRICS]
Target: [TARGET_METRICS]

Areas to optimize:
1. [AREA_1]
2. [AREA_2]

Constraints:
- Must remain async
- Cannot change public API
- Maintain readability

Provide optimized version with explanations."
```

### Debugging Assistance
```
"Debugging [ISSUE_DESCRIPTION]:

Error:
```
[PASTE ERROR MESSAGE]
```

Relevant code:
```python
[PASTE 20-30 LINES AROUND ERROR]
```

Context:
- Happens when: [CONDITION]
- Expected: [EXPECTED_BEHAVIOR]
- Actual: [ACTUAL_BEHAVIOR]

What's wrong and how to fix it?"
```

---

## 🔄 Workflow Integration

### Git Workflow with Copilot

```bash
# 1. Create feature branch
git checkout -b refactor/cache-consolidation

# 2. Use Copilot for planning (Chat 1)
# Prompt: "Create consolidation plan for cache modules"
# Save output to: docs/plans/cache-consolidation-plan.md

# 3. Implement with Copilot (Chat 2-3)
# Prompt: "Implement phase 1 of plan: CacheManager"
# Write code with Copilot suggestions

# 4. Test with Copilot (Chat 4)
# Prompt: "Generate tests for CacheManager"
pytest tests/unit/test_cache_system.py

# 5. Review & refine
git diff  # Review changes
# If issues, new Copilot chat with diff

# 6. Commit
git add src/bot/core/storage/cache_system.py tests/
git commit -m "refactor(cache): consolidate cache modules into unified system"

# 7. Document with Copilot (Chat 5)
# Prompt: "Generate ADR for cache consolidation decision"
# Save to: docs/architecture/adr/0001-cache-consolidation.md

git add docs/architecture/adr/
git commit -m "docs: add ADR for cache consolidation"
```

### CI Integration

```yaml
# .github/workflows/copilot-suggestions.yml
name: Copilot Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      # Use Copilot CLI (if available) to review PR
      - name: Copilot PR Review
        run: |
          gh copilot suggest \
            "Review this PR for: 
            1. Type safety issues
            2. Missing tests
            3. Performance concerns
            4. Security issues"
```

---

## 📈 Measuring Copilot Effectiveness

### Track Metrics

```python
# .copilot-metrics/session-log.json
{
  "sessions": [
    {
      "date": "2026-03-08",
      "task": "cache-consolidation",
      "duration_min": 120,
      "chats": 5,
      "tokens_used": 18500,
      "lines_written": 450,
      "lines_per_hour": 225,
      "tests_generated": 12,
      "bugs_prevented": 3,
      "time_saved_estimate_hours": 4
    }
  ]
}
```

### Success Indicators

✅ **Good Session**:
- Clear outcomes after each chat
- Working code with minimal manual fixes
- Tests generated and passing
- Documentation complete
- Time saved vs manual coding

❌ **Poor Session**:
- Copilot giving generic responses
- Lots of back-and-forth on same issue
- Code doesn't work without major changes
- Hitting token limits frequently
- Context lost mid-session

### Improvement Over Time

```
Week 1: Learning curve
  - 60% efficiency (lots of trial & error)
  - 3-4 chats per task
  
Week 3: Finding rhythm
  - 80% efficiency (better prompts)
  - 2-3 chats per task
  
Week 6: Expert usage
  - 90% efficiency (prompt templates)
  - 1-2 chats per task
  
Week 10: Optimized
  - 95% efficiency (predictable patterns)
  - Often 1 chat or inline suggestions sufficient
```

---

## 🎓 Training Resources

### Learn Prompt Engineering
1. **OpenAI Prompt Engineering Guide**
2. **GitHub Copilot Documentation**
3. **Practice**: Start with simple tasks, increase complexity

### Example Learning Path

**Week 1**: Basic prompts
- "Add type hints to this function"
- "Generate tests for this class"
- "Explain this code"

**Week 2**: Context-rich prompts
- Include requirements, constraints
- Reference related code
- Ask for alternatives

**Week 3**: Advanced techniques
- Multi-step reasoning
- Architectural guidance
- Performance optimization

**Week 4+**: Expert level
- Custom prompt templates
- Efficient token management
- Complex refactoring

---

## 📝 Quick Reference Card

### Prompt Checklist
- [ ] Clear goal stated
- [ ] Relevant context provided
- [ ] Constraints specified
- [ ] Expected output format defined
- [ ] Code snippets under 100 lines
- [ ] Specific, not vague

### Session Hygiene
- [ ] New chat for new module/domain
- [ ] Sessions < 30 minutes
- [ ] Save important outputs to files
- [ ] Document decisions in ADRs
- [ ] Review and test all suggestions
- [ ] Commit frequently

### Token Management
- [ ] Paste only relevant code
- [ ] Use diffs for large files
- [ ] Start new chat at 4K tokens
- [ ] Reference saved outputs vs re-pasting
- [ ] Break large tasks into smaller chats

---

## 🚀 Ready to Start!

1. **Read this guide** - Familiarize yourself with techniques
2. **Create `.copilot-context/` folder** - Store context and templates
3. **Review Week 1 action list** - `../.copilot-context/plans/week1-action-list-2026-03-08.md`
4. **Start Week 1 Session 1** - Architecture audit
5. **Track your sessions** - Learn what works for you
6. **Iterate and improve** - Refine your prompts over time

**Remember**: GitHub Copilot is a tool to augment your expertise, not replace it. Always review, test, and validate suggestions!

---

**Related Documents**:
- [IMPROVEMENT_ROADMAP.md](IMPROVEMENT_ROADMAP.md) - What to build
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) - Week-by-week tasks
- [QUICK_REFERENCE_PRIORITIES.md](QUICK_REFERENCE_PRIORITIES.md) - Priority actions
- `../.copilot-context/plans/week1-action-list-2026-03-08.md` - Current execution priorities

**Good luck! 🤖✨**
