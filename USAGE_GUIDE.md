# Complete Usage Guide - Commands & Examples

**Modified by: justadi**  
**Version: 3.0.0**  
**Date: January 30, 2026**

---

## 📚 Table of Contents

1. [Command Categories](#command-categories)
2. [Download Commands](#download-commands)
3. [Queue Management](#queue-management)
4. [Task Management](#task-management)
5. [File Operations](#file-operations)
6. [System Commands](#system-commands)
7. [Admin Commands](#admin-commands)
8. [Practical Examples](#practical-examples)

---

## 📂 Command Categories

### Download & Mirroring (6 commands)
Mirror files from various sources to Google Drive

### Leeching (4 commands)
Download files from Google Drive to Telegram

### Queue Management (6 commands)
Control active downloads and manage priorities

### Task Management (5 commands)
Search, filter, and manage download history

### File Operations (5 commands)
Archive, extract, and process media files

### System Monitoring (6 commands)
Check bot status and system resources

### Administration (8 commands)
Owner-only bot management commands

---

## 📥 Download Commands

### 1. `/mirror` - Mirror to Google Drive

**Basic Usage:**
```
/mirror <link>
```

**Full Usage:**
```
/mirror <link> [--up-limit 10M] [--extract] [--index-link]
```

**Examples:**

**Example 1: Simple Direct Link**
```
/mirror https://example.com/file.zip
```

**Result:**
```
⬇️ Starting download...
File: file.zip
📊 Size: 500 MB
URL: https://example.com/file.zip

[After completion]
✅ Download Complete!
📁 file.zip - 500 MB
☁️ Google Drive: [Drive Link]
🌐 Index URL: [Index Link] (if configured)
```

**Example 2: Mirror with Extraction**
```
/mirror https://example.com/archive.zip --extract
```

**Result:**
```
⬇️ Downloading: archive.zip
✅ Download Complete
🔄 Extracting files...
✅ Extraction Complete!
📁 Files extracted and uploaded to Drive
```

**Example 3: YouTube Video**
```
/mirror https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Result:**
```
⬇️ Downloading video...
📺 Title: Video Title
⏱️ Duration: 4:33
📊 Size: 50 MB
✅ Complete!
☁️ Uploaded to Drive
```

**Example 4: Torrent Magnet Link**
```
/mirror magnet:?xt=urn:btih:HASH...
```

**Result:**
```
⬇️ Adding torrent...
📊 Pieces: 1000
📁 Files: 5
⏳ Downloading...
✅ Complete!
```

---

### 2. `/qmirror` - Mirror with qBittorrent

**Usage:**
```
/qmirror <magnet_or_torrent_link>
```

**Example: Torrent Download**
```
/qmirror https://example.com/torrent.torrent
```

**Result:**
```
🧲 Adding to qBittorrent...
📊 Peers: 45
⬇️ Downloading...
[After completion]
✅ Upload to Drive Complete!
```

---

### 3. `/jdmirror` - Mirror with JDownloader

**Usage:**
```
/jdmirror <link>
```

**Example: JDownloader Download**
```
/jdmirror https://example-host.com/file.rar
```

**Result:**
```
🔗 Adding to JDownloader...
⬇️ Downloading...
✅ Complete!
```

---

### 4. `/nzbmirror` - Mirror NZB Files

**Usage:**
```
/nzbmirror <nzb_link>
```

**Example: NZB Download**
```
/nzbmirror https://example-nzb-site.com/file.nzb
```

**Result:**
```
📦 Processing NZB...
⬇️ Downloading from Usenet...
✅ Upload to Drive Complete!
```

---

## 📤 Leech Commands

### 1. `/leech` - Leech from Google Drive

**Usage:**
```
/leech <file_id_or_link>
```

**Example 1: By File ID**
```
/leech 1A2B3C4D5E6F7G8H9I0J
```

**Result:**
```
⬇️ Downloading from Google Drive...
📁 file.zip - 500 MB
⬆️ Uploading to Telegram...
✅ Upload Complete!
📥 File sent to chat
```

**Example 2: By Google Drive Link**
```
/leech https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J
```

**Result:**
```
[Same as above]
```

**Example 3: Bulk Leech (Multiple Files)**
```
Send multiple file IDs in one message:
1A2B3C4D5E6F7G8H9I0J
2B3C4D5E6F7G8H9I0J1K
3C4D5E6F7G8H9I0J1K2L
```

**Result:**
```
⬇️ Downloading 3 files...
⬆️ Uploading files...
✅ All uploads complete!
```

---

### 2. `/qleech` - Leech with qBittorrent

**Usage:**
```
/qleech <torrent_link>
```

**Example:**
```
/qleech magnet:?xt=urn:btih:HASH...
```

---

### 3. `/ytdl` - YouTube Download

**Usage:**
```
/ytdl <youtube_url>
```

**Example: Download Video**
```
/ytdl https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Result:**
```
🎬 Processing...
📺 Title: Video Title
📊 Best Format: 1080p
⬇️ Downloading...
☁️ Uploading to Drive...
✅ Complete!
```

---

## 🔄 Queue Management

### 1. `/queue` - View Download Queue

**Usage:**
```
/queue
```

**Example Output:**
```
📋 Queue Status
━━━━━━━━━━━━━━━━━━━━━━━━━━
Active Tasks: 3
Total Speed: 15.2 MB/s
━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ file1.zip [500 MB]
   ████████░░ 80%
   📊 Speed: 5.5 MB/s
   ⏱️ ETA: 2 minutes
   [Pause] [Resume] [Cancel]

2️⃣ video.mkv [2 GB]
   ██████░░░░ 60%
   📊 Speed: 8.2 MB/s
   ⏱️ ETA: 4 minutes
   [Pause] [Resume] [Cancel]

3️⃣ archive.7z [300 MB]
   ██████████ 100% ✅
   Status: Uploading...

━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 Storage Used: 45%
🎯 Priority: Normal
```

### 2. `/pqueue` - Pause Download

**Usage:**
```
/pqueue <gid>
```

**Example:**
```
/pqueue abc123def456
```

**Result:**
```
✅ Download paused
📁 file.zip paused at 80%
(Resume with /rqueue abc123def456)
```

### 3. `/rqueue` - Resume Download

**Usage:**
```
/rqueue <gid>
```

**Example:**
```
/rqueue abc123def456
```

**Result:**
```
✅ Download resumed
📁 file.zip resuming from 80%
⬇️ Speed: 5.2 MB/s
```

### 4. `/prqueue` - Set Priority

**Usage:**
```
/prqueue <gid> <priority>
```

**Priority Levels:**
- `1` - Very High
- `2` - High
- `3` - Normal
- `4` - Low
- `5` - Very Low

**Example 1: Set High Priority**
```
/prqueue abc123def456 2
```

**Result:**
```
✅ Priority set to High
📁 file.zip moved to high priority
Will start after current task completes
```

**Example 2: Set Low Priority**
```
/prqueue xyz789uvw012 4
```

### 5. `/pauseall` - Pause All Downloads

**Usage:**
```
/pauseall
```
*(Owner only)*

**Result:**
```
⏸️ All downloads paused!
📊 3 tasks paused
⏱️ Paused tasks: file1, file2, file3
(Resume with /resumeall)
```

### 6. `/resumeall` - Resume All Downloads

**Usage:**
```
/resumeall
```
*(Owner only)*

**Result:**
```
▶️ Resuming all downloads!
📊 3 tasks resumed
⏱️ Total speed: 12.5 MB/s
```

---

## 📊 Task Management

### 1. `/history` - Download History

**Usage:**
```
/history
```

**Example Output:**
```
📚 Download History

[Today]
✅ 14:30 - file1.zip (500 MB)
✅ 13:45 - video.mkv (2 GB)
❌ 13:20 - archive.rar (1 GB) - Failed
⏳ 12:30 - document.pdf (50 MB) - Uploading

[Yesterday]
✅ 18:45 - backup.zip (3 GB)
✅ 16:20 - movie.mkv (1.5 GB)

[Pages: 1/5] [Next Page] [Latest 100] [Search]
```

### 2. `/search` - Search Downloads

**Usage:**
```
/search <query>
```

**Examples:**

**Search by Name:**
```
/search movie
```

**Result:**
```
🔍 Search Results: "movie"

✅ 2024-01-30 movie.mkv (2 GB)
✅ 2024-01-29 movies.zip (500 MB)
✅ 2024-01-28 filmography.tar (1 GB)

[3 results found]
```

**Search by Extension:**
```
/search .mp4
```

**Search with Size:**
```
/search >100M
```

### 3. `/filter` - Filter Tasks

**Usage:**
```
/filter <criteria>
```

**Examples:**

**Filter by Status:**
```
/filter status:completed
```

**Result:**
```
✅ Completed Downloads (145)

file1.zip ✅
file2.mkv ✅
archive.7z ✅
...
[Showing 1-20 of 145]
```

**Filter by Size:**
```
/filter size:>1G
```

**Result:**
```
📊 Downloads > 1 GB (23)

large_file.zip (5 GB) ✅
video.mkv (2.5 GB) ✅
...
```

**Filter by Date:**
```
/filter date:today
```

### 4. `/taskdetails` - Task Details

**Usage:**
```
/taskdetails <gid>
```

**Example:**
```
/taskdetails abc123def456
```

**Result:**
```
📋 Task Details
━━━━━━━━━━━━━━━━━━━━━━━━━
File: file.zip
Size: 500 MB
Status: Downloading ⏳
Progress: ████████░░ 80%

📊 Speed: 5.5 MB/s
⏱️ ETA: 2m 30s
⬇️ Downloaded: 400 MB
⬆️ Uploaded: 0 MB

🔗 Source: https://example.com/file.zip
📁 Destination: Google Drive
🏷️ Category: Documents
🎯 Priority: Normal

[Pause] [Resume] [Cancel] [More Info]
```

### 5. `/cancel` - Cancel Download

**Usage:**
```
/cancel <gid>
```

**Example:**
```
/cancel abc123def456
```

**Result:**
```
✅ Download cancelled
📁 file.zip cancelled
⚠️ Incomplete file removed
```

---

## 🗂️ File Operations

### 1. `/zip` - Create Archive

**Usage:**
```
/zip <source_path> [format] [level]
```

**Supported Formats:**
- `zip` - Default, universal
- `tar` - No compression
- `tar.gz` - Good compression
- `tar.bz2` - Better compression
- `7z` - Best compression

**Compression Levels:** 0-9 (0=store, 9=max)

**Examples:**

**Example 1: Basic ZIP**
```
/zip /downloads/folder
```

**Result:**
```
🔄 Creating ZIP archive...
✅ Archive Created!
📦 folder.zip (450 MB)
💾 Original: 500 MB
📦 Compressed: 450 MB
📊 Ratio: 90%
```

**Example 2: High Compression (7Z)**
```
/zip /downloads/videos 7z 9
```

**Result:**
```
🔄 Creating 7Z archive...
✅ Archive Created!
📦 videos.7z (150 MB)
💾 Original: 500 MB
📦 Compressed: 150 MB
📊 Ratio: 30%
⏱️ Time: 45 seconds
```

**Example 3: TAR.GZ**
```
/zip /downloads/documents tar.gz 6
```

---

### 2. `/unzip` - Extract Archive

**Usage:**
```
/unzip <archive_path> [destination] [password]
```

**Examples:**

**Example 1: Basic Extraction**
```
/unzip /downloads/archive.zip
```

**Result:**
```
🔄 Extracting archive...
✅ Extraction Complete!
📁 Files extracted: 45
💾 Total size: 500 MB
⏱️ Time: 10 seconds
📍 Location: /downloads/
```

**Example 2: Extract to Specific Location**
```
/unzip /downloads/backup.zip /tmp/extracted
```

**Result:**
```
🔄 Extracting to /tmp/extracted...
✅ Complete!
📁 45 files extracted
📍 /tmp/extracted/
```

**Example 3: Extract with Password**
```
/unzip /downloads/protected.zip /tmp mypassword123
```

---

### 3. `/zipinfo` - Archive Information

**Usage:**
```
/zipinfo <archive_path>
```

**Example:**
```
/zipinfo /downloads/archive.zip
```

**Result:**
```
📦 Archive Information
━━━━━━━━━━━━━━━━━━━━━━━━━
File: archive.zip
📁 Total Files: 45
💾 Original Size: 500 MB
📦 Compressed: 450 MB
📊 Ratio: 90%
🔒 Encrypted: No

Type: ZIP
Created: 2024-01-30
Modified: 2024-01-30
```

---

### 4. `/mediainfo` - Media Information

**Usage:**
```
/mediainfo <file_path>
```

**Example:**
```
/mediainfo /downloads/movie.mkv
```

**Result:**
```
🎬 Media Information
━━━━━━━━━━━━━━━━━━━━━━━━━
File: movie.mkv
📊 Size: 2 GB
📺 Format: Matroska

🎥 Video:
   Codec: H.264
   Resolution: 1920x1080 (1080p)
   FPS: 23.976
   Bitrate: 8000 kbps

🔊 Audio:
   Codec: AAC
   Channels: 2.0 (Stereo)
   Bitrate: 192 kbps
   Language: English

⏱️ Duration: 2h 15m 30s
```

---

### 5. `/thumbnail` - Extract Thumbnail

**Usage:**
```
/thumbnail <video_path>
```

**Example:**
```
/thumbnail /downloads/movie.mkv
```

**Result:**
```
🖼️ Extracting thumbnail...
✅ Thumbnail extracted!
[Image sent to chat]
📊 Resolution: 1920x1080
```

---

## 🖥️ System Commands

### 1. `/stats` - System Statistics

**Usage:**
```
/stats
```

**Example Output:**
```
📊 System Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━
🖥️ Server Information:
   Hostname: linux-server
   OS: Ubuntu 22.04 LTS
   Uptime: 15 days 3 hours
   Kernel: 5.15.0

💾 Storage:
   Total: 1 TB
   Used: 450 GB (45%)
   Free: 550 GB (55%)
   Download Dir: 350 GB

🔋 Resources:
   CPU: 4 cores @ 2.4 GHz
   CPU Usage: 35%
   Memory: 8 GB
   RAM Usage: 3.2 GB (40%)

📊 Network:
   Upload: 125 MB/s
   Download: 125 MB/s
   Ping: 15 ms

🤖 Bot:
   Status: ✅ Running
   Version: 3.0.0
   Uptime: 2 days 4 hours
   Active Tasks: 2
   Database: ✅ Connected

━━━━━━━━━━━━━━━━━━━━━━━━━
Last Updated: 2024-01-30 15:45:30
```

### 2. `/ping` - Bot Latency

**Usage:**
```
/ping
```

**Example Output:**
```
🏓 Pong!
⏱️ Response time: 245 ms
✅ Bot is responding
```

### 3. `/speed` - Network Speed Test

**Usage:**
```
/speed
```

**Example Output:**
```
⚡ Running Speed Test...
[After 30-60 seconds]

🚀 Speed Test Results
━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Download: 125.5 Mbps
📤 Upload: 95.2 Mbps
🏓 Ping: 15 ms
🌍 Location: New York, USA

━━━━━━━━━━━━━━━━━━━━━━━━━
[Retry] [Close]
```

### 4. `/dashboard` - Web Dashboard

**Usage:**
```
/dashboard
```

**Result:**
```
🌐 Opening Dashboard...

Access at: http://your-server:8050/dashboard

Dashboard Features:
✅ Real-time monitoring
✅ System stats
✅ Task control
✅ File management
✅ Mobile-responsive
```

### 5. `/help` - Command Help

**Usage:**
```
/help
```

**Result:**
```
📚 Mirror-Leech Bot Help
━━━━━━━━━━━━━━━━━━━━━━━━━

📥 Download Commands
/mirror - Mirror to Drive
/leech - Leech from Drive
/qmirror - Mirror with qBittorrent
... [all commands listed]

[Use /help <command> for details]
```

### 6. `/start` - Initialize Bot

**Usage:**
```
/start
```

**Result:**
```
👋 Welcome to Mirror-Leech Bot v3.0.0!
✅ Bot initialized
🎯 Ready to use!

Quick start:
/help - Show all commands
/mirror <link> - Download
/stats - System info
```

---

## 👨‍💼 Admin Commands

### 1. `/authorize` - Add User

**Usage:**
```
/authorize <user_id>
```
*(Owner only)*

**Example:**
```
/authorize 123456789
```

**Result:**
```
✅ User 123456789 authorized
👤 Can now use bot
```

### 2. `/unauthorize` - Remove User

**Usage:**
```
/unauthorize <user_id>
```
*(Owner only)*

**Example:**
```
/unauthorize 123456789
```

### 3. `/bsetting` - Bot Settings

**Usage:**
```
/bsetting
```
*(Owner only)*

**Result:**
```
⚙️ Bot Settings Panel

[Buttons for each setting]
- Download Limit
- Bandwidth Limit
- Task Limit
- Auto-pause Threshold
- ... [more options]
```

### 4. `/restart` - Restart Bot

**Usage:**
```
/restart
```
*(Owner only)*

**Result:**
```
🔄 Restarting bot...
[Bot restarts]
✅ Bot restarted!
🤖 Ready to use
```

### 5. `/log` - View Logs

**Usage:**
```
/log
```
*(Owner only)*

**Result:**
```
📋 Recent Logs
━━━━━━━━━━━━━━━━━━━━━━
[15:45] Bot started
[15:46] Aria2 connected
[15:47] Database initialized
[15:48] First user connected
[15:50] Download started
... [more logs]
```

### 6. `/shell` - Run Shell Commands

**Usage:**
```
/shell <command>
```
*(Owner only)*

**Example:**
```
/shell df -h
```

**Result:**
```
Filesystem      Size  Used Avail Use%
/dev/sda1       1.0T  450G  550G  45%
tmpfs           3.9G  2.1G  1.8G  54%
```

---

## 🎯 Practical Examples

### Scenario 1: Download Large File to Google Drive

**Goal:** Download 5GB movie file to Google Drive

**Steps:**
```
1. Send file link
/mirror https://example.com/movie.mkv

2. Bot starts downloading
⬇️ 5 GB file
📊 Speed: 10 MB/s
⏱️ ETA: 8 minutes

3. File uploads to Drive automatically
✅ Complete!
🔗 Google Drive link provided
```

**Check progress:**
```
/queue
/taskdetails <gid>
```

---

### Scenario 2: Archive and Backup Multiple Folders

**Goal:** Create high-compression backup of important folders

**Steps:**
```
1. Create archive with maximum compression
/zip /backups 7z 9

2. Monitor progress
⏱️ Creating 7Z archive...
📊 Compression ratio: 85%

3. Mirror to Drive
/mirror /backups.7z

4. Verify
/history
✅ Backup complete!
```

---

### Scenario 3: Manage Multiple Parallel Downloads

**Goal:** Download 3 files simultaneously with priority

**Steps:**
```
1. Start downloads
/mirror https://example.com/file1.zip
/mirror https://example.com/file2.mkv
/mirror https://example.com/file3.tar.gz

2. Set priorities
/prqueue gid1 1  (High - file2.mkv)
/prqueue gid2 3  (Normal)
/prqueue gid3 4  (Low)

3. Monitor queue
/queue

4. Manage bandwidth
/limit 20M  (Set global 20MB/s limit)

5. View results
/history
✅ All downloads complete!
```

---

### Scenario 4: Download Torrent and Leech

**Goal:** Download torrent and share via Telegram

**Steps:**
```
1. Mirror torrent to Drive
/qmirror magnet:?xt=urn:btih:...

2. Wait for completion
⏳ 1-2 hours (depends on size)

3. Leech from Drive to Telegram
/leech <file_id>

4. Share with users
✅ Files sent to chat
```

---

### Scenario 5: Schedule Recurring Backup

**Goal:** Auto-backup important files every day at 2 AM

**Steps:**
```
1. Create schedule
/schedule https://backup.example.com/daily.zip

2. Configure
→ Time: 02:00 (2 AM)
→ Recurrence: Daily
→ Enabled: ✅

3. Verify
/schedule
→ Shows: Daily backup at 2 AM ✅

4. Let it run automatically!
Every day at 2 AM, bot downloads backup
```

---

## 💡 Tips & Tricks

### Tip 1: Bulk Download
```
Send multiple links in one message
/mirror link1
/mirror link2
/mirror link3
```

### Tip 2: Extract on Download
```
/mirror archive.zip --extract
Automatically extracts after download
```

### Tip 3: Priority Management
```
Set high priority for important tasks
/prqueue abc123 1
Task starts first
```

### Tip 4: Bandwidth Optimization
```
/limit 20M  - Limits all downloads to 20MB/s
Prevents network congestion
```

### Tip 5: Monitor While Busy
```
/stats - Quick overview
/queue - Current downloads
/history - Recent activity
```

---

**Modified by:** justadi  
**Version:** 3.0.0  
**Last Updated:** January 30, 2026  
**Status:** ✅ Complete
