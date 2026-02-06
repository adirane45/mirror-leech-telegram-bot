# CodeScene Analysis for MLTB

This directory contains CodeScene configuration and analysis reports for code health monitoring.

## Setup

### 1. Save Your Personal Access Token

Create a `.token` file in this directory (already gitignored):

```bash
echo "your_personal_access_token_here" > .codescene/.token
chmod 600 .codescene/.token
```

Or set as environment variable:

```bash
export CODESCENE_TOKEN="your_personal_access_token_here"
```

### 2. Run Analysis

```bash
# Full analysis (all metrics)
bash scripts/codescene_analyze.sh full

# Quick analysis (complexity only)
bash scripts/codescene_analyze.sh quick

# Hotspot analysis (change patterns)
bash scripts/codescene_analyze.sh hotspots
```

## Analysis Types

### Complexity Analysis
- Identifies functions with high cyclomatic complexity
- Highlights refactoring opportunities
- Tracks cognitive complexity

### Hotspot Analysis
- Finds files with high change frequency + high complexity
- Prioritizes refactoring efforts
- Detects stability issues

### Code Health Analysis
- Documentation coverage
- Code structure quality
- Maintainability metrics
- Anti-pattern detection

### Technical Debt Analysis
- TODO/FIXME/HACK tracking
- Deprecated code detection
- Code smell identification
- Effort estimation

## Reports Location

All reports are saved in `.codescene/reports/` with timestamps:
- `complexity_YYYYMMDD_HHMMSS.json`
- `hotspots_YYYYMMDD_HHMMSS.json`
- `health_YYYYMMDD_HHMMSS.json`
- `tech_debt_YYYYMMDD_HHMMSS.json`

## Understanding Results

### Complexity Ratings
- **Low** (1-5): Easy to maintain
- **Medium** (6-10): Acceptable
- **High** (11-20): Consider refactoring
- **Very High** (21+): Urgent refactoring needed

### Hotspot Priorities
- **Critical**: High change rate + high complexity
- **High**: Frequent changes, moderate complexity
- **Medium**: Occasional changes
- **Low**: Stable code

### Health Score (0-100)
- **90-100**: Excellent
- **70-89**: Good
- **50-69**: Needs improvement
- **<50**: Critical attention needed

## Integration with Development

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
bash scripts/codescene_analyze.sh quick
```

### CI/CD Integration
Add to your CI pipeline to track code health trends over time.

## Getting Your Token

1. Visit https://codescene.io/
2. Sign in or create account
3. Go to Settings > Personal Access Tokens
4. Generate new token
5. Save securely in `.codescene/.token`

## Best Practices

1. **Run before major refactoring** to establish baseline
2. **Run after refactoring** to measure improvement
3. **Monitor trends** over time, not absolute values
4. **Focus on hotspots** - highest ROI for refactoring
5. **Document decisions** when ignoring recommendations

## Support

For issues or questions:
- CodeScene Docs: https://docs.codescene.io/
- Project Issues: Create issue in repository
