# Fix: HTTP 403 Forbidden Error in /qm Command

**Error**: `/qm` command returns `HTTP 403 Forbidden`

---

## ❌ What This Error Means

The torrent source (tracker, website, or DHT network) rejected your download request. The server is actively blocking access.

---

## 🔍 Common Causes

### 1. **Geo-Blocking** (Most Common)
- Torrent source is restricted by region (geo-blocked)
- Your country/IP is blacklisted
- The tracker blocks certain regions

### 2. **Rate Limiting**
- Your IP made too many requests, now blocked
- ISP detected torrent traffic
- Source throttling your connection

### 3. **Authentication Required**
- Source requires login, API key, or cookies
- qBittorrent cannot provide credentials
- Private tracker needs account

### 4. **Link No Longer Valid**
- Torrent file/magnet expired
- Tracker removed the content
- Magnet link timed out

### 5. **qBittorrent Configuration Issue**
- Missing User-Agent header
- Proxy not configured
- Old qBittorrent version

---

## ✅ Solutions (Try in Order)

### **Solution 1: Wait & Retry** ⏱️
If it's temporary blocking:
```bash
# Wait 5-10 minutes, then retry
/qm <magnet-link-or-url>
```

---

### **Solution 2: Use Different Torrent Source** 🔗
Try a different tracker or torrent file:
```bash
# If using HTTP tracker, try magnet link
/qm magnet:?xt=urn:btih:HASH_HERE

# If magnet failed, try .torrent file
# Download the .torrent file and reply with it
```

---

### **Solution 3: Use /mirror Command Instead** 🚀
```bash
# Instead of /qm, try /mirror for direct downloads
/mirror <torrent-url-or-magnet>

# /mirror uses Aria2 which may bypass some blocks
```

---

### **Solution 4: Direct Torrent File Upload** 📁
Instead of providing a link:
1. Download the `.torrent` file to your device
2. Reply to bot with: `/qm` and attach the .torrent file
3. Bot will upload and add directly

```
This bypasses the URL completely and avoids 403 errors.
```

---

### **Solution 5: Check qBittorrent Configuration** ⚙️

If the issue persists for ALL torrents:

**Check User-Agent Header**:
```bash
# SSH into server, check qBittorrent config
cat /path/to/qBittorrent/config/qBittorrent.ini | grep -i "user.agent"

# If missing, qBittorrent may appear as bot to source
# Sources block requests without proper User-Agent
```

**Restart qBittorrent**:
```bash
# Restart the service
docker compose -f deployment/compose/docker-compose.yml restart qbittorrent

# Wait 10 seconds
sleep 10

# Try /qm again
```

---

### **Solution 6: Check Bot Debug Logs** 📊

```bash
# View bot logs for detailed error
docker compose -f deployment/compose/docker-compose.yml logs bot | tail -50 | grep -i "403\|forbidden\|qbittorrent"

# Look for the exact error message
```

---

## 🔧 Advanced Troubleshooting

### **Is qBittorrent Connected?**
```bash
# Check bot status
/stats

# If qBittorrent shows offline, it's not running
```

### **Is the Link Valid?**
```bash
# Test the torrent link directly (careful!)
# Try in browser: Copy the magnet link or .torrent URL

# If browser also blocks it, the link itself is blocked
```

### **Is Your IP Blocked?**
```bash
# Check your public IP
curl https://api.ipify.org

# If source has IP-based blocking, VPN might help
# (Only if bot admin allows VPN)
```

---

## 📋 When to Use Each Command

| Scenario | Use This | Why |
|----------|----------|-----|
| **Magnet link, can't download** | `/mirror` instead of `/qm` | Aria2 may bypass blocks |
| **Torrent file available** | Reply with `.torrent` + `/qm` | Bypasses URL blocking |
| **Source geo-blocked** | `/mirror` or wait | Try different source |
| **Rate limited (too many requests)** | Wait 10+ mins, then retry | Server need time to reset |
| **Private tracker/authentication needed** | `/mirror` (won't work either) | Need account credentials |

---

## 🚫 What WON'T Fix It

❌ **Using VPN** - Bot must be configured to support it  
❌ **Adding headers manually** - Not possible in Telegram  
❌ **Downloading in browser first** - Then uploading will still get 403 if source blocks it  
❌ **Using /leech instead of /qm** - Same backend, same error  

---

## 📞 Still Not Working?

### **For Admin**:
1. Check Docker logs: `docker logs <container-id> | grep 403`
2. Verify qBittorrent service: `docker ps | grep qbittorrent`
3. Check network: `curl https://ipv4.icanhazip.com`

### **For Users**:
1. Confirm error message: Screenshot and share with admin
2. Try alternative source
3. Use `/mirror` command instead
4. Wait 15+ minutes and retry

---

## 💡 Prevention Tips

1. **Use reputable torrent sources** - Big trackers rarely block
2. **Don't spam downloads** - Space requests 5+ seconds apart
3. **Use magnet links** - More resilient than HTTP links
4. **Keep .torrent files** - Upload files directly to avoid URL issues
5. **Monitor /stats** - Check if qBittorrent is running

---

## 🔗 Related Commands

```bash
/mirror      # Use this for blocked /qm links
/stats       # Check qBittorrent status
/leech       # Download & upload (also uses qBittorrent)
/help        # See all commands
```

---

**Error Fixed By**: Improved error handling in v3.2.1+  
**Date**: 2026-02-23  
**Status**: Enhanced user messaging for 403 errors
