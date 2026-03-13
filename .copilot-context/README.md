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
