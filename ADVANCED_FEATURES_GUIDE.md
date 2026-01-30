# Advanced Features Implementation Guide

> **Modified by:** justadi  
> **Date:** 2026-01-30  
> **Version:** 3.0.0

This document provides a comprehensive guide for the three newly implemented advanced features:
1. **Archive Management** - ZIP/TAR file compression and extraction
2. **Media Information Extraction** - Video/audio analysis with FFmpeg
3. **Web-Based Dashboard** - Real-time monitoring interface

---

## Table of Contents

1. [Archive Management](#archive-management)
2. [Media Information Extraction](#media-information-extraction)
3. [Web-Based Dashboard](#web-based-dashboard)
4. [Technologies Used](#technologies-used)
5. [Integration Guide](#integration-guide)
6. [Troubleshooting](#troubleshooting)

---

## Archive Management

### Overview

The Archive Management feature allows users to compress and extract files directly on the server before uploading to cloud storage or sending to Telegram. This reduces bandwidth usage and improves efficiency when dealing with large file collections.

### Supported Formats

| Format | Use Case | Compression | Speed |
|--------|----------|-------------|-------|
| ZIP | Universal, cross-platform | Good | Fast |
| TAR | Uncompressed archive | None | Very Fast |
| TAR.GZ | Unix standard | Excellent | Good |
| TAR.BZ2 | Better compression | Best | Slow |
| 7Z | Maximum compression | Best | Slow |

### Commands

#### `/zip <path> [format] [level]` - Create Archive

**Usage Examples:**

```
/zip /downloads/movies             # Create ZIP with default compression
/zip /downloads/video.mp4 zip 9    # Create ZIP with max compression (level 9)
/zip /downloads/folder tar.gz      # Create TAR.GZ for Unix systems
/zip /downloads/docs 7z 9          # Create 7Z with best compression
```

**Parameters:**

- `path` (required): Directory or file to compress
- `format` (optional, default=zip): zip | tar | tar.gz | tar.bz2 | 7z
- `level` (optional, default=6): Compression level 0-9
  - 0: No compression (store only)
  - 1-5: Light to medium compression
  - 6: Balanced (default)
  - 7-9: High compression (slower)

**Response Format:**

```
✅ Archive Created Successfully!

📦 Format: ZIP
📁 Filename: movies.zip
💾 Original Size: 4.52 GB
📦 Compressed Size: 3.14 GB
📊 Compression Ratio: 30.5%
⏱️ Time Taken: 45.23s
🚀 Speed: 115.42 MB/s

📍 Location: /downloads/movies.zip
```

#### `/unzip <path> [destination] [password]` - Extract Archive

**Usage Examples:**

```
/unzip /downloads/archive.zip                    # Extract to same directory
/unzip archive.zip /tmp/extracted                # Extract to specific path
/unzip secure.zip /tmp password123               # Extract with password
/unzip /downloads/backup.tar.gz /restore/data    # Extract TAR.GZ
```

**Parameters:**

- `path` (required): Path to archive file
- `destination` (optional, default=same dir): Where to extract files
- `password` (optional): For encrypted archives

**Response Format:**

```
✅ Archive Extracted Successfully!

📁 Archive: archive.zip
📦 Files Extracted: 247
💾 Total Size: 3.14 GB
⏱️ Time Taken: 32.15s
🚀 Speed: 97.66 MB/s

📍 Destination: /tmp/extracted
```

#### `/zipinfo <path>` - List Archive Contents

**Usage:**

```
/zipinfo archive.zip
/zipinfo /downloads/backup.tar.gz
```

**Response Format:**

```
📦 Archive Information

📁 File: archive.zip
📊 Files: 247
💾 Original Size: 3.14 GB
📦 Compressed Size: 2.85 GB
📈 Compression Ratio: 9.3%

Use /unzip to extract this archive
```

### Implementation Details

**Core Module:** `bot/core/archive_manager.py`

**Key Classes:**

```python
class ArchiveManager:
    """Manages all archive operations"""
    
    SUPPORTED_COMPRESS = ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z']
    SUPPORTED_EXTRACT = ['zip', 'tar', 'tar.gz', 'tar.bz2', '7z', 'rar']
    
    async def compress(source_path, output_path, format, compression_level)
    async def extract(archive_path, extract_to, password, files)
    async def list_zip_contents(zip_path)
    async def get_zip_stats(zip_path)
```

**Technologies:**

- **zipfile**: Python's native ZIP support
- **tarfile**: Python's native TAR support
- **py7zr**: 7-Zip format support
- **subprocess**: External binary execution (7z, unrar)
- **asyncio**: Async task management
- **ThreadPoolExecutor**: Parallel I/O operations

**Step-by-Step Process:**

1. **Compression**:
   - Validate source path exists
   - Calculate original size
   - Iterate through files/directories
   - Write to archive with specified compression
   - Calculate compression statistics
   - Return results with stats

2. **Extraction**:
   - Validate archive integrity
   - Create destination directory
   - Extract files based on format
   - Verify extraction success
   - Calculate extraction stats
   - Return results

3. **Size Calculations**:
   - Recursive directory traversal
   - File size summation
   - Ratio calculations: (1 - compressed/original) × 100

---

## Media Information Extraction

### Overview

The Media Information Extraction feature analyzes video and audio files to extract technical metadata. This helps users verify file quality before downloading/uploading and check codec compatibility.

### Use Cases

- **Quality Verification**: Check resolution, bitrate, codec before download
- **Compatibility Checking**: Ensure codecs are compatible with target platform
- **Bandwidth Estimation**: Calculate required bandwidth based on bitrate
- **Metadata Extraction**: Get title, artist, album information
- **Preview Generation**: Extract thumbnail frames from video

### Commands

#### `/mediainfo <path> [brief]` - Get Media Details

**Usage Examples:**

```
/mediainfo /downloads/movie.mkv          # Full detailed analysis
/mediainfo video.mp4 brief               # Brief summary
/mediainfo audio.flac
/mediainfo movie.avi brief
```

**Output - Full Mode:**

```
📊 Media Information

📁 File: movie.mkv
📦 Format: MATROSKA
⏱ Duration: 02:15:30
💾 Size: 4.85 GB
📡 Bitrate: 4.2 Mbps

🎬 Video Streams:
  Stream 1:
    • Codec: H.264 (High Profile)
    • Resolution: 1920x1080 @ 23.976 FPS
    • Aspect Ratio: 16:9
    • Bitrate: 3.8 Mbps
    • Pixel Format: yuv420p
    • Color Space: bt709

🔊 Audio Streams:
  Stream 1 - English:
    • Codec: AAC
    • Channels: 6 (5.1)
    • Sample Rate: 48000 Hz
    • Bitrate: 320 Kbps
  
  Stream 2 - Spanish:
    • Codec: AAC
    • Channels: 2 (Stereo)
    • Sample Rate: 48000 Hz
    • Bitrate: 128 Kbps

💬 Subtitle Streams:
  1. SUBRIP - English
  2. SUBRIP - Spanish [FORCED]
  3. ASS - English (Styled)

⭐ Quality: High (1080p)
```

**Output - Brief Mode:**

```
📊 Quick Media Stats

📁 File: movie.mkv
📦 Format: MATROSKA
⏱️ Duration: 02:15:30
💾 Size: 4.85 GB

🎬 Resolution: 1920x1080 @ 23.976 FPS
📹 Video Codec: H.264
🔊 Audio Codec: AAC
🎙️ Channels: 6 (5.1)

⭐ Quality: High (1080p)
```

#### `/thumbnail <path> [timestamp]` - Extract Video Thumbnail

**Usage Examples:**

```
/thumbnail video.mp4                # Extract at 5 seconds (default)
/thumbnail movie.mkv 00:00:30       # Extract at 30 seconds
/thumbnail film.avi 00:02:15        # Extract at 2 minutes 15 seconds
/thumbnail series.mkv 01:30:00      # Extract at 1 hour 30 minutes
```

**Timestamp Format:**

```
HH:MM:SS

Examples:
  00:00:05  → 5 seconds
  00:00:30  → 30 seconds
  00:01:00  → 1 minute
  00:02:45  → 2 minutes 45 seconds
  01:30:00  → 1 hour 30 minutes
```

**Response:**

```
✅ Thumbnail extracted successfully!

📁 Source: movie.mkv
⏱️ Timestamp: 00:00:30
💾 Size: 45 KB

[Image sent as media file]
```

#### `/mstats <path>` - Quick Media Statistics

**Usage:**

```
/mstats video.mp4
/mstats /downloads/movie.mkv
```

**Response:**

```
📊 Quick Media Stats

📁 File: video.mp4
📦 Format: H.264
⏱️ Duration: 00:45:30
💾 Size: 2.14 GB

🎬 Resolution: 1920x1080 @ 29.97 FPS
📹 Video Codec: H.264
🔊 Audio Codec: AAC
🎙️ Channels: 2 (Stereo)

⭐ Quality: High (1080p)
```

### Quality Rating System

| Rating | Criteria |
|--------|----------|
| Very Low | 480p or less |
| Low | 480-720p |
| Medium | 720p |
| High | 1080p |
| Excellent | 4K (2160p) |

*Ratings may include warnings for low bitrate relative to resolution*

### Implementation Details

**Core Module:** `bot/core/media_info.py`

**Key Classes:**

```python
class MediaInfoExtractor:
    """Extract and format media file information"""
    
    async def get_media_info(file_path) -> Dict
    def format_info(media_info, detailed=True) -> str
    def get_quality_rating(media_info) -> str
    async def extract_thumbnail(file_path, output_path, timestamp) -> bool
```

**Technologies:**

- **FFprobe**: Part of FFmpeg, analyzes media files
- **FFmpeg**: Extracts frames and generates thumbnails
- **JSON**: Parses FFprobe's JSON output
- **subprocess**: Executes FFmpeg commands
- **asyncio**: Async command execution

**Step-by-Step Process:**

1. **Information Extraction**:
   - Execute FFprobe with `-print_format json`
   - Parse JSON output
   - Extract and organize streams:
     - Video streams (codec, resolution, fps, bitrate)
     - Audio streams (codec, channels, bitrate)
     - Subtitle streams (codec, language)
   - Extract container information (format, duration, size)
   - Parse metadata (title, artist, album, etc.)

2. **Quality Rating**:
   - Check video height (resolution)
   - Compare bitrate to expected values
   - Generate rating based on specs
   - Add warnings for anomalies

3. **Thumbnail Generation**:
   - Seek to specified timestamp
   - Extract single frame
   - Scale to 320px width
   - Save as JPEG

---

## Web-Based Dashboard

### Overview

The Web-Based Dashboard provides a lightweight, real-time web interface for monitoring downloads, uploads, and tasks. It offers more screen space and interactive controls compared to the Telegram interface.

### Access

```
http://your-server-domain:8000/dashboard

Examples:
http://192.168.1.100:8000/dashboard
http://bot.example.com:8000/dashboard
http://localhost:8000/dashboard
```

### Features

#### Real-Time Updates

- **WebSocket Connection**: Instant status updates without page refresh
- **Automatic Reconnection**: Reconnects if connection drops
- **Live Progress Bars**: Visual feedback of download/upload progress
- **Status Badges**: Color-coded task status (downloading, uploading, completed, error, paused)

#### Task Management

| Action | Description | Usage |
|--------|-------------|-------|
| Pause | Temporarily stop a task | Click "Pause" button |
| Resume | Continue paused task | Click "Resume" button |
| Cancel | Stop and delete task | Click "Cancel" button |

#### Dashboard Metrics

```
┌─────────────────┬──────────────────┬─────────────────┬───────────────┐
│  Active Tasks   │   Total Speed    │ Total Downloads │ Total Uploads │
│        5        │    15.2 MB/s     │        24       │       18      │
└─────────────────┴──────────────────┴─────────────────┴───────────────┘
```

#### Task Cards

Each active task displays:

```
Task: video_download_2025.mp4
[Downloading] [████████░░░░░░░░░░] 45%

Progress: 45%        Speed: 5.2 MB/s
ETA: 00:05:30        Size: 500 MB / 1.1 GB

[Pause] [Resume] [Cancel]
```

#### System Information

```
CPU Usage: 35%
Memory Usage: 62%
Disk Usage: 48%
Uptime: 12 days 5 hours
```

### User Interface

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│  🟢 Connected    Download Manager Dashboard         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Stat Cards (4 columns - responsive)                │
│  ┌─────────┬─────────┬─────────┬─────────┐          │
│  │ Active  │  Speed  │ DL Cnt  │ UL Cnt  │          │
│  │   5     │15.2MB/s │  24     │  18     │          │
│  └─────────┴─────────┴─────────┴─────────┘          │
│                                                     │
│  Task Cards (Scrollable)                            │
│  ┌───────────────────────────────────────────┐      │
│  │ Task 1: Downloads...                      │      │
│  │ [████████░░░░░░░░░░] 45% Speed: 5.2 MB/s │      │
│  │ [Pause] [Resume] [Cancel]                 │      │
│  └───────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────┐      │
│  │ Task 2: Uploads...                        │      │
│  │ [███████████░░░░░░░░░░░░░] 62% ...        │      │
│  │ [Pause] [Resume] [Cancel]                 │      │
│  └───────────────────────────────────────────┘      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Implementation Details

**Core Module:** `bot/core/web_dashboard.py`

**Key Classes:**

```python
class DashboardManager:
    """Manages WebSocket connections and broadcasts"""
    
    async def connect(websocket)
    def disconnect(websocket)
    async def broadcast_task_status(task_id, status)
    async def broadcast_message(message, msg_type)
    async def send_dashboard_stats(stats)
    async def server_sent_events(task_id)

class DashboardEndpoints:
    """FastAPI endpoints for dashboard"""
    
    GET /dashboard → HTML page
    WebSocket /ws/dashboard → Real-time updates
    GET /api/tasks → Get all tasks
    GET /api/tasks/{id} → Task details
    POST /api/tasks/{id}/control → Control task
    GET /api/stats → Dashboard statistics
    GET /api/stream/{id} → SSE stream
```

**Technologies:**

- **FastAPI**: High-performance async web framework
- **Uvloop**: Ultra-fast event loop implementation
- **Jinja2**: Template engine for HTML rendering
- **WebSocket**: Bidirectional real-time communication
- **Bootstrap 5**: Responsive CSS framework
- **JavaScript Fetch API**: Client-side async requests
- **Server-Sent Events (SSE)**: One-way streaming

**Architecture:**

```
┌─────────────────────────────────────────┐
│         Client (Web Browser)            │
│  ┌──────────────────────────────────┐   │
│  │  HTML/CSS/JavaScript Dashboard   │   │
│  │  - Renders task cards            │   │
│  │  - Updates progress bars         │   │
│  │  - Sends control commands        │   │
│  └──────────────────────────────────┘   │
│           ↕ WebSocket ↕                  │
│  ┌──────────────────────────────────┐   │
│  │  Connection Manager (browser)    │   │
│  │  - Auto-reconnect logic          │   │
│  │  - Message routing               │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
         ↕ HTTP(S) WebSocket ↕
┌─────────────────────────────────────────┐
│       FastAPI Web Server                │
│  ┌──────────────────────────────────┐   │
│  │  DashboardManager                │   │
│  │  - WebSocket connections         │   │
│  │  - Message broadcasting          │   │
│  │  - Connection state tracking     │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  API Endpoints                   │   │
│  │  - /api/tasks - Get tasks        │   │
│  │  - /api/stats - Get statistics   │   │
│  │  - /api/control - Control tasks  │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
         ↕ Internal Async ↕
┌─────────────────────────────────────────┐
│       Task Manager (Core)               │
│  - Monitor task progress                │
│  - Broadcast status updates             │
│  - Execute control commands             │
└─────────────────────────────────────────┘
```

### WebSocket Message Format

**Task Status Update:**

```json
{
    "type": "task_status",
    "task_id": "task_123",
    "data": {
        "status": "downloading",
        "progress": 45,
        "speed": 5242880,
        "eta": 120,
        "current_size": 524288000,
        "total_size": 1048576000,
        "name": "video_file.mp4"
    },
    "timestamp": "2026-01-30T12:34:56.789Z"
}
```

**Dashboard Statistics:**

```json
{
    "type": "dashboard_stats",
    "data": {
        "active_tasks": 5,
        "total_downloads": 24,
        "total_uploads": 18,
        "total_speed": 16000000,
        "cpu_usage": 35.2,
        "memory_usage": 62.5,
        "disk_usage": 48.3,
        "uptime": 1050000
    },
    "timestamp": "2026-01-30T12:34:56.789Z"
}
```

---

## Technologies Used

### Archive Management

| Technology | Version | Purpose |
|-----------|---------|---------|
| zipfile | Built-in | ZIP compression/extraction |
| tarfile | Built-in | TAR format support |
| py7zr | Latest | 7-Zip support |
| subprocess | Built-in | External binary execution |
| asyncio | Built-in | Async operations |

### Media Information

| Technology | Version | Purpose |
|-----------|---------|---------|
| FFmpeg | 5.x+ | Media analysis and processing |
| FFprobe | 5.x+ | File information extraction |
| json | Built-in | JSON parsing |
| subprocess | Built-in | Command execution |

### Web Dashboard

| Technology | Version | Purpose |
|-----------|---------|---------|
| FastAPI | 0.100+ | Web framework |
| Uvloop | Latest | High-performance event loop |
| Jinja2 | 3.x+ | Template engine |
| Bootstrap | 5.1+ | UI framework |
| JavaScript | ES6+ | Client-side logic |
| WebSocket | RFC 6455 | Real-time communication |

---

## Integration Guide

### Installation Requirements

**System Packages:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg python3-dev

# Optional for better compression
sudo apt-get install -y p7zip-full unrar
```

**Python Packages:**

```bash
# Already in requirements.txt
pip install py7zr
pip install fastapi uvloop
```

### Configuration

**1. Enable Web Dashboard:**

Edit `config_sample.py`:

```python
# Enable web dashboard
WEB_DASHBOARD_ENABLED = True
WEB_DASHBOARD_PORT = 8000
WEB_DASHBOARD_HOST = "0.0.0.0"
```

**2. Archive Settings:**

```python
# Archive compression defaults
ARCHIVE_DEFAULT_FORMAT = "zip"
ARCHIVE_DEFAULT_LEVEL = 6
ARCHIVE_TEMP_DIR = "/tmp"  # Temporary storage during compression
```

**3. Media Info Settings:**

```python
# FFmpeg paths
FFMPEG_PATH = "/usr/bin/ffmpeg"
FFPROBE_PATH = "/usr/bin/ffprobe"
THUMBNAIL_SIZE = "320:-1"  # Width:-1 for auto height
THUMBNAIL_FORMAT = "jpg"
```

### Integration with Download Tasks

**Auto-Archive After Download:**

```python
# After download completes
if auto_archive_enabled:
    success, msg, stats = await archive_manager.compress(
        source_path=downloaded_file,
        output_path=f"{downloaded_file}.zip",
        format="zip",
        compression_level=6
    )
```

**Media Info Check Before Download:**

```python
# Before downloading media file
info = await media_info_extractor.get_media_info(local_file)
quality = media_info_extractor.get_quality_rating(info)
await bot.send_message(chat_id, f"Quality: {quality}")
```

---

## Troubleshooting

### Archive Management Issues

**Problem:** `7z command not found`

**Solution:**
```bash
sudo apt-get install p7zip-full
```

**Problem:** `unrar: command not found`

**Solution:**
```bash
sudo apt-get install unrar
```

**Problem:** `Permission denied when extracting`

**Solution:**
```bash
# Ensure output directory is writable
chmod 755 /path/to/destination
```

### Media Information Issues

**Problem:** `FFprobe not found`

**Solution:**
```bash
sudo apt-get install ffmpeg
```

**Problem:** `No audio/video streams found`

**Solution:**
- File might be corrupted
- Check file format is supported
- Try with a different file

**Problem:** `Thumbnail extraction failed`

**Solution:**
- Verify video file is valid
- Check timestamp is within video duration
- Ensure write permission to output directory

### Web Dashboard Issues

**Problem:** `Connection refused` when accessing dashboard

**Solution:**
```bash
# Check if service is running
sudo systemctl status bot

# Check port is open
sudo netstat -tulpn | grep 8000

# Firewall rules
sudo ufw allow 8000
```

**Problem:** `WebSocket connection drops frequently`

**Solution:**
- Check network stability
- Increase reconnection timeout
- Monitor server resources

**Problem:** `Dashboard shows no tasks`

**Solution:**
- Verify task manager integration
- Check database connection
- Ensure broadcast methods are called

### Performance Optimization

**For Large Archives (>1GB):**

```python
# Use 7Z for maximum compression
await archive_manager.compress(
    source_path=path,
    output_path=output,
    format="7z",
    compression_level=9
)
```

**For Frequent Extractions:**

```python
# Use ThreadPoolExecutor with more workers
archive_manager = ArchiveManager(max_workers=8)
```

**For Media Analysis:**

```python
# Use brief mode for faster response
await media_info_extractor.format_info(info, detailed=False)
```

---

## Testing

### Unit Tests

```python
# Test archive operations
async def test_archive_zip():
    success, msg, stats = await archive_manager.compress(
        test_file,
        "test.zip",
        "zip",
        6
    )
    assert success == True
    assert stats['compression_ratio'] > 0

# Test media extraction
async def test_media_info():
    info = await media_info_extractor.get_media_info("test.mp4")
    assert info is not None
    assert len(info['video_streams']) > 0
```

### Integration Tests

```bash
# Test compression
/zip /test/folder zip

# Test extraction
/unzip /test/archive.zip /test/extracted

# Test media info
/mediainfo /test/video.mp4

# Access dashboard
curl http://localhost:8000/dashboard
```

---

## Performance Metrics

### Archive Operations

- ZIP compression: 50-200 MB/s
- TAR.GZ compression: 30-100 MB/s
- 7Z compression: 20-50 MB/s (higher ratio)
- Extraction: 100-300 MB/s

### Media Analysis

- FFprobe analysis: 0.5-2 seconds per file
- Thumbnail generation: 0.2-0.5 seconds
- Quality rating: <100ms

### Web Dashboard

- Page load time: <1 second
- WebSocket latency: 50-100ms
- Task update frequency: 1-2 seconds

---

## Future Enhancements

1. **Selective File Compression** - Choose specific files to compress
2. **Archive Encryption** - Password-protected archives
3. **Batch Operations** - Compress multiple files/folders
4. **Advanced Filtering** - Filter tasks by status, type, date
5. **Export Reports** - Export task history and statistics
6. **Mobile App** - Native mobile dashboard application
7. **Cloud Integration** - Direct cloud upload after compression
8. **Video Transcoding** - Convert between formats
9. **Advanced Metadata Editing** - Modify file metadata
10. **Scheduled Operations** - Schedule compression/extraction tasks

---

## Support

For issues or questions, please refer to:

- **Documentation**: Check this guide first
- **Issue Tracker**: GitHub Issues
- **Community**: Telegram Group
- **Author**: @justadi

---

**Last Updated:** 2026-01-30  
**Maintained by:** justadi  
**Status:** Production Ready ✅

