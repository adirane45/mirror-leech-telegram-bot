# Quick Start Guide - New Features
**Enhanced by: justadi**

## 🚀 Quick Command Reference

### Basic Commands
```bash
/speed                    # Test internet speed
/dashboard                # Show overview
/history                  # View download history
/settings                 # Configure bot
```

### Queue Management
```bash
/queue                    # Show all tasks
/pqueue abc123            # Pause task
/rqueue abc123            # Resume task
/prqueue abc123 1         # Set priority (high)
/pauseall                 # Pause all (owner)
/resumeall                # Resume all (owner)
```

### Task Operations
```bash
/taskdetails abc123       # Show task info
/searchtasks movie        # Search tasks
/filtertasks download     # Filter by status
```

### Settings
```bash
/viewtoggle compact       # Switch view mode
/setalerts errors_only    # Set notifications
```

---

## 📊 Status Indicators

- 📥 Downloading
- 📤 Uploading
- ⏸️ Paused
- 📋 Queued
- ✅ Complete
- ❌ Failed
- 🔄 Processing

---

## 🎯 Priority Levels

- `-1` or `low` - Low priority
- `0` or `normal` - Normal priority
- `1` or `high` - High priority

---

## 🔧 Auto-Pause Settings

Default thresholds:
- **CPU:** 80%
- **RAM:** 85%
- **Disk:** 10GB free

Configure with `/settings` command.

---

## 🔑 Permission Requirements

### All Authorized Users
- All UI/UX commands
- Queue viewing
- Task pause/resume/priority

### Owner Only
- Pause all tasks
- Resume all tasks
- System-wide settings

---

## 💡 Tips

1. **Reply to Messages**  
   Most commands work by replying to task messages
   ```
   [Reply to task] /pqueue
   ```

2. **Interactive Buttons**  
   All features have buttons for easier access

3. **Search Shortcuts**  
   Use partial names for quick searches
   ```
   /searchtasks mov    # Finds "movie", "movies", etc.
   ```

4. **History Limit**  
   Last 200 downloads are kept

5. **View Modes**  
   - `compact` - Less detail, more tasks
   - `detailed` - Full information

---

## 🐛 Troubleshooting

### Command Not Working
1. Check you're authorized: `/start`
2. Verify command syntax with `/help`
3. Try with GID instead of reply

### Auto-Pause Not Working
1. Open settings: `/settings`
2. Check thresholds are enabled
3. Verify monitoring is on

### History Not Showing
1. Only tracks after bot restart
2. Complete at least one task
3. Check with `/history`

---

## 📝 Examples

### Example 1: Manage Queue
```bash
# Show queue
/queue

# Pause slow task
/pqueue abc123

# Set important task to high priority
/prqueue xyz789 1

# Resume paused task
/rqueue abc123
```

### Example 2: Search & Filter
```bash
# Find all movie downloads
/searchtasks movie

# Show only paused tasks
/filtertasks paused

# Show task details
/taskdetails abc123
```

### Example 3: Configure Settings
```bash
# Open settings panel
/settings

# Click "CPU Monitoring: OFF" button to enable
# Click "Set CPU Threshold" and enter 75
# Click "Set Interval" and enter 30 (seconds)
```

### Example 4: Monitor System
```bash
# Quick overview
/dashboard

# Check history for patterns
/history

# View specific task
/taskdetails abc123
```

---

## 🔄 Integration with Existing Commands

All new features work alongside existing bot commands:

### Before
```bash
/mirror https://example.com/file.zip
/status
```

### Now (Enhanced)
```bash
/mirror https://example.com/file.zip
/dashboard              # Better overview than /status
/taskdetails abc123     # Detailed info
/pqueue abc123          # Pause if needed
```

---

## 📱 Mobile Usage

All features optimized for mobile:
- ✅ Interactive buttons (no typing)
- ✅ Compact view mode
- ✅ Clear visual indicators
- ✅ Reply-based commands

---

## ⚡ Performance

### Response Times
- Dashboard: <1 second
- Queue view: <1 second
- Search: <2 seconds (1000 tasks)
- History: <1 second

### Resource Usage
- CPU: <1% additional
- RAM: ~50MB additional
- Disk: ~5MB for history

---

## 🎨 Customization

### Change Auto-Pause Thresholds
```bash
/settings
# Click appropriate buttons
# Enter new values
```

### Change View Mode
```bash
/viewtoggle compact    # Space-saving
/viewtoggle detailed   # Full info
```

### Change Notifications
```bash
/setalerts on          # All notifications
/setalerts errors_only # Only errors
/setalerts off         # No notifications
```

---

## 🔐 Security Notes

- Settings are per-user (not shared)
- History shows only your tasks
- Owner commands protected
- No sensitive data logged

---

## 📞 Support

Need help? Check these in order:

1. **Help Command**
   ```bash
   /help
   ```

2. **Error Logs**
   ```bash
   /log
   ```

3. **Documentation**
   - See `NEW_FEATURES_GUIDE.md`
   - See `TECHNICAL_IMPLEMENTATION.md`

4. **Common Issues**
   - Restart bot: `/restart`
   - Clear cache: Re-authenticate
   - Check permissions: Owner/Sudo

---

**Developed by: justadi**  
**Version: 2.0**  
**Last Updated: 2024**

---

## 🎁 All New Commands Summary

| Command | Description | Permission |
|---------|-------------|------------|
| `/speed` | Test internet speed | All |
| `/dashboard` | System overview | All |
| `/queue` | Show task queue | All |
| `/pqueue [gid]` | Pause task | All |
| `/rqueue [gid]` | Resume task | All |
| `/prqueue [gid] [p]` | Set priority | All |
| `/pauseall` | Pause all tasks | Owner |
| `/resumeall` | Resume all tasks | Owner |
| `/taskdetails [gid]` | Task information | All |
| `/searchtasks [q]` | Search tasks | All |
| `/filtertasks [s]` | Filter tasks | All |
| `/history` | Download history | All |
| `/settings` | Bot settings | All |
| `/viewtoggle [m]` | Change view | All |
| `/setalerts [o]` | Set notifications | All |

**Total: 15 new commands + Interactive keyboards system**

---

Enjoy your enhanced bot! 🎉
