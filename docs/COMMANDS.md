# Command Reference

This document lists all bot commands, shortcuts, and example usage.
If CMD_SUFFIX is configured, append it to each command (for example, /mirror1).

## General

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /start | /hi | /start | /start | - |
| /help | /menu, /commands | /help [keyword] | /help downloads | - |

## Downloads & Uploads

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /mirror | /m, /download, /dl | /mirror <link> [args] | /mirror https://example.com/file.zip | - |
| /leech | /l, /upload, /ul | /leech <link> [args] | /leech https://example.com/file.zip | - |
| /qbmirror | /qm | /qbmirror <magnet|torrent> | /qbmirror magnet:?xt=urn:btih:... | - |
| /qbleech | /ql | /qbleech <magnet|torrent> | /qbleech magnet:?xt=urn:btih:... | - |
| /jdmirror | /jm | /jdmirror <link> | /jdmirror https://example.com/file.zip | - |
| /jdleech | /jl | /jdleech <link> | /jdleech https://example.com/file.zip | - |
| /ytdl | /y | /ytdl <url> [options] | /ytdl https://youtu.be/xxxxx | - |
| /ytdlleech | /yl | /ytdlleech <url> [options] | /ytdlleech https://youtu.be/xxxxx | - |
| /nzbmirror | /nm | /nzbmirror <nzb_url> | /nzbmirror https://example.com/file.nzb | - |
| /nzbleech | /nl | /nzbleech <nzb_url> | /nzbleech https://example.com/file.nzb | - |

## Drive & Rclone

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /clone | - | /clone <link|path> | /clone https://drive.google.com/... | - |
| /count | - | /count <link|path> | /count https://drive.google.com/... | - |
| /del | - | /del <link|path> | /del https://drive.google.com/... | - |
| /list | - | /list <query> | /list ubuntu | - |

## Queue & Status

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /status | /st | /status | /status | - |
| /queue | /tasks | /queue | /queue | - |
| /pqueue | - | /pqueue <gid> | /pqueue 1a2b3c | - |
| /rqueue | - | /rqueue <gid> | /rqueue 1a2b3c | - |
| /prqueue | - | /prqueue <gid> <level> | /prqueue 1a2b3c 1 | - |
| /pauseall | - | /pauseall | /pauseall | Owner only |
| /resumeall | - | /resumeall | /resumeall | Owner only |
| /cancel | /c | /cancel <gid> | /cancel 1a2b3c | - |
| /cancelall | - | /cancelall | /cancelall | Owner only |
| /forcestart | /fs | /forcestart <gid> | /forcestart 1a2b3c | Owner only |
| /taskdetails | - | /taskdetails <gid> | /taskdetails 1a2b3c | - |

## Search & History

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /search | - | /search <query> | /search linux iso | - |
| /nzbsearch | - | /nzbsearch <query> | /nzbsearch ubuntu | - |
| /searchtasks | - | /searchtasks <query> | /searchtasks ubuntu | - |
| /filtertasks | - | /filtertasks <status> | /filtertasks downloading | - |
| /history | - | /history [limit] | /history 10 | - |

## Automation

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /schedule | - | /schedule <time> <command> | /schedule 30m /mirror https://example.com/file.zip | - |
| /schedules | - | /schedules | /schedules | - |
| /unschedule | - | /unschedule <id> | /unschedule 3 | - |
| /rss | - | /rss <add|del|list> [args] | /rss add https://example.com/feed.xml | - |

## Settings

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /usetting | /us | /usetting | /usetting | - |
| /bsetting | /bs | /bsetting | /bsetting | Owner only |
| /settings | /prefs, /preferences | /settings | /settings | - |
| /viewtoggle | - | /viewtoggle | /viewtoggle | - |
| /setalerts | - | /setalerts | /setalerts | Owner only |
| /limit | - | /limit <number> | /limit 5 | Owner only |
| /limit_task | - | /limit_task <gid> <number> | /limit_task 1a2b3c 2 | Owner only |
| /category | - | /category <name> | /category movies | - |
| /categorize | - | /categorize <gid> <name> | /categorize 1a2b3c movies | - |

## Tools & Media

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /streamlink | /sl | /streamlink <file_id> | /streamlink AgACAg... | Reply to a file also works |
| /zip | - | /zip <path> [format] [level] | /zip /path/to/folder | - |
| /unzip | - | /unzip <archive_path> [password] | /unzip /path/to/file.zip | - |
| /zipinfo | - | /zipinfo <archive_path> | /zipinfo /path/to/file.zip | - |
| /mediainfo | - | /mediainfo <file_path> | /mediainfo /path/to/video.mkv | - |
| /thumbnail | - | /thumbnail <file_path> [timestamp] | /thumbnail /path/to/video.mkv 00:00:10 | - |
| /mstats | - | /mstats <file_path> | /mstats /path/to/video.mkv | - |
| /sel | - | /sel <gid> | /sel 1a2b3c | - |

## System & Monitoring

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /ping | - | /ping | /ping | - |
| /stats | - | /stats | /stats | - |
| /estats | - | /estats | /estats | - |
| /cstats | - | /cstats | /cstats | - |
| /speed | - | /speed | /speed | - |
| /rmon | - | /rmon | /rmon | - |
| /health | - | /health | /health | - |
| /psummary | - | /psummary | /psummary | - |

## Dashboards

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /dashboard | - | /dashboard | /dashboard | - |
| /webdash | - | /webdash | /webdash | - |
| /edash | - | /edash | /edash | - |
| /equick | - | /equick | /equick | - |
| /eanalytics | - | /eanalytics | /eanalytics | - |

## Admin

| Command | Shortcuts | Usage | Example | Notes |
| --- | --- | --- | --- | --- |
| /users | - | /users | /users | Owner only |
| /auth | - | /auth <user_id> | /auth 123456789 | Owner only |
| /unauth | - | /unauth <user_id> | /unauth 123456789 | Owner only |
| /addsudo | - | /addsudo <user_id> | /addsudo 123456789 | Owner only |
| /rmsudo | - | /rmsudo <user_id> | /rmsudo 123456789 | Owner only |
| /restart | - | /restart | /restart | Owner only |
| /log | - | /log [lines] | /log 100 | Owner only |
| /shell | - | /shell <command> | /shell ls -la | Owner only |
| /exec | - | /exec <python> | /exec print(1) | Owner only |
| /aexec | - | /aexec <python> | /aexec await asyncio.sleep(1) | Owner only |
| /clearlocals | - | /clearlocals | /clearlocals | Owner only |
