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
