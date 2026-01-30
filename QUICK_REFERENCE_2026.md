# Quick Reference Guide - Advanced Features

**Version:** 3.0.0 | **Author:** justadi | **Date:** 2026-01-30

---

## Archive Management

### Create Archive

```bash
/zip /path/to/files                    # ZIP (default level 6)
/zip /path/to/file.mp4 zip 9           # ZIP max compression
/zip /downloads/docs tar.gz            # TAR.GZ format
/zip /downloads/folder 7z 9            # 7Z best compression
```

**Formats:** zip | tar | tar.gz | tar.bz2 | 7z  
**Levels:** 0-9 (0=none, 6=default, 9=max)

### Extract Archive

```bash
/unzip /path/to/archive.zip            # Extract same directory
/unzip archive.zip /tmp/extracted      # Extract to path
/unzip secure.7z /tmp password123      # With password
```

### List Contents

```bash
/zipinfo archive.zip                   # Show file count & ratio
```

---

## Media Information

### Get Details

```bash
/mediainfo /downloads/movie.mkv        # Full analysis
/mediainfo video.mp4 brief             # Brief summary
```

### Extract Thumbnail

```bash
/thumbnail video.mp4                   # At 5 seconds (default)
/thumbnail movie.mkv 00:00:30          # At 30 seconds
/thumbnail film.avi 00:02:15           # At 2:15
```

**Time Format:** HH:MM:SS

### Quick Stats

```bash
/mstats video.mp4                      # Essential info only
```

---

## Web Dashboard

### Access

```
http://your-server:8000/dashboard

Examples:
http://192.168.1.100:8000/dashboard
http://bot.example.com:8000/dashboard
```

### Features

- Real-time progress bars
- Task control (pause/resume/cancel)
- Live speed monitoring
- System statistics
- Connection status indicator

### Controls

| Action | Button |
|--------|--------|
| Pause Task | Pause |
| Resume Task | Resume |
| Cancel Task | Cancel |

---

## Installation

### System Packages

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg p7zip-full unrar

# CentOS/RHEL
sudo yum install ffmpeg p7zip unrar
```

### Enable Features

Edit `config_sample.py`:

```python
ARCHIVE_ENABLED = True
MEDIA_INFO_ENABLED = True
WEB_DASHBOARD_ENABLED = True
WEB_DASHBOARD_PORT = 8000
```

### Restart

```bash
/restart
```

---

## Performance

### Speed

| Operation | Speed |
|-----------|-------|
| ZIP (L6) | 50-200 MB/s |
| TAR.GZ | 30-100 MB/s |
| 7Z (L9) | 20-50 MB/s |
| Extract | 100-300 MB/s |
| Media Analysis | 0.5-2s |
| Thumbnail | 0.2-0.5s |
| Dashboard Load | <1s |

---

## Examples

### Archive Downloaded Files

```python
await archive_manager.compress(
    '/downloads/movie.mp4',
    '/downloads/movie.zip',
    'zip',
    6
)
```

### Check Video Before Download

```python
info = await media_info_extractor.get_media_info('/downloads/video.mp4')
quality = media_info_extractor.get_quality_rating(info)
# Returns: "High (1080p)", "Excellent (4K)", etc.
```

### Update Dashboard

```python
await dashboard_manager.broadcast_task_status(
    'task_123',
    {
        'status': 'downloading',
        'progress': 45,
        'speed': 5242880,  # 5 MB/s
        'eta': 120,
        'current_size': 524288000,
        'total_size': 1048576000
    }
)
```

---

## Troubleshooting

### "7z command not found"
```bash
sudo apt-get install p7zip-full
```

### "FFprobe not found"
```bash
sudo apt-get install ffmpeg
```

### "Connection refused" for dashboard
```bash
# Check service running
sudo systemctl status bot

# Check port open
sudo netstat -tulpn | grep 8000

# Open firewall
sudo ufw allow 8000
```

### Archive extraction fails
```bash
# Check permissions
chmod 755 /path/to/destination

# Check archive integrity
/zipinfo archive.zip
```

---

## Documentation

- **Full Guide:** `ADVANCED_FEATURES_GUIDE.md`
- **Features:** `NEW_FEATURES_GUIDE.md`
- **Implementation:** `IMPLEMENTATION_2026.md`
- **Help:** `/help <command>`

---

## Support

**Need help?**

1. Check `/help archive`, `/help mediainfo`, `/help dashboard`
2. Review `ADVANCED_FEATURES_GUIDE.md`
3. Check bot logs: `/log`
4. Report issues: GitHub Issues

---

**Made with ❤️ by justadi**
