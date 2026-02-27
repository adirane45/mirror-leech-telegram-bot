# God Root WebUI - Quick Reference

## 🌐 Access URLs
```
Main Dashboard:  http://justadi.qzz.io:8060/
Admin Login:     http://justadi.qzz.io:8060/admin/login
Admin Dashboard: http://justadi.qzz.io:8060/admin/dashboard
```

## 🔐 Credentials
```
Username: admin
Password: admin123
```

## ✅ Status: All Operational

### Main Dashboard
- ✅ Real-time system stats (CPU, memory, uptime)
- ✅ Active downloads monitoring
- ✅ Download speed tracking

### Admin Panel
- ✅ JWT authentication (24h tokens)
- ✅ Download queue management
- ✅ Mirror/Leech operations
- ✅ qBittorrent/Aria2/JDownloader support

### Background Services
- ✅ Admin download processor (polls every 5s)
- ✅ Aria2 (port 6800)
- ✅ qBittorrent (port 8090)
- ✅ JDownloader (MyJD)
- ✅ Redis (port 6379)

## 📋 Quick Commands

### Start Download via cURL
```bash
# Get token
TOKEN=$(curl -s -X POST "http://justadi.qzz.io:8060/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# Queue download
curl -X POST "http://justadi.qzz.io:8060/admin/api/download/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/file.zip",
    "operation": "mirror"
  }'

# Check status
curl -s "http://justadi.qzz.io:8060/admin/api/downloads" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Operations Available
- `mirror` - Download + upload to cloud
- `leech` - Download + send to Telegram
- `qm` - qBittorrent mirror
- `jm` - JDownloader mirror
- `qb_mirror` - qBittorrent direct

### Troubleshooting
```bash
# Check container
docker ps | grep mltb-app
docker logs --tail 50 mltb-app

# Check processor
docker logs mltb-app 2>&1 | grep "Admin download processor"

# Restart
docker restart mltb-app

# Test endpoints
bash /tmp/test_admin_panel.sh
```

## 📚 Full Documentation
See [GOD_ROOT_WEBUI_GUIDE.md](./GOD_ROOT_WEBUI_GUIDE.md) for complete API reference and usage examples.

## ⚠️ Known Issues
**Aria2 RPC Authentication Warnings:** Expected and non-critical. Doesn't affect functionality.

## 🚀 Next Phase
Phase 3 features available on request:
- WebSocket real-time updates
- File browser interface
- Download history
- Multi-user support
- Enhanced security
