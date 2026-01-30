# Quick Reference Guide

**Modified by: justadi**  
**Version: 3.0.0**  
**Date: January 30, 2026**

---

## 📱 Command Quick Reference

### Most Used Commands

```
/mirror <link>          Mirror to Google Drive
/leech <id>             Leech from Google Drive
/queue                  Show active downloads
/stats                  System information
/help                   Show all commands
/settings               User preferences
/cancel <gid>           Cancel download
/search <query>         Search downloads
/history                Download history
```

---

## 📥 Download (Top 3)

| Command | Purpose | Example |
|---------|---------|---------|
| `/mirror` | Any source → Drive | `/mirror https://example.com/file.zip` |
| `/leech` | Drive → Telegram | `/leech file_id` |
| `/qmirror` | Torrent → Drive | `/qmirror magnet:...` |

---

## 🔄 Queue (Most Used)

| Command | Purpose | Example |
|---------|---------|---------|
| `/queue` | View all downloads | `/queue` |
| `/pqueue` | Pause download | `/pqueue gid123` |
| `/rqueue` | Resume download | `/rqueue gid123` |
| `/prqueue` | Set priority | `/prqueue gid123 2` |
| `/cancel` | Cancel download | `/cancel gid123` |

---

## 📊 Information

| Command | Purpose |
|---------|---------|
| `/stats` | Full system info |
| `/ping` | Bot latency |
| `/speed` | Internet speed test |
| `/dashboard` | Web interface |
| `/help` | Command list |

---

## 🎯 Priority Levels

```
1 = Very High (starts immediately)
2 = High
3 = Normal (default)
4 = Low
5 = Very Low (starts last)
```

**Example:**
```
/prqueue abc123 1    ← High priority
/prqueue xyz789 5    ← Low priority
```

---

## 🏷️ File Operations

```
/zip /path            Create ZIP archive
/unzip /path          Extract archive
/zipinfo /path        Archive info
/mediainfo /path      Media details
/thumbnail /path      Extract thumbnail
```

---

## 👤 Admin Commands (Owner)

```
/authorize <id>       Add user
/unauthorize <id>     Remove user
/bsetting             Bot settings
/restart              Restart bot
/log                  View logs
/shell <cmd>          Run command
```

---

## ⚙️ Configuration Quick Setup

**Minimum required in config.py:**

```python
BOT_TOKEN = "123456:ABC..."
OWNER_ID = 987654321
AUTHORIZED_CHATS = "987654321"
DOWNLOAD_DIR = "/downloads"
```

---

## 🔗 Links & Resources

| Resource | Link |
|----------|------|
| Get Bot Token | [@BotFather](https://t.me/botfather) |
| Get User ID | [@userinfobot](https://t.me/userinfobot) |
| GitHub | [mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot) |
| Documentation | [README_COMPLETE.md](README_COMPLETE.md) |
| Setup Guide | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| Usage Guide | [USAGE_GUIDE.md](USAGE_GUIDE.md) |

---

## 📲 Common Workflows

### Download File to Google Drive
```
1. /mirror https://example.com/file.zip
2. Wait for completion
3. Get Drive link in response
```

### Download from Drive to Telegram
```
1. /leech <file_id>
2. Wait for upload
3. Receive file in chat
```

### Create Backup Archive
```
1. /zip /path/to/folder 7z 9
2. /mirror /path.7z
3. Get backup link
```

### Manage Downloads
```
1. /queue (view all)
2. /prqueue gid 1 (set priority)
3. /pqueue gid (pause if needed)
```

### Monitor System
```
1. /stats (full info)
2. /dashboard (web interface)
3. /speed (test speed)
```

---

## 🚨 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Bot not responding | `/ping` or restart via `/restart` |
| Download stuck | `/pqueue gid` then `/rqueue gid` |
| Slow speed | `/limit 0` (remove limit) or add more bandwidth |
| High CPU | `/pauseall` and `TASK_LIMIT = 1` in config |
| Drive quota full | Check `/stats` and clear old files |

---

## 📊 Default Settings

```python
TASK_LIMIT = 2              (Max 2 parallel downloads)
BANDWIDTH_LIMIT = 0         (Unlimited)
AUTO_PAUSE_CPU = 80         (Pause at 80% CPU)
AUTO_PAUSE_MEMORY = 85      (Pause at 85% RAM)
INCOMPLETE_TASK_NOTIFIER = True
```

---

## 🆘 Emergency Commands

```
/restart                Restart bot (owner)
/log                    View error logs (owner)
/cancelall              Cancel all downloads (owner)
/pauseall               Pause everything (owner)
/shell systemctl status Check service status (owner)
```

---

## 💾 Storage Information

**Check storage:**
```
/stats

Look for:
💾 Storage section
📊 Shows: Total / Used / Free
```

**Free up space:**
```
1. /history
2. Look for old completed downloads
3. Use /shell to delete if needed
```

---

## 🔐 Security Tips

1. **Never share BOT_TOKEN**
2. **Keep config.py private**
3. **Use AUTHORIZED_CHATS carefully**
4. **Change default passwords** (qBittorrent, etc.)
5. **Use strong database passwords**
6. **Enable database authentication** if exposed

---

## 📈 Performance Tips

### For Better Speed
```
/limit 0                (Remove bandwidth limit)
/prqueue gid 1          (Prioritize important tasks)
TASK_LIMIT = 5          (Increase parallel downloads)
```

### For Better Stability
```
/limit 20M              (Set safe bandwidth limit)
TASK_LIMIT = 1          (One download at a time)
AUTO_PAUSE_CPU = 70     (Pause earlier to prevent hang)
```

### For Better Resources
```
BANDWIDTH_LIMIT = 50M   (Limit speed)
TASK_LIMIT = 2          (2 parallel max)
AUTO_PAUSE = True       (Auto pause on high load)
```

---

## 🎓 Learning Path

**Beginner:**
1. Read: SETUP_GUIDE.md
2. Try: `/mirror <simple_link>`
3. Check: `/queue` and `/stats`

**Intermediate:**
4. Try: `/zip`, `/unzip`
5. Learn: Priority management
6. Test: `/dashboard`

**Advanced:**
7. Schedule: `/schedule`
8. Automate: RSS feeds
9. Admin: Bot settings

---

## 📞 Where to Get Help

1. **Documentation** - Read markdown files
2. **Logs** - Use `/log` command
3. **GitHub** - Check issues/discussions
4. **Examples** - See USAGE_GUIDE.md

---

## ✅ First Time Setup Checklist

- [ ] Docker installed (if using Docker)
- [ ] Bot token from @BotFather
- [ ] User ID from @userinfobot
- [ ] config.py created and configured
- [ ] Bot started successfully
- [ ] Test with `/start` command
- [ ] Try `/mirror` with test file
- [ ] Check queue with `/queue`
- [ ] View stats with `/stats`
- [ ] Test `/settings` for customization

---

## 🎯 Next Steps

1. **Setup:** Follow SETUP_GUIDE.md
2. **Learn:** Read USAGE_GUIDE.md
3. **Explore:** Try all commands
4. **Customize:** Adjust config.py
5. **Automate:** Use scheduling
6. **Share:** Invite other users
7. **Monitor:** Use dashboard regularly

---

## 📋 Command Categories

**Files:** `/zip`, `/unzip`, `/zipinfo`, `/mediainfo`, `/thumbnail`  
**Download:** `/mirror`, `/leech`, `/qmirror`, `/jdmirror`, `/nzbmirror`, `/ytdl`  
**Queue:** `/queue`, `/pqueue`, `/rqueue`, `/prqueue`, `/pauseall`, `/resumeall`  
**Management:** `/history`, `/search`, `/filter`, `/taskdetails`, `/cancel`  
**System:** `/stats`, `/ping`, `/speed`, `/dashboard`, `/help`, `/settings`  
**Admin:** `/authorize`, `/unauthorize`, `/bsetting`, `/restart`, `/log`, `/shell`  

---

## 🚀 Pro Tips

**Tip 1:** Use `/prqueue` to prioritize important files
**Tip 2:** Monitor `/dashboard` for real-time updates
**Tip 3:** Set `/limit` to prevent network congestion
**Tip 4:** Use `/search` to find old downloads
**Tip 5:** Enable `/schedule` for automated backups
**Tip 6:** Check `/stats` regularly for health
**Tip 7:** Archive files with `/zip` before uploading
**Tip 8:** Use `/speed` to verify connectivity

---

## 📞 Support

- **Documentation:** See markdown files
- **Issues:** GitHub issues page
- **Discussions:** GitHub discussions
- **Logs:** Use `/log` command (owner)

---

**Modified by:** justadi  
**Version:** 3.0.0  
**Last Updated:** January 30, 2026  
**Status:** ✅ Complete

Remember: Read the full docs for detailed information!
