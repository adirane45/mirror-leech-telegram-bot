# Documentation Index

## Enhanced MLTB v3.1.0 - Complete Documentation

Welcome to the comprehensive documentation for Enhanced Mirror-Leech Telegram Bot v3.1.0. This documentation covers all aspects of installation, configuration, deployment, and usage.

---

## 📚 Documentation Structure

### Getting Started
- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions from scratch
- **[Configuration Guide](CONFIGURATION.md)** - All configuration options and settings
- **[Quick Start Guide](../README.md#-quick-start)** - Get up and running in 5 minutes

### Advanced Topics
- **[API Documentation](API.md)** - GraphQL and REST API reference
- **[Health Monitoring](../HEALTH_CHECK_GUIDE.md)** - Health check scripts and monitoring
- **[Test Report](../TEST_REPORT.md)** - Complete test coverage analysis

### Reference
- **[Workspace Reorganization](../WORKSPACE_REORGANIZATION_COMPLETE.md)** - Project structure documentation
- **[License](LICENSE)** - MIT License terms

---

## 🚀 Quick Links

### Essential Pages
| Document | Description | Best For |
|----------|-------------|----------|
| [Installation](INSTALLATION.md) | Step-by-step setup | New users, first-time setup |
| [Configuration](CONFIGURATION.md) | All settings explained | Configuration, customization |
| [API Docs](API.md) | GraphQL & REST API | Developers, integrations |
| [Health Checks](../HEALTH_CHECK_GUIDE.md) | Monitoring & diagnostics | Operations, troubleshooting |

### By Use Case

**🆕 First Time User**
1. Read [Installation Guide](INSTALLATION.md)
2. Follow [Quick Start](../README.md#-quick-start)
3. Check [Health Monitoring](../HEALTH_CHECK_GUIDE.md)

**⚙️ Configuration**
1. Review [Configuration Guide](CONFIGURATION.md)
2. Edit `config/main_config.py`
3. Update `config/.env.production`

**🔌 Integration Development**
1. Read [API Documentation](API.md)
2. Test with GraphQL Playground
3. Implement using REST or GraphQL

**🏥 Operations & Monitoring**
1. Run [Health Check Scripts](../HEALTH_CHECK_GUIDE.md)
2. Monitor [Dashboard](../README.md#-monitoring--metrics)
3. Review [Test Reports](../TEST_REPORT.md)

---

## 📖 Documentation Guide

### Installation Guide
**File:** [INSTALLATION.md](INSTALLATION.md)  
**Length:** ~12KB, ~10 min read  
**Topics:**
- System requirements
- Docker installation
- Repository setup
- Configuration
- Post-installation
- Verification
- Troubleshooting

### Configuration Guide
**File:** [CONFIGURATION.md](CONFIGURATION.md)  
**Length:** ~14KB, ~15 min read  
**Topics:**
- Bot settings
- Download/upload configuration
- Phase 1/2/3 settings
- Service configuration
- Advanced settings
- Environment variables
- Examples

### API Documentation
**File:** [API.md](API.md)  
**Length:** ~14KB, ~15 min read  
**Topics:**
- GraphQL API
- REST endpoints
- WebSocket API
- Authentication
- Rate limiting
- Examples (cURL, Python, JavaScript)

### Health Check Guide
**File:** [../HEALTH_CHECK_GUIDE.md](../HEALTH_CHECK_GUIDE.md)  
**Length:** ~8KB, ~8 min read  
**Topics:**
- Quick health check script
- Comprehensive diagnostics
- Understanding results
- Common issues
- Automated monitoring

### Test Report
**File:** [../TEST_REPORT.md](../TEST_REPORT.md)  
**Length:** ~6KB, ~5 min read  
**Topics:**
- Test results summary
- Phase 1/2/3 verification
- Functional status
- Known issues
- Production readiness

---

## 🎯 Feature Documentation

### Phase 1: Infrastructure
- **Redis Cache:** In-memory caching for performance
- **Prometheus Metrics:** Real-time monitoring data
- **Grafana Dashboards:** Visual analytics and alerts
- **Celery Workers:** Distributed task processing

### Phase 2: Advanced Services
- **Logger Manager:** Centralized logging with rotation
- **Alert Manager:** Smart notification system
- **Backup Manager:** Automated backup & restore
- **Profiler:** Performance profiling tools
- **Recovery Manager:** Automatic failure recovery

### Phase 3: Advanced Features
- **GraphQL API:** Powerful query interface
- **Plugin System:** Dynamic plugin loading
- **Advanced Dashboard:** Real-time web interface
- **Live Metrics:** Real-time statistics

---

## 🔧 Configuration Quick Reference

### Essential Settings

**Bot Token (REQUIRED):**
```bash
BOT_TOKEN=your_bot_token_here
```

**Owner ID (REQUIRED):**
```bash
OWNER_ID=123456789
```

**Phase Activation:**
```python
ENABLE_PHASE_1 = True  # Redis + Prometheus
ENABLE_PHASE_2 = True  # Advanced Services
ENABLE_PHASE_3 = True  # GraphQL + Plugins
```

**Download Limits:**
```python
MAX_CONCURRENT_DOWNLOADS = 5
MAX_CONCURRENT_UPLOADS = 5
MAX_SPLIT_SIZE = 2097152000  # 2GB
```

See [Configuration Guide](CONFIGURATION.md) for complete reference.

---

## 🏥 Health & Monitoring

### Quick Health Check
```bash
./scripts/quick_health_check.sh
```

### Comprehensive Check
```bash
./scripts/health_check_comprehensive.sh
```

### Access Monitoring
- **Dashboard:** http://localhost:8060
- **GraphQL:** http://localhost:8060/graphql
- **Prometheus:** http://localhost:9091
- **Grafana:** http://localhost:3000

---

## 🔌 API Quick Reference

### GraphQL Query Example
```graphql
query {
  status {
    version
    uptime
    activeTasks
  }
}
```

### REST API Example
```bash
curl http://localhost:8060/api/stats
```

### WebSocket Subscription
```javascript
ws://localhost:8060/ws
```

See [API Documentation](API.md) for complete reference.

---

## 🧪 Testing

### Run Tests
```bash
docker exec mltb-app python3 -m pytest tests/ -v
```

### Test Results
- **46/57 tests passed** (81%)
- **0 functional failures**
- **All Phase 1/2/3 verified**

See [Test Report](../TEST_REPORT.md) for details.

---

## 🐛 Troubleshooting

### Common Issues

**Bot not starting:**
```bash
docker-compose logs app
docker-compose restart app
```

**Health check failures:**
```bash
./scripts/health_check_comprehensive.sh
```

**Configuration errors:**
```bash
python3 config/main_config.py
docker-compose config
```

### Getting Help

1. Check [Installation Guide](INSTALLATION.md) troubleshooting section
2. Review [Configuration Guide](CONFIGURATION.md) for settings
3. Run health checks for diagnostics
4. Check Docker logs for errors

---

## 📊 Architecture Overview

```
Enhanced MLTB v3.1.0
├── Phase 1: Infrastructure
│   ├── Redis Cache (port 6379)
│   ├── Prometheus Metrics (port 9091)
│   └── Grafana Dashboard (port 3000)
│
├── Phase 2: Advanced Services
│   ├── Logger Manager
│   ├── Alert Manager
│   ├── Backup Manager
│   ├── Profiler
│   └── Recovery Manager
│
├── Phase 3: Advanced Features
│   ├── GraphQL API (port 8060/graphql)
│   ├── Plugin System
│   └── Advanced Dashboard (port 8060)
│
└── Download Clients
    ├── Aria2 (port 6800)
    ├── qBittorrent (port 8090)
    ├── SABnzbd (port 8080)
    └── JDownloader (MyJD cloud)
```

---

## 📝 Documentation Credits

**Created:** February 6, 2026  
**Version:** 3.1.0  
**Status:** Production Ready

**Documentation Includes:**
- 40+ pages of comprehensive guides
- 100+ configuration options explained
- 50+ API endpoints documented
- 20+ code examples
- Complete test coverage report
- Health monitoring guides

---

## 🆕 Recent Updates

**v3.1.0 (2026-02-06)**
- ✅ Complete workspace reorganization
- ✅ Comprehensive documentation suite
- ✅ Health monitoring scripts
- ✅ Full API documentation
- ✅ Test coverage report
- ✅ Production deployment guides

---

## 🔗 External Resources

### Official Links
- **GitHub Repository:** https://github.com/yourusername/mirror-leech-telegram-bot
- **Issue Tracker:** https://github.com/yourusername/mirror-leech-telegram-bot/issues
- **Discussions:** https://github.com/yourusername/mirror-leech-telegram-bot/discussions

### Related Documentation
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Docker Documentation](https://docs.docker.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [GraphQL Documentation](https://graphql.org/learn/)

---

## 📞 Support

### Documentation Feedback
Found an issue in the documentation? Please:
1. Check if it's already reported in Issues
2. Open a new issue with the "documentation" label
3. Suggest improvements via Pull Request

### Getting Help
- 📖 Read relevant documentation first
- 🔍 Search existing issues
- 💬 Ask in Discussions
- 📧 Email support for critical issues

---

**Documentation maintained by the MLTB Community** 

Last updated: February 6, 2026
