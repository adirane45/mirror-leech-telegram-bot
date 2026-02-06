# CodeScene Refactoring Implementation Checklist

This checklist guides systematic implementation of CodeScene findings.

---

## Phase 1: Immediate Fixes (1-2 days)

### Quick Wins - Already Completed ✅
- [x] Clarify HACK comment in `yt_dlp_download.py` 
  - Replaced vague "Hack" with detailed explanation
  - Documented the filename tracking mechanism

### Phase 1 TODOs (2-4 hours)
- [ ] Review third-party code policy
  - [ ] Decide on qBittorrent plugin modifications
  - [ ] Contact plugin maintainers if needed
  - [ ] Document policy for third-party code

- [ ] Generate baseline metrics
  - [ ] Record current code statistics
  - [ ] Run CodeScene analysis and save results
  - [ ] Document current technical debt baseline
  - [ ] Create dashboard/report template

- [ ] Team awareness
  - [ ] Share CodeScene report with team
  - [ ] Discuss refactoring priorities
  - [ ] Allocate resources for upcoming work

---

## Phase 2: High-Impact Refactoring (1-2 weeks)

### RedisManager Refactoring (8 hours)

**Preparation** (1 hour)
- [ ] Review `bot/core/redis_manager.py` completely
- [ ] List all 21 methods and group by responsibility
- [ ] Create refactoring design document
- [ ] Get code review approval

**Implementation** (5 hours)
- [ ] Create `bot/core/repositories/` directory structure
  - [ ] Create `bot/core/repositories/__init__.py`
  - [ ] Create `bot/core/repositories/base.py` with Repository base class
  - [ ] Create `bot/core/repositories/cache_repository.py`
  - [ ] Create `bot/core/repositories/session_repository.py`
  - [ ] Create `bot/core/repositories/token_repository.py`
  - [ ] Create `bot/core/repositories/config_repository.py`
  - [ ] Create `bot/core/repositories/connection_manager.py`

- [ ] Implement each repository
  - [ ] Write full implementation
  - [ ] Add docstrings
  - [ ] Add type hints
  - [ ] Add error handling

**Testing** (1.5 hours)
- [ ] Create `tests/test_cache_repository.py`
- [ ] Create `tests/test_session_repository.py`
- [ ] Create `tests/test_token_repository.py`
- [ ] Write unit tests for each repository (80%+ coverage)
- [ ] Write integration tests
- [ ] Run full test suite

**Migration** (0.5 hours)
- [ ] Update imports in dependent files
- [ ] Run tests after each file update
- [ ] Update documentation

### DbManager Refactoring (8 hours)
- [ ] Review `bot/helper/ext_utils/db_handler.py`
- [ ] Create repository pattern structure
- [ ] Implement UserRepository
- [ ] Implement LogRepository
- [ ] Implement ConfigRepository
- [ ] Implement TokenRepository
- [ ] Create comprehensive tests
- [ ] Update all callers
- [ ] Run full test suite

### JobFunctions Refactoring (8 hours)
- [ ] Analyze `integrations/sabnzbdapi/job_functions.py`
- [ ] Create manager classes structure
- [ ] Implement JobStatusManager
- [ ] Implement JobHistoryManager
- [ ] Implement JobQueueManager
- [ ] Implement JobConfigManager
- [ ] Create unit tests
- [ ] Update all integration points
- [ ] Verify no regression

### Verification & Documentation (2 hours)
- [ ] Run CodeScene analysis again
- [ ] Verify technical debt reduction
- [ ] Update API documentation
- [ ] Document new architecture
- [ ] Create migration guide for team

---

## Phase 3: Medium-Priority Function Refactoring (2-4 weeks)

### Hotspot Functions First

**Week 1: Critical Path Functions**
- [ ] `bot/modules/mirror_leech.py:new_event()` (296 lines)
  - [ ] Identify sections/concerns
  - [ ] Create helper classes/methods
  - [ ] Extract and test each part
  - [ ] Verify download flow works

- [ ] `bot/modules/bot_settings.py:edit_bot_settings()` (298 lines)
  - [ ] Apply Strategy pattern (see guide)
  - [ ] Extract setting validators
  - [ ] Extract setting appliers
  - [ ] Create comprehensive tests

**Week 2: Dashboard & Status Functions**
- [ ] `bot/core/web_dashboard.py:_get_dashboard_html()` (475 lines)
  - [ ] Split into data gathering phase
  - [ ] Split into formatting phase
  - [ ] Split into HTML generation phase
  - [ ] Use HtmlBuilder or template engine

- [ ] `bot/helper/common.py:before_start()` (343 lines)
  - [ ] Extract initialization steps
  - [ ] Create initialization manager
  - [ ] Test each step independently

**Week 3: Download-Related Functions**
- [ ] `bot/helper/mirror_leech_utils/download_utils/jd_download.py:add_jd_download()` (259 lines)
- [ ] `bot/modules/users_settings.py:get_user_settings()` (295 lines)
- [ ] `bot/modules/users_settings.py:edit_user_settings()` (145 lines)
- [ ] `bot/helper/listeners/task_listener.py:on_download_complete()` (251 lines)

**Week 4: Remaining Long Functions**
- [ ] Process remaining 19 long functions
- [ ] Follow same extraction patterns
- [ ] Maintain 80%+ test coverage
- [ ] Document changes

### Testing Throughout
- [ ] Run unit tests after each extraction
- [ ] Run integration tests weekly
- [ ] No regressions allowed
- [ ] Coverage should not decrease

---

## Phase 4: Cleanup & Optimization (1 week)

### Code Cleanup
- [ ] Remove deprecated methods from RedisManager
- [ ] Remove deprecated methods from DbManager
- [ ] Consolidate duplicate utility functions
- [ ] Clean up imports

### Documentation
- [ ] Update architecture documentation
- [ ] Update API documentation  
- [ ] Create developer guide for new patterns
- [ ] Update contribution guidelines

### Performance Validation
- [ ] Run performance benchmarks
- [ ] Compare before/after metrics
- [ ] Optimize hot paths if needed
- [ ] Document performance characteristics

### Final Verification
- [ ] Run CodeScene analysis (full)
- [ ] Verify 50%+ technical debt reduction
- [ ] Review code coverage (target 85%+)
- [ ] Get team sign-off

---

## Success Criteria

### Code Quality Metrics

- [ ] **Cyclomatic Complexity**: Average < 5 per function
- [ ] **Function Length**: 95% of functions < 50 lines
- [ ] **Class Methods**: Max 10-12 methods per class
- [ ] **Technical Debt**: Reduced from 224 hours to < 50 hours
- [ ] **Code Coverage**: 85%+ overall coverage

### Team Readiness

- [ ] All team members understand new patterns
- [ ] New developers can navigate codebase easily
- [ ] Documentation is complete and current
- [ ] Code review process updated for new patterns

### Metrics Tracking

Track these metrics over time:
```
Week 1: Baseline collected
Week 2-4: Phase 2 (God Objects) reduction
Week 5-8: Phase 3 (Long Functions) reduction
Week 9: Phase 4 (Cleanup & Optimization)
```

Create a metrics dashboard:
```python
# metrics/codescene_tracking.py
BASELINE = {
    "god_objects": 4,
    "long_functions": 33,
    "technical_debt_hours": 224.0,
    "avg_complexity": 4.2,
    "avg_function_length": 87,
    "code_coverage": 0.72
}

TARGETS = {
    "god_objects": 0,
    "long_functions": 0,
    "technical_debt_hours": 30.0,
    "avg_complexity": 2.8,
    "avg_function_length": 35,
    "code_coverage": 0.85
}
```

---

## Risk Mitigation

### For Each Major Refactoring

1. **Branch Strategy**
   - [ ] Create feature branch
   - [ ] Keep PR focused (one class/section)
   - [ ] Limit to 300 lines changed per PR
   - [ ] Get 2 code reviews minimum

2. **Testing Strategy**
   - [ ] Existing tests must still pass
   - [ ] Add new tests for extracted code
   - [ ] Run full suite before merge
   - [ ] No coverage regressions

3. **Rollback Plan**
   - [ ] Keep original code commented (temporarily)
   - [ ] Document rollback procedure
   - [ ] Have health check ready
   - [ ] Deploy in stages

### Monitoring After Deployment

- [ ] Watch error logs for 24 hours
- [ ] Monitor performance metrics
- [ ] Have rollback command ready
- [ ] Schedule post-deployment review

---

## Communication Plan

### Week 0: Planning
- [ ] Share CodeScene report
- [ ] Present analysis findings
- [ ] Get team buy-in
- [ ] Assign owners

### Weekly During Implementation
- [ ] Stand-up meetings
- [ ] Progress updates
- [ ] Blockers/challenges discussion
- [ ] Adjustment of plan if needed

### Completion
- [ ] Final metrics presentation
- [ ] Lessons learned documentation
- [ ] Team retrospective
- [ ] Plan for ongoing code quality

---

## Tools & Scripts

Create helper scripts:

```bash
# scripts/refactor_tracking.sh
#!/bin/bash
# Track refactoring progress

echo "=== Refactoring Progress ==="
echo ""
echo "God Objects Remaining:"
python3 scripts/analyze_complexity.py | grep "God object" | wc -l

echo ""
echo "Long Functions Remaining:"
python3 scripts/analyze_complexity.py | grep "Long function" | wc -l

echo ""
echo "Code Coverage:"
pytest --cov=bot --cov-report=term-only | tail -1

echo ""
echo "Technical Debt Hours:"
cat .codescene/reports/tech_debt_*.json | \
  python3 -c "import json, sys; print(json.load(sys.stdin).get('total_debt_hours', '?'))"
```

---

## Timeline Summary

| Phase | Duration | Effort | Impact |
|-------|----------|--------|--------|
| **Phase 1** | 1-2 days | 2 hrs | Setup & baseline |
| **Phase 2** | 1-2 weeks | 32 hrs | Critical refactoring |
| **Phase 3** | 2-4 weeks | 66 hrs | Function extraction |
| **Phase 4** | 1 week | 10 hrs | Cleanup & validation |
| **TOTAL** | **3-8 weeks** | **110 hrs** | **50%+ debt reduction** |

---

## Next Steps

1. **Review** this checklist with team
2. **Assign** owners for each phase
3. **Schedule** weekly check-ins
4. **Start** Phase 1 improvements this week
5. **Plan** Phase 2 kickoff for next sprint

---

**Document Updated**: February 6, 2026  
**Status**: Ready for implementation  
**Approval**: [Team lead signature space]
