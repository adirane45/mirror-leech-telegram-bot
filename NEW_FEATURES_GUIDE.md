# New Features Guide - Mirror Leech Telegram Bot
**Enhanced by: justadi**

## Overview
This bot has been enhanced with comprehensive UI/UX features, interactive keyboards, advanced task management capabilities, task scheduling, bandwidth limiting, and categorization - all while preserving existing functionality.

---

## 🆕 Advanced Features (2026 Update)

### Task Scheduling
Schedule downloads to start at specific times, perfect for taking advantage of off-peak bandwidth hours.

**Commands:**
- `/schedule HH:MM mirror <link> [options]` - Schedule for specific time today/tomorrow
- `/schedule YYYY-MM-DD HH:MM leech <link>` - Schedule for specific date and time
- `/schedules` - List all your scheduled tasks
- `/unschedule <task_id>` - Cancel a scheduled task

**Examples:**
```bash
# Schedule at 2:30 AM tonight
/schedule 02:30 mirror https://example.com/file.zip

# Schedule with date
/schedule 2026-02-01 18:00 leech magnet:?xt=urn:btih:...

# List your schedules
/schedules

# Cancel a schedule
/unschedule abc123def456
```

**Modified by: justadi**

---

### Bandwidth Limiting
Control download and upload speeds globally or per-task to prevent network saturation.

**Commands:**
- `/limit dl <mbps>` - Set global download limit (sudo only)
- `/limit ul <mbps>` - Set global upload limit (sudo only)
- `/limit dl off` - Remove download limit
- `/limit_task <gid> dl <mbps>` - Set task-specific download limit
- `/limit_task <gid> ul <mbps>` - Set task-specific upload limit

**Examples:**
```bash
# Set global 50 Mbps download limit
/limit dl 50

# Set global 10 Mbps upload limit
/limit ul 10

# Remove limits
/limit dl off

# Limit specific task to 20 Mbps
/limit_task abc123 dl 20
```

**Modified by: justadi**

---

### Task Categorization
Organize your tasks into categories like "Movies", "Software", "Backups" for better management.

**Commands:**
- `/category list` - Show all categories
- `/category add <name>` - Create new category
- `/category del <name>` - Delete category
- `/category stats` - Show category statistics
- `/categorize <gid> <category>` - Assign task to category

**Examples:**
```bash
# Create categories
/category add movies
/category add software

# List categories
/category list

# Assign task to category
/categorize abc123 movies

# View stats
/category stats
```

**Modified by: justadi**

---

## 📊 Original Features

---

## 1. Speedtest Command
**Command:** `/speed`  
**Purpose:** Test server's internet speed  
**Features:**
- Download/Upload speed measurement
- Ping latency
- Interactive keyboard buttons for quick access

**Usage:**
```
/speed
```

---

## 2. Task Queue Manager
**Commands:**
- `/queue` - Show all active tasks with management options
- `/pqueue [gid]` - Pause a specific task
- `/rqueue [gid]` - Resume a paused task
- `/prqueue [gid] [priority]` - Set task priority (-1=low, 0=normal, 1=high)
- `/pauseall` - Pause all tasks (Owner only)
- `/resumeall` - Resume all paused tasks (Owner only)

**Features:**
- Visual queue display with status indicators
- Interactive buttons for pause/resume/priority
- Comprehensive task information (name, size, speed, progress)
- Queue position management
- Bulk operations for all tasks

**Usage:**
```bash
# Show queue
/queue

# Pause a specific task (by GID or reply to task message)
/pqueue abc123

# Set task priority
/prqueue abc123 1
```

---

## 3. Dashboard
**Command:** `/dashboard`  
**Purpose:** Comprehensive overview of bot status and system resources

**Displays:**
- Active tasks count by status (downloading, uploading, paused, queued)
- System resources (CPU, RAM, Disk usage)
- Recent activity from download history
- Quick action buttons

**Usage:**
```
/dashboard
```

---

## 4. Task Details
**Command:** `/taskdetails [gid]`  
**Purpose:** Show detailed information about a specific task

**Displays:**
- Task name and GID
- Current status
- Size and progress
- Speed and ETA
- User who initiated
- Source link
- Task age
- Interactive action buttons

**Usage:**
```bash
# Show details for specific task
/taskdetails abc123

# Or reply to a task message
/taskdetails
```

---

## 5. Search & Filter Tasks
**Commands:**
- `/searchtasks [query]` - Search tasks by name or GID
- `/filtertasks [status]` - Filter tasks by status

**Status Options:**
- `download` - Show only downloading tasks
- `upload` - Show only uploading tasks
- `paused` - Show only paused tasks
- `queued` - Show only queued tasks
- `all` - Show all tasks

**Features:**
- Regex-based search
- Case-insensitive matching
- Shows top 10 results with pagination hints
- Interactive filter buttons

**Usage:**
```bash
# Search for tasks
/searchtasks movie

# Filter by status
/filtertasks download
```

---

## 6. Download History
**Command:** `/history`  
**Purpose:** View download history with success/failure tracking

**Features:**
- Last 200 downloads tracked
- Success/failure statistics
- Timestamps for each entry
- File sizes
- Visual indicators (✅/❌)

**Usage:**
```
/history
```

---

## 7. Settings Panel
**Command:** `/settings`  
**Purpose:** Configure bot behavior and auto-pause features

**Features:**
- **Auto-Pause on High CPU** - Automatically pause tasks when CPU usage exceeds threshold
- **Auto-Pause on High RAM** - Automatically pause tasks when RAM usage exceeds threshold
- **Auto-Pause on Low Disk** - Automatically pause tasks when disk space is low
- **Monitoring Interval** - Set how often system resources are checked (default: 60 seconds)
- Interactive toggle buttons for each setting
- Real-time monitoring in background

**Settings Storage:**
- Per-user preferences
- Persistent across bot restarts
- Default thresholds: CPU=80%, RAM=85%, Disk=10GB free

**Usage:**
```
/settings
```

---

## 8. View Toggle
**Command:** `/viewtoggle [mode]`  
**Purpose:** Switch between compact and detailed status views

**Modes:**
- `compact` - Minimal information, space-saving
- `detailed` - Full information with all details

**Usage:**
```bash
/viewtoggle compact
/viewtoggle detailed
```

---

## 9. Alert Configuration
**Command:** `/setalerts [option]`  
**Purpose:** Configure notification preferences

**Options:**
- `on` - Enable all notifications
- `off` - Disable notifications
- `errors_only` - Only notify on errors
- `completion` - Only notify on task completion

**Usage:**
```bash
/setalerts errors_only
```

---

## 10. Interactive Keyboards
All features now support interactive button-based controls for easier navigation and management.

**Available Keyboard Collections:**
- **Task Actions** - Pause, Resume, Cancel, Priority
- **Queue Management** - Show Queue, Pause All, Resume All
- **Priority Selector** - High, Normal, Low priority buttons
- **Task Confirmation** - Yes/No confirmation dialogs
- **Status Filters** - Download, Upload, Paused, Queued, All
- **Search Filters** - By Name, By GID, By Status
- **Pagination** - Previous, Next, Page number
- **Task Menu** - Details, Actions, History
- **Quick Actions** - Dashboard, Queue, Settings, History
- **Toggle Buttons** - On/Off, Enable/Disable

---

## System Requirements

### Python Packages
All required packages are already in `requirements.txt`:
- `pyrogram` - Telegram bot framework
- `psutil` - System monitoring
- `apscheduler` - Background task scheduling
- `speedtest-cli` - Network speed testing

### Installation
No additional installation needed. All dependencies are included.

---

## Auto-Pause Monitor

The auto-pause feature runs in the background and checks system resources at configured intervals.

**Default Thresholds:**
- CPU: 80%
- RAM: 85%
- Disk: 10GB free space

**How It Works:**
1. Monitors system resources every 60 seconds (configurable)
2. When threshold exceeded, automatically pauses all active tasks
3. Sends notification to owner
4. Tasks must be manually resumed with `/resumeall`

**Configuration:**
Use `/settings` command to:
- Enable/disable auto-pause for each resource type
- Adjust monitoring interval
- View current system status

---

## Permission Levels

### All Authorized Users Can Use:
- `/speed`, `/dashboard`, `/taskdetails`, `/searchtasks`, `/filtertasks`
- `/history`, `/settings`, `/viewtoggle`, `/setalerts`
- `/queue`, `/pqueue`, `/rqueue`, `/prqueue`

### Owner Only:
- `/pauseall`, `/resumeall`

---

## Tips & Best Practices

1. **Use Dashboard First** - Get an overview before diving into specific tasks
2. **Search Before Browse** - Use `/searchtasks` to quickly find specific tasks
3. **Monitor History** - Check `/history` to track success rates
4. **Configure Auto-Pause** - Prevent system overload with `/settings`
5. **Use Interactive Buttons** - Faster than typing commands
6. **Set Priorities** - Ensure important tasks download first
7. **Filter by Status** - Focus on specific task types with `/filtertasks`

---

## Branding

This bot enhancement includes "justadi" signature in:
- `bot/__init__.py`
- `bot/modules/speedtest.py`
- `bot/modules/queue_manager.py`
- `bot/helper/telegram_helper/interactive_keyboards.py`
- `bot/modules/dashboard.py`
- `bot/modules/search_filter.py`
- `bot/modules/history.py`
- `bot/modules/settings_ui.py`
- `bot/helper/ext_utils/history_utils.py`
- `bot/core/handlers.py`

---

## Troubleshooting

### Commands Not Working
1. Restart the bot: `/restart`
2. Check bot logs: `/log`
3. Verify user permissions

### Auto-Pause Not Activating
1. Check settings with `/settings`
2. Ensure thresholds are configured
3. Verify monitoring is enabled

### History Not Showing
1. History starts tracking after bot restart
2. Maximum 200 entries stored
3. Old entries automatically removed

---

## Future Enhancements (Optional)

Potential features to add:
- Task scheduling (start downloads at specific times)
- Bandwidth limiting per task
- Download templates/presets
- Advanced filtering (by size, date, user)
- Export history to file
- Custom notification templates
- Task groups/categories
- Progress visualization graphs

---

## Support

For issues or questions:
1. Check `/help` for command reference
2. Use `/log` to get error details
3. Verify all dependencies installed
4. Check Python version (3.8+ required)

---

**Developed by: justadi**  
**Version: 2.0 - Enhanced UI/UX Edition**  
**Last Updated: 2024**
