#!/usr/bin/env bash
#
# GitHub Copilot Context Setup Script
# Creates directory structure and example prompts for Copilot sessions
#
# Usage: ./scripts/setup_copilot_context.sh

set -e

echo "🤖 Setting up GitHub Copilot context structure..."

# Create directory structure
mkdir -p .copilot-context/{templates,plans,sessions}

echo "✅ Created .copilot-context/ folders"

# Copy strategy guide to context folder
if [ -f "docs/GITHUB_COPILOT_STRATEGY.md" ]; then
    cp docs/GITHUB_COPILOT_STRATEGY.md .copilot-context/
    echo "✅ Copied Copilot strategy guide"
fi

# Create template files
cat > .copilot-context/templates/refactoring.md << 'EOF'
# Template: Module Refactoring

I'm refactoring [CLASS_NAME] in [FILE_PATH].

Current code:
```python
[PASTE CODE - 50-100 lines max]
```

Goals:
- [GOAL_1]
- [GOAL_2]
- [GOAL_3]

Requirements:
- Type hints (Python 3.11+)
- Async/await support
- Unit testable
- Pass mypy --strict
- [OTHER_REQUIREMENTS]

Provide:
1. Refactored class implementation
2. Migration guide for existing callers
3. Unit test skeleton
EOF

cat > .copilot-context/templates/type-hints.md << 'EOF'
# Template: Adding Type Hints

Add strict type hints to this Python module:

File: [FILE_PATH]

```python
[PASTE CLASS/FUNCTIONS - signatures preferred, 30-50 lines]
```

Requirements:
- Python 3.11+ type syntax (PEP 585)
- Pass mypy --strict
- Use typing.Protocol for interfaces
- Document complex types with comments
- Show before/after diff

Current mypy errors (if any):
```
[PASTE MYPY OUTPUT]
```
EOF

cat > .copilot-context/templates/test-generation.md << 'EOF'
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
EOF

cat > .copilot-context/templates/debugging.md << 'EOF'
# Template: Debugging Assistance

Debugging [BRIEF_DESCRIPTION]:

Error message:
```
[PASTE FULL ERROR WITH TRACEBACK]
```

Relevant code:
```python
[PASTE 20-40 LINES AROUND ERROR LOCATION]
```

Context:
- Happens when: [TRIGGER CONDITION]
- Expected behavior: [WHAT SHOULD HAPPEN]
- Actual behavior: [WHAT HAPPENS INSTEAD]
- Python version: [VERSION]
- Relevant dependencies: [LIST]

Questions:
1. What's causing this error?
2. How to fix it?
3. How to prevent similar errors?
EOF

cat > .copilot-context/templates/optimization.md << 'EOF'
# Template: Performance Optimization

Optimize this [FUNCTION/CLASS] for performance:

Current implementation:
```python
[PASTE CODE - 30-60 lines]
```

Performance metrics:
- Current: [TIME/MEMORY/THROUGHPUT]
- Target: [DESIRED METRICS]

Areas to optimize:
1. [SPECIFIC AREA 1]
2. [SPECIFIC AREA 2]

Constraints:
- Must maintain async/await
- Cannot change public API
- Must remain readable
- [OTHER CONSTRAINTS]

Provide:
1. Optimized implementation
2. Explanation of changes
3. Expected performance improvement
4. Benchmark/test code to verify
EOF

echo "✅ Created prompt templates in .copilot-context/templates/"

# Create example session plan
cat > .copilot-context/plans/week1-example.md << 'EOF'
# Week 1 Copilot Sessions Plan

## Monday: Module Analysis
**Session 1** (30 min)
- Goal: Categorize 154 core modules
- Prompt: See templates/module-analysis.md
- Expected: Categorization table
- Save to: plans/module-categorization.md

## Tuesday: Consolidation Planning
**Session 2** (30 min)  
- Goal: Plan cache module consolidation
- Prompt: See templates/consolidation-plan.md
- Expected: Merge strategy
- Save to: plans/cache-consolidation.md

## Wednesday: Implementation
**Session 3** (45 min)
- Goal: Implement unified CacheManager
- Prompt: Copy design from Session 2, ask for implementation
- Expected: Working code
- Commit: Immediately after testing

## Thursday: Type Hints
**Session 4** (30 min)
- Goal: Add strict types to cache_system.py
- Prompt: Use templates/type-hints.md
- Expected: Typed code passing mypy --strict
- Verify: Run mypy after applying

## Friday: Testing
**Session 5** (30 min)
- Goal: Generate tests for CacheManager  
- Prompt: Use templates/test-generation.md
- Expected: test_cache_system.py with >80% coverage
- Verify: Run pytest --cov
EOF

echo "✅ Created example week plan"

# Create session log template
cat > .copilot-context/sessions/session-log.md << 'EOF'
# Copilot Session Log

Track your Copilot sessions to improve efficiency over time.

## Session 1: [YYYY-MM-DD] - [TASK NAME]

**Duration**: [XX] minutes  
**Chat #**: New chat
**Goal**: [WHAT YOU WANTED TO ACCOMPLISH]

**Prompt Used**:
```
[PASTE YOUR PROMPT]
```

**Outcome**:
- ✅ Success / ⚠️ Partial / ❌ Failed
- [DESCRIBE WHAT YOU GOT]

**Code Generated**: [LINES OF CODE]
**Tests Generated**: [NUMBER]
**Time Saved**: [ESTIMATE]

**Notes**:
- What worked well
- What didn't work
- Adjustments for next time

---

## Session 2: [YYYY-MM-DD] - [TASK NAME]

[REPEAT FORMAT]

---

## Weekly Summary

**Total Sessions**: [NUMBER]
**Total Time**: [HOURS]
**Code Generated**: [LINES]
**Time Saved vs Manual**: [ESTIMATE]

**Key Learnings**:
1. [LEARNING 1]
2. [LEARNING 2]
EOF

echo "✅ Created session log template"

# Create .gitignore for copilot context
cat > .copilot-context/.gitignore << 'EOF'
# Copilot context folder - git tracking recommendations

# Track templates (reusable)
!templates/

# Track plans (historical reference)
!plans/

# Don't track sessions (personal notes)
sessions/*.md
!sessions/session-log.md
!sessions/README.md

# Don't track generated outputs
*.tmp
*.bak
EOF

echo "✅ Created .gitignore for context folder"

# Create README for context folder
cat > .copilot-context/README.md << 'EOF'
# GitHub Copilot Context Folder

This folder helps organize your GitHub Copilot sessions during the code improvement project.

## Structure

```
.copilot-context/
├── templates/          # Reusable prompt templates
│   ├── refactoring.md
│   ├── type-hints.md
│   ├── test-generation.md
│   ├── debugging.md
│   └── optimization.md
├── plans/             # Week-by-week implementation plans
│   └── week1-example.md
├── sessions/          # Session logs and notes
│   └── session-log.md
└── GITHUB_COPILOT_STRATEGY.md  # Full strategy guide
```

## Usage

### Before Each Session

1. **Choose a template** from `templates/`
2. **Fill in placeholders** with your specific details
3. **Copy to Copilot Chat**
4. **Save useful responses** to `plans/` for reference

### During Implementation

- **Log your sessions** in `sessions/session-log.md`
- **Track what works** and what doesn't
- **Refine prompts** based on results
- **Save context** for complex multi-session tasks

### Tips for Success

1. **Start fresh chats** for new modules/domains
2. **Keep sessions focused** (<30 minutes)
3. **Paste minimal code** (50-100 lines max)
4. **Include errors** when debugging
5. **Iterate in same chat** for related questions

## Example Workflow

```bash
# Day 1: Module analysis
1. Open Copilot Chat (new session)
2. Use template: templates/module-analysis.md (create if needed)
3. Paste output to: plans/module-categorization.md

# Day 2: Implementation
1. Open new Copilot Chat
2. Use template: templates/refactoring.md
3. Get code, test it
4. Log in: sessions/session-log.md
5. Commit changes

# Day 3: Testing
1. Open new chat
2. Use template: templates/test-generation.md
3. Run tests
4. Iterate if needed (same chat)
```

## See Also

- [GITHUB_COPILOT_STRATEGY.md](../docs/GITHUB_COPILOT_STRATEGY.md) - Complete guide
- [IMPROVEMENT_ROADMAP.md](../docs/IMPROVEMENT_ROADMAP.md) - What to build
- [IMPLEMENTATION_CHECKLIST.md](../docs/IMPLEMENTATION_CHECKLIST.md) - Task tracking
EOF

echo "✅ Created README for context folder"

echo ""
echo "================================================"
echo "  GitHub Copilot Context Setup Complete! 🎉"
echo "================================================"
echo ""
echo "Created:"
echo "  📁 .copilot-context/"
echo "     ├── templates/      (5 prompt templates)"
echo "     ├── plans/          (example week plan)"
echo "     ├── sessions/       (session log template)"
echo "     └── README.md       (usage guide)"
echo ""
echo "Next steps:"
echo "  1. Review: cat .copilot-context/README.md"
echo "  2. Check templates: ls -la .copilot-context/templates/"
echo "  3. Read strategy: cat docs/GITHUB_COPILOT_STRATEGY.md"
echo "  4. Start Week 1: Follow week1-example.md plan"
echo ""
echo "💡 Tip: Customize templates based on your workflow!"
echo ""
