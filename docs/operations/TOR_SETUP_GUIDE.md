# Tor Setup Guide - Fix HTTP 403 Forbidden Errors

**Problem**: `/qm` command returns HTTP 403 Forbidden
**Solution**: Use Tor to rotate IP addresses and bypass IP-based blocking
**Status**: ✅ Implemented & Ready to Use

---

## 🎯 Quick Start (3 Steps)

### Step 1: Enable Tor in .env

Edit `config/.env.production`:
```bash
# Enable Tor for rotating IP (fixes 403 errors)
ENABLE_TOR=true
TOR_PROXY_URL=socks5://tor:9050
```

### Step 2: Start Tor Service

```bash
# Start with Tor profile enabled
docker compose --profile tor -f deployment/compose/docker-compose.yml up -d

# Or if already running, just add Tor
docker compose --profile tor -f deployment/compose/docker-compose.yml up tor -d
```

### Step 3: Restart Bot

```bash
# Restart bot to connect through Tor
docker compose -f deployment/compose/docker-compose.yml restart mirror-bot

# Verify in logs
docker logs mltb | tail -20 | grep -i "tor\|proxy"
```

**Done!** Now `/qm` will use rotating Tor IPs.

---

## 📊 How It Works

```
User /qm Command
        ↓
qBittorrent-bot
        ↓
Tor SOCKS5 Proxy (rotates IP every ~10 minutes)
        ↓
Torrent Source (sees different IP)
        ↓
✅ Returns 200 OK / ❌ Returns new 403 after rotation
```

---

## 🔧 Configuration Options

### Option 1: Use Built-in Tor Service (Recommended)

**In `config/.env.production`**:
```bash
ENABLE_TOR=true
TOR_PROXY_URL=socks5://tor:9050
```

**Start with Tor**:
```bash
docker compose --profile tor -f deployment/compose/docker-compose.yml up -d
```

### Option 2: Use External SOCKS5 Proxy

**In `config/.env.production`**:
```bash
USE_PROXY=true
PROXY_URL=socks5://your-proxy-host:port
```

**Example with external Tor service**:
```bash
USE_PROXY=true
PROXY_URL=socks5://192.168.1.100:9050  # External Tor
```

### Option 3: Use HTTP Proxy (Cloudflare, etc.)

**In `config/.env.production`**:
```bash
USE_PROXY=true
PROXY_URL=http://proxy.host:port
# Can use Basic auth: http://user:pass@proxy:port
```

### Option 4: Disable Proxy (Default)

```bash
ENABLE_TOR=false
USE_PROXY=false
```

---

## 🐳 Docker Commands

### Start Everything with Tor

```bash
docker compose --profile tor -f deployment/compose/docker-compose.yml up -d
```

### Start Services Without Tor

```bash
docker compose -f deployment/compose/docker-compose.yml up -d

# Tor NOT started (ENABLE_TOR ignored if Tor container not running)
```

### Check Tor Status

```bash
# Verify Tor is running
docker ps | grep tor

# Check Tor logs
docker logs mltb-tor | tail -20

# Test SOCKS5 connection
docker exec mltb-tor curl -x socks5://localhost:9050 https://check.torproject.org | grep -i "Congratulations"
```

### Rotate Tor IP Manually

```bash
# New circuit (new IP)
docker exec mltb-tor bash -c 'echo "signal NEWNYM" | nc localhost 9051' && sleep 3

# Verify IP changed
docker exec mltb-tor curl -x socks5://localhost:9050 https://api.ipify.org
```

---

## 📋 Troubleshooting

### Bot Still Shows 403 Error

**Check 1: Verify Tor is running**
```bash
docker ps | grep tor
# Should see: mltb-tor ... Up

# If not running, start it
docker compose --profile tor -f deployment/compose/docker-compose.yml up tor -d
```

**Check 2: Verify logs show Tor is enabled**
```bash
docker logs mltb | grep -i "tor\|proxy"
# Should show: "Tor proxy enabled" or "Proxy enabled"
```

**Check 3: Check bot can reach Tor**
```bash
docker exec mltb curl -x socks5://tor:9050 https://check.torproject.org
# Should return Tor congratulations page
```

**Check 4: Restart qBittorrent**
```bash
docker compose -f deployment/compose/docker-compose.yml restart qbittorrent
sleep 5
# Try /qm again
```

### Tor Connection Timeout

**Solution**: Increase wait time for Tor to start
```bash
# Restart Tor with longer startup
docker compose --profile tor -f deployment/compose/docker-compose.yml down tor
sleep 3
docker compose --profile tor -f deployment/compose/docker-compose.yml up tor -d
sleep 10  # Wait 10 seconds for Tor to initialize
docker compose -f deployment/compose/docker-compose.yml restart mirror-bot
```

### Performance Issues

Tor is slower than direct connection (adds ~1-2 second latency)

**Solution**: Try alternative proxy if available
```bash
# Use faster external proxy
USE_PROXY=true
PROXY_URL=socks5://fast-proxy:1080

# Restart
docker restart mltb
```

### Port 9050 Already in Use

```bash
# Find what's using port 9050
lsof -i :9050

# Use different port if needed (also change in .env)
# Create custom docker-compose override:
```

Create `docker-compose.override.yml`:
```yaml
services:
  tor:
    ports:
      - "9055:9050"  # Map to 9055 instead

  mirror-bot:
    environment:
      - TOR_PROXY_URL=socks5://tor:9055  # Update reference
```

---

## 🔍 Monitoring & Stats

### Check Current IP Through Tor

```bash
# Local IP (direct)
curl https://api.ipify.org

# Tor IP (rotated)
curl -x socks5://localhost:9050 https://api.ipify.org

# They should be different!
```

### Monitor IP Changes

```bash
# Every 30 seconds, show current Tor IP
watch -n 30 "curl -s -x socks5://localhost:9050 https://api.ipify.org && echo ''"
```

### Check Tor Circuit Info

```bash
# Get exit node info
curl -x socks5://localhost:9050 https://api.ipify.org/json?format=json

# Should show different IP and country on each call
```

---

## 🚀 Advanced Configuration

### Custom Tor Settings

If you need to configure Tor beyond defaults, create `tor-config` volume and add `torrc`:

1. Create file: `integrations/tor/torrc`
```
# Custom Tor configuration
Log notice file /var/log/tor/notices.log
SocksPort 0.0.0.0:9050
ControlPort 0.0.0.0:9051
CookieAuthentication 1

# Rotate circuit every 10 minutes
MaxCircuitDirtiness 600000

# Change exit node country (optional)
# ExitNodes {us},{gb},{de}
# EntryNodes {us},{gb},{de}
```

2. Update `docker-compose.yml` Tor service:
```yaml
tor:
  volumes:
    - ./integrations/tor/torrc:/etc/tor/torrc:ro
```

3. Restart:
```bash
docker compose --profile tor up tor -d
```

### Connection Pool Settings

For heavy loads, increase qBittorrent connection pool:

In `config/.env.production`:
```bash
# Add these for better Tor performance
QB_CONNECTION_LIMIT=500
QB_PEER_CONNECTION_LIMIT=1000
```

---

## 🎭 When to Use Tor vs Regular Connection

| Situation | Use Tor | Notes |
|-----------|---------|-------|
| **Getting 403 errors** | ✅ Yes | Rotates IP every 10 min |
| **Geo-blocked content** | ✅ Yes | Exit node varies by country |
| **Rate limited** | ✅ Yes | New IP = reset rate limit |
| **Normal downloads** | ❌ No | Slower, unnecessary |
| **Testing** | ❌ No | Use direct for speed |
| **Region-specific sources** | ✅ Maybe | Select exit node country |

---

## 📞 FAQ

### Q: Is Tor slower?
**A**: Yes, ~500ms-2s added latency. Worth it if it fixes blocking.

### Q: Does Tor hide my identity?
**A**: Tor rotates your IP. Torrent sources see different IP. Your ISP can still see you're using Tor (but not what torrents).

### Q: Can I use residential proxy instead?
**A**: Yes! Set `USE_PROXY=true` and `PROXY_URL=socks5://residential-proxy:port`

### Q: How often does Tor rotate IP?
**A**: By default every ~10 minutes. Can customize in torrc.

### Q: Will this work with all torrent sources?
**A**: Most, but some block Tor exit nodes. Try different solutions if still blocked.

### Q: Can I run Tor on a different machine?
**A**: Yes, specify external Tor IP in `TOR_PROXY_URL` or `PROXY_URL`

### Q: Is Tor legal?
**A**: Yes, Tor itself is legal in most countries. Using it for torrents depends on content.

---

## 🔗 Related Documentation

- [Fix 403 Error Guide](FIX_QM_403_ERROR.md)
- [qBittorrent Configuration](CONFIGURATION.md)
- [Commands Reference](COMMANDS.md)
- [Troubleshooting](../docs/TESTING_GUIDE.md)

---

## 📚 External Resources

- **Tor Project**: https://www.torproject.org/
- **SOCKS5 Protocol**: https://tools.ietf.org/html/rfc1928
- **aiohttp-socks**: https://github.com/romis2k/aiohttp-socks

---

**Status**: ✅ Tor support fully implemented
**Version**: v3.2.1+
**Date**: 2026-02-23
**Tested**: Docker Compose with tor-simple image
