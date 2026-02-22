# Mirror-Leech Telegram Bot

Production-ready Telegram bot for multi-protocol downloads, cloud sync, and automated media workflows. Built for reliability, observability, and scale.

## Highlights

- Multi-protocol downloads: HTTP/HTTPS, torrents, NZB, YouTube, Google Drive.
- Cloud sync: Google Drive and 40+ providers via rclone.
- Robust automation: queueing, retries, scheduling, and health checks.
- Monitoring: dashboards, metrics, and log streaming.
- Enterprise extensions: link bypassing, debrid integrations, performance optimizations.

## Quick Start (Docker)

```bash
# Clone
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Configure
cp config/.env.production.example config/.env.production
nano config/.env.production

# Run
docker compose -f deployment/docker-compose.yml up -d --build
```

Verify:
- Send `/ping` to the bot.
- Open the web dashboard: http://localhost:8060

## Configuration

Minimum required keys in config/.env.production:

```env
BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_API=YOUR_API_ID
TELEGRAM_HASH=YOUR_API_HASH
OWNER_ID=YOUR_TELEGRAM_USER_ID
```

See full configuration in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

## Commands

- Full command list: [docs/COMMANDS.md](docs/COMMANDS.md)
- BotFather command list: [docs/TELEGRAM_COMMANDS.txt](docs/TELEGRAM_COMMANDS.txt)
- In-bot list: `/cmdlist`

## Documentation

- Setup: [docs/INSTALLATION.md](docs/INSTALLATION.md)
- Configuration: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- API reference: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- Deployment: [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)
- Roadmap: [docs/FEATURE_IMPLEMENTATION_ROADMAP.md](docs/FEATURE_IMPLEMENTATION_ROADMAP.md)
- Development guide: [docs/DEVELOPMENT_JOURNEY.md](docs/DEVELOPMENT_JOURNEY.md)

## Phase 6-11 Validation

### Short Checklist (User/Client View)

- Phase 6: `/streamlink` works on a replied file; `/log` returns a log file; `/edash` loads.
- Phase 7: `/health`, `/estats`, `/rmon` respond without errors.
- Phase 8: `/eanalytics` and `/equick` return data.
- Phase 9: run phase 9 tests (see below) or verify logs if enabled in workflows.
- Phase 10: run phase 10 tests (core modules only).
- Phase 11: run phase 11 tests (core modules only).

### Step-by-Step Validation

1) Phase 6 (Quick Wins)
- Stream link: reply to a file with `/streamlink` and open the returned URL.
- Web dashboard: open http://localhost:8060 and check status widgets.
- Log access: `/log` should return the current log file.
- Config hot reload: update config/.env.production and restart to confirm no errors.

2) Phase 7 (Performance/Reliability)
- Health: `/health` should return system health summary.
- Metrics: `/estats` and `/rmon` should return resource stats.
- Queue: `/queue` and `/status` should reflect active tasks.

3) Phase 8 (Advanced Intelligence)
- Enhanced analytics: `/eanalytics` should return analytics view.
- Quick overview: `/equick` should return a summary.

4) Phase 9 (Enterprise Features)
- Run tests: `python -m pytest tests/test_phase9_enterprise_features.py -o addopts=""`
- If you use these features in production, check logs for metadata stripping, captcha solving,
  cross-seed actions, and quota bypass steps.

5) Phase 10 (Ecosystem Integrations)
- Run tests: `python -m pytest tests/test_phase10_ecosystem_integrations.py -o addopts=""`
- Phase 10 features are core modules without user-facing commands in this build.

6) Phase 11 (Optimization & Scaling)
- Run tests: `python -m pytest tests/test_phase11_optimization_scaling.py -o addopts=""`
- Phase 11 features are core modules without user-facing commands in this build.

## Reporting Issues and Fixing Errors

### Report Issues

If you see errors or regressions:
1. Capture the command used and full error output.
2. Attach relevant logs from `data/logs/log.txt`.
3. Note environment details (OS, Python version, Docker version).
4. Open a GitHub issue with the above details and steps to reproduce.

### Local Fix Workflow

1. Update dependencies: `pip install -r requirements-dev.txt`
2. Run the failing tests directly.
3. Check logs: `tail -n 200 data/logs/log.txt`
4. Fix code, re-run tests, and verify with `python -m pytest -o addopts=""`.

## License

MIT. See [docs/LICENSE](docs/LICENSE).
