from ..telegram_helper.bot_commands import BotCommands
from ...core.telegram_manager import TgClient


def _cmd_list(cmd):
  return list(cmd) if isinstance(cmd, (list, tuple)) else [cmd]


def _cmd_primary(cmd):
  return _cmd_list(cmd)[0]


def _cmd_aliases(cmd):
  return _cmd_list(cmd)[1:]


def format_command(cmd):
  primary = _cmd_primary(cmd)
  return f"/{primary}"


def format_shortcuts(cmd):
  aliases = _cmd_aliases(cmd)
  if not aliases:
    return ""
  return ", ".join(f"/{alias}" for alias in aliases)


HELP_CATEGORIES = {
  "general": {
    "title": "General",
    "items": [
      {
        "name": "Start",
        "cmd": BotCommands.StartCommandList,
        "desc": "Start the bot",
        "usage": f"/{_cmd_primary(BotCommands.StartCommandList)}",
        "example": f"/{_cmd_primary(BotCommands.StartCommandList)}",
      },
      {
        "name": "Help",
        "cmd": BotCommands.HelpCommandList,
        "desc": "Open the help menu or search commands by keyword",
        "usage": f"/{_cmd_primary(BotCommands.HelpCommandList)} [keyword]",
        "example": f"/{_cmd_primary(BotCommands.HelpCommandList)} mirror",
      },
      {
        "name": "Command List",
        "cmd": BotCommands.CommandListCommand,
        "desc": "Show all commands and send a BotFather-ready command list",
        "usage": f"/{_cmd_primary(BotCommands.CommandListCommand)}",
        "example": f"/{_cmd_primary(BotCommands.CommandListCommand)}",
      },
    ],
  },
  "downloads": {
    "title": "Downloads & Uploads",
    "items": [
      {
        "name": "Mirror",
        "cmd": BotCommands.MirrorCommand,
        "desc": "Mirror links to cloud",
        "usage": f"/{_cmd_primary(BotCommands.MirrorCommand)} <link> [args]",
        "example": f"/{_cmd_primary(BotCommands.MirrorCommand)} https://example.com/file.zip",
      },
      {
        "name": "Leech",
        "cmd": BotCommands.LeechCommand,
        "desc": "Upload to Telegram",
        "usage": f"/{_cmd_primary(BotCommands.LeechCommand)} <link> [args]",
        "example": f"/{_cmd_primary(BotCommands.LeechCommand)} https://example.com/file.zip",
      },
      {
        "name": "Qbit Mirror",
        "cmd": BotCommands.QbMirrorCommand,
        "desc": "Torrents via qBittorrent",
        "usage": f"/{_cmd_primary(BotCommands.QbMirrorCommand)} <magnet|torrent>",
        "example": f"/{_cmd_primary(BotCommands.QbMirrorCommand)} magnet:?xt=urn:btih:...",
      },
      {
        "name": "Qbit Leech",
        "cmd": BotCommands.QbLeechCommand,
        "desc": "Leech torrents",
        "usage": f"/{_cmd_primary(BotCommands.QbLeechCommand)} <magnet|torrent>",
        "example": f"/{_cmd_primary(BotCommands.QbLeechCommand)} magnet:?xt=urn:btih:...",
      },
      {
        "name": "JDownloader Mirror",
        "cmd": BotCommands.JdMirrorCommand,
        "desc": "Mirror via JDownloader",
        "usage": f"/{_cmd_primary(BotCommands.JdMirrorCommand)} <link>",
        "example": f"/{_cmd_primary(BotCommands.JdMirrorCommand)} https://example.com/file.zip",
      },
      {
        "name": "JDownloader Leech",
        "cmd": BotCommands.JdLeechCommand,
        "desc": "Leech via JDownloader",
        "usage": f"/{_cmd_primary(BotCommands.JdLeechCommand)} <link>",
        "example": f"/{_cmd_primary(BotCommands.JdLeechCommand)} https://example.com/file.zip",
      },
      {
        "name": "YT-DLP Mirror",
        "cmd": BotCommands.YtdlCommand,
        "desc": "Video downloads",
        "usage": f"/{_cmd_primary(BotCommands.YtdlCommand)} <url> [options]",
        "example": f"/{_cmd_primary(BotCommands.YtdlCommand)} https://youtu.be/xxxxx",
      },
      {
        "name": "YT-DLP Leech",
        "cmd": BotCommands.YtdlLeechCommand,
        "desc": "Leech videos to Telegram",
        "usage": f"/{_cmd_primary(BotCommands.YtdlLeechCommand)} <url> [options]",
        "example": f"/{_cmd_primary(BotCommands.YtdlLeechCommand)} https://youtu.be/xxxxx",
      },
      {
        "name": "NZB Mirror",
        "cmd": BotCommands.NzbMirrorCommand,
        "desc": "Mirror NZB files",
        "usage": f"/{_cmd_primary(BotCommands.NzbMirrorCommand)} <nzb_url>",
        "example": f"/{_cmd_primary(BotCommands.NzbMirrorCommand)} https://example.com/file.nzb",
      },
      {
        "name": "NZB Leech",
        "cmd": BotCommands.NzbLeechCommand,
        "desc": "Leech NZB files",
        "usage": f"/{_cmd_primary(BotCommands.NzbLeechCommand)} <nzb_url>",
        "example": f"/{_cmd_primary(BotCommands.NzbLeechCommand)} https://example.com/file.nzb",
      },
    ],
  },
  "drive": {
    "title": "Drive & Rclone",
    "items": [
      {
        "name": "Clone",
        "cmd": BotCommands.CloneCommand,
        "desc": "Copy drive/rclone paths",
        "usage": f"/{_cmd_primary(BotCommands.CloneCommand)} <link|path>",
        "example": f"/{_cmd_primary(BotCommands.CloneCommand)} https://drive.google.com/...",
      },
      {
        "name": "Count",
        "cmd": BotCommands.CountCommand,
        "desc": "Count drive folder",
        "usage": f"/{_cmd_primary(BotCommands.CountCommand)} <link|path>",
        "example": f"/{_cmd_primary(BotCommands.CountCommand)} https://drive.google.com/...",
      },
      {
        "name": "Delete",
        "cmd": BotCommands.DeleteCommand,
        "desc": "Delete drive item",
        "usage": f"/{_cmd_primary(BotCommands.DeleteCommand)} <link|path>",
        "example": f"/{_cmd_primary(BotCommands.DeleteCommand)} https://drive.google.com/...",
      },
      {
        "name": "List",
        "cmd": BotCommands.ListCommand,
        "desc": "Search in drive",
        "usage": f"/{_cmd_primary(BotCommands.ListCommand)} <query>",
        "example": f"/{_cmd_primary(BotCommands.ListCommand)} ubuntu",
      },
    ],
  },
  "queue": {
    "title": "Queue & Status",
    "items": [
      {
        "name": "Status",
        "cmd": BotCommands.StatusCommandList,
        "desc": "Show task status",
        "usage": f"/{_cmd_primary(BotCommands.StatusCommandList)}",
        "example": f"/{_cmd_primary(BotCommands.StatusCommandList)}",
      },
      {
        "name": "Queue",
        "cmd": BotCommands.QueueCommandList,
        "desc": "Manage active tasks",
        "usage": f"/{_cmd_primary(BotCommands.QueueCommandList)}",
        "example": f"/{_cmd_primary(BotCommands.QueueCommandList)}",
      },
      {
        "name": "Pause",
        "cmd": BotCommands.PauseCommand,
        "desc": "Pause a task",
        "usage": f"/{_cmd_primary(BotCommands.PauseCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.PauseCommand)} 1a2b3c",
      },
      {
        "name": "Resume",
        "cmd": BotCommands.ResumeCommand,
        "desc": "Resume a task",
        "usage": f"/{_cmd_primary(BotCommands.ResumeCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.ResumeCommand)} 1a2b3c",
      },
      {
        "name": "Priority",
        "cmd": BotCommands.PriorityCommand,
        "desc": "Set task priority",
        "usage": f"/{_cmd_primary(BotCommands.PriorityCommand)} <gid> <level>",
        "example": f"/{_cmd_primary(BotCommands.PriorityCommand)} 1a2b3c 1",
      },
      {
        "name": "Pause All",
        "cmd": BotCommands.PauseAllCommand,
        "desc": "Pause all tasks",
        "usage": f"/{_cmd_primary(BotCommands.PauseAllCommand)}",
        "example": f"/{_cmd_primary(BotCommands.PauseAllCommand)}",
      },
      {
        "name": "Resume All",
        "cmd": BotCommands.ResumeAllCommand,
        "desc": "Resume all tasks",
        "usage": f"/{_cmd_primary(BotCommands.ResumeAllCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ResumeAllCommand)}",
      },
      {
        "name": "Cancel",
        "cmd": BotCommands.CancelTaskCommand,
        "desc": "Cancel a task",
        "usage": f"/{_cmd_primary(BotCommands.CancelTaskCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.CancelTaskCommand)} 1a2b3c",
      },
      {
        "name": "Cancel All",
        "cmd": BotCommands.CancelAllCommand,
        "desc": "Cancel all tasks",
        "usage": f"/{_cmd_primary(BotCommands.CancelAllCommand)}",
        "example": f"/{_cmd_primary(BotCommands.CancelAllCommand)}",
      },
      {
        "name": "Force Start",
        "cmd": BotCommands.ForceStartCommand,
        "desc": "Force start a queued task",
        "usage": f"/{_cmd_primary(BotCommands.ForceStartCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.ForceStartCommand)} 1a2b3c",
      },
      {
        "name": "Task Details",
        "cmd": BotCommands.TaskDetailsCommand,
        "desc": "Show task details",
        "usage": f"/{_cmd_primary(BotCommands.TaskDetailsCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.TaskDetailsCommand)} 1a2b3c",
      },
    ],
  },
  "search": {
    "title": "Search & History",
    "items": [
      {
        "name": "Search",
        "cmd": BotCommands.SearchCommand,
        "desc": "Search torrents",
        "usage": f"/{_cmd_primary(BotCommands.SearchCommand)} <query>",
        "example": f"/{_cmd_primary(BotCommands.SearchCommand)} linux iso",
      },
      {
        "name": "NZB Search",
        "cmd": BotCommands.NzbSearchCommand,
        "desc": "Search NZB files",
        "usage": f"/{_cmd_primary(BotCommands.NzbSearchCommand)} <query>",
        "example": f"/{_cmd_primary(BotCommands.NzbSearchCommand)} ubuntu",
      },
      {
        "name": "Task Search",
        "cmd": BotCommands.SearchTasksCommand,
        "desc": "Find tasks",
        "usage": f"/{_cmd_primary(BotCommands.SearchTasksCommand)} <query>",
        "example": f"/{_cmd_primary(BotCommands.SearchTasksCommand)} ubuntu",
      },
      {
        "name": "Filter Tasks",
        "cmd": BotCommands.FilterTasksCommand,
        "desc": "Filter by status",
        "usage": f"/{_cmd_primary(BotCommands.FilterTasksCommand)} <status>",
        "example": f"/{_cmd_primary(BotCommands.FilterTasksCommand)} downloading",
      },
      {
        "name": "History",
        "cmd": BotCommands.HistoryCommand,
        "desc": "Download history",
        "usage": f"/{_cmd_primary(BotCommands.HistoryCommand)} [limit]",
        "example": f"/{_cmd_primary(BotCommands.HistoryCommand)} 10",
      },
    ],
  },
  "automation": {
    "title": "Automation",
    "items": [
      {
        "name": "Schedule",
        "cmd": BotCommands.ScheduleCommand,
        "desc": "Schedule tasks",
        "usage": f"/{_cmd_primary(BotCommands.ScheduleCommand)} <time> <command>",
        "example": f"/{_cmd_primary(BotCommands.ScheduleCommand)} 30m /{_cmd_primary(BotCommands.MirrorCommand)} https://example.com/file.zip",
      },
      {
        "name": "Schedules",
        "cmd": BotCommands.SchedulesCommand,
        "desc": "List schedules",
        "usage": f"/{_cmd_primary(BotCommands.SchedulesCommand)}",
        "example": f"/{_cmd_primary(BotCommands.SchedulesCommand)}",
      },
      {
        "name": "Unschedule",
        "cmd": BotCommands.UnscheduleCommand,
        "desc": "Remove a schedule",
        "usage": f"/{_cmd_primary(BotCommands.UnscheduleCommand)} <id>",
        "example": f"/{_cmd_primary(BotCommands.UnscheduleCommand)} 3",
      },
      {
        "name": "RSS",
        "cmd": BotCommands.RssCommand,
        "desc": "Manage RSS feeds",
        "usage": f"/{_cmd_primary(BotCommands.RssCommand)} <add|del|list> [args]",
        "example": f"/{_cmd_primary(BotCommands.RssCommand)} add https://example.com/feed.xml",
      },
    ],
  },
  "settings": {
    "title": "Settings",
    "items": [
      {
        "name": "User Settings",
        "cmd": BotCommands.UserSetCommand,
        "desc": "Per-user preferences",
        "usage": f"/{_cmd_primary(BotCommands.UserSetCommand)}",
        "example": f"/{_cmd_primary(BotCommands.UserSetCommand)}",
      },
      {
        "name": "Bot Settings",
        "cmd": BotCommands.BotSetCommand,
        "desc": "Owner settings",
        "usage": f"/{_cmd_primary(BotCommands.BotSetCommand)}",
        "example": f"/{_cmd_primary(BotCommands.BotSetCommand)}",
      },
      {
        "name": "UI Settings",
        "cmd": BotCommands.SettingsUICommandList,
        "desc": "UI & alerts",
        "usage": f"/{_cmd_primary(BotCommands.SettingsUICommandList)}",
        "example": f"/{_cmd_primary(BotCommands.SettingsUICommandList)}",
      },
      {
        "name": "View Toggle",
        "cmd": BotCommands.ViewToggleCommand,
        "desc": "Toggle view mode",
        "usage": f"/{_cmd_primary(BotCommands.ViewToggleCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ViewToggleCommand)}",
      },
      {
        "name": "Set Alerts",
        "cmd": BotCommands.SetAlertsCommand,
        "desc": "Configure alert preferences",
        "usage": f"/{_cmd_primary(BotCommands.SetAlertsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.SetAlertsCommand)}",
      },
      {
        "name": "Limit",
        "cmd": BotCommands.LimitCommand,
        "desc": "Set global task limit",
        "usage": f"/{_cmd_primary(BotCommands.LimitCommand)} <number>",
        "example": f"/{_cmd_primary(BotCommands.LimitCommand)} 5",
      },
      {
        "name": "Limit Task",
        "cmd": BotCommands.LimitTaskCommand,
        "desc": "Set per-task limit",
        "usage": f"/{_cmd_primary(BotCommands.LimitTaskCommand)} <gid> <number>",
        "example": f"/{_cmd_primary(BotCommands.LimitTaskCommand)} 1a2b3c 2",
      },
      {
        "name": "Category",
        "cmd": BotCommands.CategoryCommand,
        "desc": "Manage task categories",
        "usage": f"/{_cmd_primary(BotCommands.CategoryCommand)} <name>",
        "example": f"/{_cmd_primary(BotCommands.CategoryCommand)} movies",
      },
      {
        "name": "Categorize",
        "cmd": BotCommands.CategorizeCommand,
        "desc": "Assign category to a task",
        "usage": f"/{_cmd_primary(BotCommands.CategorizeCommand)} <gid> <name>",
        "example": f"/{_cmd_primary(BotCommands.CategorizeCommand)} 1a2b3c movies",
      },
    ],
  },
  "tools": {
    "title": "Tools & Media",
    "items": [
      {
        "name": "Stream Link",
        "cmd": BotCommands.StreamLinkCommand,
        "desc": "Generate HTTP download link",
        "usage": f"/{_cmd_primary(BotCommands.StreamLinkCommand)} <file_id>",
        "example": f"/{_cmd_primary(BotCommands.StreamLinkCommand)} AgACAg...",
      },
      {
        "name": "Bypass URL",
        "cmd": BotCommands.BypassCommand,
        "desc": "Expand short/redirect URLs",
        "usage": f"/{_cmd_primary(BotCommands.BypassCommand)} <url>",
        "example": f"/{_cmd_primary(BotCommands.BypassCommand)} https://bit.ly/example",
      },
      {
        "name": "Zip",
        "cmd": BotCommands.ZipCommand,
        "desc": "Create archives",
        "usage": f"/{_cmd_primary(BotCommands.ZipCommand)} <path> [format] [level]",
        "example": f"/{_cmd_primary(BotCommands.ZipCommand)} /path/to/folder",
      },
      {
        "name": "Unzip",
        "cmd": BotCommands.UnzipCommand,
        "desc": "Extract archives",
        "usage": f"/{_cmd_primary(BotCommands.UnzipCommand)} <archive_path> [password]",
        "example": f"/{_cmd_primary(BotCommands.UnzipCommand)} /path/to/file.zip",
      },
      {
        "name": "Zip Info",
        "cmd": BotCommands.ZipInfoCommand,
        "desc": "Show archive contents",
        "usage": f"/{_cmd_primary(BotCommands.ZipInfoCommand)} <archive_path>",
        "example": f"/{_cmd_primary(BotCommands.ZipInfoCommand)} /path/to/file.zip",
      },
      {
        "name": "Media Info",
        "cmd": BotCommands.MediaInfoCommand,
        "desc": "Show media information",
        "usage": f"/{_cmd_primary(BotCommands.MediaInfoCommand)} <file_path>",
        "example": f"/{_cmd_primary(BotCommands.MediaInfoCommand)} /path/to/video.mkv",
      },
      {
        "name": "Thumbnail",
        "cmd": BotCommands.ThumbnailCommand,
        "desc": "Extract a video thumbnail",
        "usage": f"/{_cmd_primary(BotCommands.ThumbnailCommand)} <file_path> [timestamp]",
        "example": f"/{_cmd_primary(BotCommands.ThumbnailCommand)} /path/to/video.mkv 00:00:10",
      },
      {
        "name": "Media Stats",
        "cmd": BotCommands.MStatsCommand,
        "desc": "Quick media stats",
        "usage": f"/{_cmd_primary(BotCommands.MStatsCommand)} <file_path>",
        "example": f"/{_cmd_primary(BotCommands.MStatsCommand)} /path/to/video.mkv",
      },
      {
        "name": "Select Files",
        "cmd": BotCommands.SelectCommand,
        "desc": "Select files for a task",
        "usage": f"/{_cmd_primary(BotCommands.SelectCommand)} <gid>",
        "example": f"/{_cmd_primary(BotCommands.SelectCommand)} 1a2b3c",
      },
    ],
  },
  "system": {
    "title": "System & Monitoring",
    "items": [
      {
        "name": "Ping",
        "cmd": BotCommands.PingCommand,
        "desc": "Check bot latency",
        "usage": f"/{_cmd_primary(BotCommands.PingCommand)}",
        "example": f"/{_cmd_primary(BotCommands.PingCommand)}",
      },
      {
        "name": "Stats",
        "cmd": BotCommands.StatsCommand,
        "desc": "Server stats",
        "usage": f"/{_cmd_primary(BotCommands.StatsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.StatsCommand)}",
      },
      {
        "name": "Enhanced Stats",
        "cmd": BotCommands.EnhancedStatsCommand,
        "desc": "Detailed system stats",
        "usage": f"/{_cmd_primary(BotCommands.EnhancedStatsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.EnhancedStatsCommand)}",
      },
      {
        "name": "Comparison Stats",
        "cmd": BotCommands.ComparisonStatsCommand,
        "desc": "Compare system stats",
        "usage": f"/{_cmd_primary(BotCommands.ComparisonStatsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ComparisonStatsCommand)}",
      },
      {
        "name": "Speedtest",
        "cmd": BotCommands.SpeedCommand,
        "desc": "Network speed",
        "usage": f"/{_cmd_primary(BotCommands.SpeedCommand)}",
        "example": f"/{_cmd_primary(BotCommands.SpeedCommand)}",
      },
      {
        "name": "Resource Monitor",
        "cmd": BotCommands.ResourceMonitorCommand,
        "desc": "Live resource monitor",
        "usage": f"/{_cmd_primary(BotCommands.ResourceMonitorCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ResourceMonitorCommand)}",
      },
      {
        "name": "System Health",
        "cmd": BotCommands.SystemHealthCommand,
        "desc": "Health report",
        "usage": f"/{_cmd_primary(BotCommands.SystemHealthCommand)}",
        "example": f"/{_cmd_primary(BotCommands.SystemHealthCommand)}",
      },
      {
        "name": "Progress Summary",
        "cmd": BotCommands.ProgressSummaryCommand,
        "desc": "Summary of running tasks",
        "usage": f"/{_cmd_primary(BotCommands.ProgressSummaryCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ProgressSummaryCommand)}",
      },
    ],
  },
  "dashboard": {
    "title": "Dashboards",
    "items": [
      {
        "name": "Dashboard",
        "cmd": BotCommands.DashboardCommand,
        "desc": "System dashboard",
        "usage": f"/{_cmd_primary(BotCommands.DashboardCommand)}",
        "example": f"/{_cmd_primary(BotCommands.DashboardCommand)}",
      },
      {
        "name": "Web Dashboard",
        "cmd": BotCommands.WebDashboardCommand,
        "desc": "Web dashboard link",
        "usage": f"/{_cmd_primary(BotCommands.WebDashboardCommand)}",
        "example": f"/{_cmd_primary(BotCommands.WebDashboardCommand)}",
      },
      {
        "name": "Enhanced Dashboard",
        "cmd": BotCommands.EnhancedDashCommand,
        "desc": "Enhanced dashboard",
        "usage": f"/{_cmd_primary(BotCommands.EnhancedDashCommand)}",
        "example": f"/{_cmd_primary(BotCommands.EnhancedDashCommand)}",
      },
      {
        "name": "Quick Status",
        "cmd": BotCommands.EnhancedQuickCommand,
        "desc": "Quick overview",
        "usage": f"/{_cmd_primary(BotCommands.EnhancedQuickCommand)}",
        "example": f"/{_cmd_primary(BotCommands.EnhancedQuickCommand)}",
      },
      {
        "name": "Analytics",
        "cmd": BotCommands.EnhancedAnalyticsCommand,
        "desc": "Task analytics",
        "usage": f"/{_cmd_primary(BotCommands.EnhancedAnalyticsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.EnhancedAnalyticsCommand)}",
      },
    ],
  },
  "admin": {
    "title": "Admin",
    "items": [
      {
        "name": "Users",
        "cmd": BotCommands.UsersCommand,
        "desc": "List users",
        "usage": f"/{_cmd_primary(BotCommands.UsersCommand)}",
        "example": f"/{_cmd_primary(BotCommands.UsersCommand)}",
      },
      {
        "name": "Authorize",
        "cmd": BotCommands.AuthorizeCommand,
        "desc": "Authorize users",
        "usage": f"/{_cmd_primary(BotCommands.AuthorizeCommand)} <user_id>",
        "example": f"/{_cmd_primary(BotCommands.AuthorizeCommand)} 123456789",
      },
      {
        "name": "Unauthorize",
        "cmd": BotCommands.UnAuthorizeCommand,
        "desc": "Remove access",
        "usage": f"/{_cmd_primary(BotCommands.UnAuthorizeCommand)} <user_id>",
        "example": f"/{_cmd_primary(BotCommands.UnAuthorizeCommand)} 123456789",
      },
      {
        "name": "Add Sudo",
        "cmd": BotCommands.AddSudoCommand,
        "desc": "Add sudo",
        "usage": f"/{_cmd_primary(BotCommands.AddSudoCommand)} <user_id>",
        "example": f"/{_cmd_primary(BotCommands.AddSudoCommand)} 123456789",
      },
      {
        "name": "Remove Sudo",
        "cmd": BotCommands.RmSudoCommand,
        "desc": "Remove sudo",
        "usage": f"/{_cmd_primary(BotCommands.RmSudoCommand)} <user_id>",
        "example": f"/{_cmd_primary(BotCommands.RmSudoCommand)} 123456789",
      },
      {
        "name": "Restart",
        "cmd": BotCommands.RestartCommand,
        "desc": "Restart bot",
        "usage": f"/{_cmd_primary(BotCommands.RestartCommand)}",
        "example": f"/{_cmd_primary(BotCommands.RestartCommand)}",
      },
      {
        "name": "Log",
        "cmd": BotCommands.LogCommand,
        "desc": "View logs",
        "usage": f"/{_cmd_primary(BotCommands.LogCommand)} [lines]",
        "example": f"/{_cmd_primary(BotCommands.LogCommand)} 100",
      },
      {
        "name": "Shell",
        "cmd": BotCommands.ShellCommand,
        "desc": "Run shell commands",
        "usage": f"/{_cmd_primary(BotCommands.ShellCommand)} <command>",
        "example": f"/{_cmd_primary(BotCommands.ShellCommand)} ls -la",
      },
      {
        "name": "Exec",
        "cmd": BotCommands.ExecCommand,
        "desc": "Run Python code",
        "usage": f"/{_cmd_primary(BotCommands.ExecCommand)} <python>",
        "example": f"/{_cmd_primary(BotCommands.ExecCommand)} print(1)",
      },
      {
        "name": "Async Exec",
        "cmd": BotCommands.AExecCommand,
        "desc": "Run async Python code",
        "usage": f"/{_cmd_primary(BotCommands.AExecCommand)} <python>",
        "example": f"/{_cmd_primary(BotCommands.AExecCommand)} await asyncio.sleep(1)",
      },
      {
        "name": "Clear Locals",
        "cmd": BotCommands.ClearLocalsCommand,
        "desc": "Clear exec locals",
        "usage": f"/{_cmd_primary(BotCommands.ClearLocalsCommand)}",
        "example": f"/{_cmd_primary(BotCommands.ClearLocalsCommand)}",
      },
    ],
  },
}


HELP_CATEGORY_ORDER = [
  "general",
  "downloads",
  "drive",
  "queue",
  "search",
  "automation",
  "settings",
  "tools",
  "system",
  "dashboard",
  "admin",
]


HELP_CATEGORY_ALIASES = {
  "general": "general",
  "start": "general",
  "help": "general",
  "downloads": "downloads",
  "download": "downloads",
  "uploads": "downloads",
  "drive": "drive",
  "rclone": "drive",
  "queue": "queue",
  "status": "queue",
  "search": "search",
  "history": "search",
  "automation": "automation",
  "schedule": "automation",
  "rss": "automation",
  "settings": "settings",
  "prefs": "settings",
  "tools": "tools",
  "media": "tools",
  "system": "system",
  "dashboard": "dashboard",
  "admin": "admin",
}


def build_help_home_text():
  return (
    "<b>📘 Command Center</b>\n"
    "Pick a category or search.\n\n"
    "<b>Quick Start</b>\n"
    f"1) Mirror a link: <code>/{_cmd_primary(BotCommands.MirrorCommand)} [link]</code>\n"
    f"2) Leech to Telegram: <code>/{_cmd_primary(BotCommands.LeechCommand)} [link]</code>\n"
    f"3) View tasks: <code>/{_cmd_primary(BotCommands.StatusCommandList)}</code>\n\n"
    "Tip: Use /help <keyword> to search commands, and shortcuts like /dl or /ul for faster commands."
  )


def build_help_category_text(category_key):
  cat = HELP_CATEGORIES.get(category_key)
  if not cat:
    return "❌ Category not found."
  lines = [f"<b>📂 {cat['title']}</b>", "<i>Tap a command to copy, or use shortcuts.</i>"]
  for item in cat["items"]:
    cmd_text = format_command(item["cmd"])
    extras = []
    usage = item.get("usage")
    if usage:
      extras.append(f"<b>Usage</b>: <code>{usage}</code>")
    shortcuts = format_shortcuts(item["cmd"])
    if shortcuts:
      extras.append(f"<b>Shortcuts</b>: <code>{shortcuts}</code>")
    example = item.get("example")
    if example:
      extras.append(f"<b>Example</b>: <code>{example}</code>")
    if extras:
      lines.append(f"• <b>{cmd_text}</b> — {item['desc']}")
      lines.extend([f"  {line}" for line in extras])
    else:
      lines.append(f"• <b>{cmd_text}</b> — {item['desc']}")
  return "\n".join(lines)


def search_help(term):
  needle = term.lower().strip()
  if not needle:
    return "❌ Please enter a search keyword."
  matches = []
  for cat_key in HELP_CATEGORY_ORDER:
    cat = HELP_CATEGORIES[cat_key]
    for item in cat["items"]:
      cmd_text = " ".join(_cmd_list(item["cmd"])).lower()
      hay = f"{item['name']} {item['desc']} {cmd_text}".lower()
      if needle in hay:
        matches.append((cat["title"], item))
  if not matches:
    return f"❌ No commands matched <code>{term}</code>."
  lines = [f"<b>🔎 Results for:</b> <code>{term}</code>"]
  for cat_title, item in matches[:12]:
    extras = []
    usage = item.get("usage")
    if usage:
      extras.append(f"<b>Usage</b>: <code>{usage}</code>")
    shortcuts = format_shortcuts(item["cmd"])
    if shortcuts:
      extras.append(f"<b>Shortcuts</b>: <code>{shortcuts}</code>")
    lines.append(f"• <b>{cat_title}</b>: <b>{format_command(item['cmd'])}</b> — {item['desc']}")
    for extra in extras:
      lines.append(f"  {extra}")
  return "\n".join(lines)

mirror = """<b>Send link along with command line or </b>

/cmd link

<b>By replying to link/file</b>:

/cmd -n new name -e -up upload destination

<b>NOTE:</b>
1. Commands that start with <b>qb</b> are ONLY for torrents."""

yt = """<b>Send link along with command line</b>:

/cmd link
<b>By replying to link</b>:
/cmd -n new name -z password -opt x:y|x1:y1

Check here all supported <a href='https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md'>SITES</a>
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L212'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options."""

clone = """Send Gdrive|Gdot|Filepress|Filebee|Appdrive|Gdflix link or rclone path along with command or by replying to the link/rc_path by command.
Use -sync to use sync method in rclone. Example: /cmd rcl/rclone_path -up rcl/rclone_path/rc -sync"""

new_name = """<b>New Name</b>: -n

/cmd link -n new name
Note: Doesn't work with torrents"""

multi_link = """<b>Multi links only by replying to first link/file</b>: -i

/cmd -i 10(number of links/files)"""

same_dir = """<b>Move file(s)/folder(s) to new folder</b>: -m

You can use this arg also to move multiple links/torrents contents to the same directory, so all links will be uploaded together as one task

/cmd link -m new folder (only one link inside new folder)
/cmd -i 10(number of links/files) -m folder name (all links contents in one folder)
/cmd -b -m folder name (reply to batch of message/file(each link on new line))

While using bulk you can also use this arg with different folder name along with the links in message or file batch
Example:
link1 -m folder1
link2 -m folder1
link3 -m folder2
link4 -m folder2
link5 -m folder3
link6
so link1 and link2 content will be uploaded from same folder which is folder1
link3 and link4 content will be uploaded from same folder also which is folder2
link5 will uploaded alone inside new folder named folder3
link6 will get uploaded normally alone
"""

thumb = """<b>Thumbnail for current task</b>: -t

/cmd link -t tg-message-link (doc or photo) or none (file without thumb)"""

split_size = """<b>Split size for current task</b>: -sp

/cmd link -sp (500mb or 2gb or 4000000000)
Note: Only mb and gb are supported or write in bytes without unit!"""

upload = """<b>Upload Destination</b>: -up

/cmd link -up rcl/gdl (rcl: to select rclone config, remote & path | gdl: To select token.pickle, gdrive id) using buttons
You can directly add the upload path: -up remote:dir/subdir or -up Gdrive_id or -up id/username (telegram) or -up id/username|topic_id (telegram)
If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.

If you want to add path or gdrive manually from your config/token (UPLOADED FROM USETTING) add mrcc: for rclone and mtp: before the path/gdrive_id without space.
/cmd link -up mrcc:main:dump or -up mtp:gdrive_id <strong>or you can simply edit upload using owner/user token/config from usetting without adding mtp: or mrcc: before the upload path/id</strong>

To add leech destination:
-up id/@username/pm
-up b:id/@username/pm (b: means leech by bot) (id or username of the chat or write pm means private message so bot will send the files in private to you)
when you should use b:(leech by bot)? When your default settings is leech by user and you want to leech by bot for specific task.
-up u:id/@username(u: means leech by user) This incase OWNER added USER_STRING_SESSION.
-up h:id/@username(hybrid leech) h: to upload files by bot and user based on file size.
-up id/@username|topic_id(leech in specific chat and topic) add | without space and write topic id after chat id or username.

In case you want to specify whether using token.pickle or service accounts you can add tp:gdrive_id (using token.pickle) or sa:gdrive_id (using service accounts) or mtp:gdrive_id (using token.pickle uploaded from usetting).
DEFAULT_UPLOAD doesn't affect on leech cmds.
"""

user_download = """<b>User Download</b>: link

/cmd tp:link to download using owner token.pickle incase service account enabled.
/cmd sa:link to download using service account incase service account disabled.
/cmd tp:gdrive_id to download using token.pickle and file_id incase service account enabled.
/cmd sa:gdrive_id to download using service account and file_id incase service account disabled.
/cmd mtp:gdrive_id or mtp:link to download using user token.pickle uploaded from usetting
/cmd mrcc:remote:path to download using user rclone config uploaded from usetting
you can simply edit upload using owner/user token/config from usetting without adding mtp: or mrcc: before the path/id"""

rcf = """<b>Rclone Flags</b>: -rcf

/cmd link|path|rcl -up path|rcl -rcf --buffer-size:8M|--drive-starred-only|key|key:value
This will override all other flags except --exclude
Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>."""

bulk = """<b>Bulk Download</b>: -b

Bulk can be used only by replying to text message or text file contains links separated by new line.
Example:
link1 -n new name -up remote1:path1 -rcf |key:value|key:value
link2 -z -n new name -up remote2:path2
link3 -e -n new name -up remote2:path2
Reply to this example by this cmd -> /cmd -b(bulk)

Note: Any arg along with the cmd will be setted to all links
/cmd -b -up remote: -z -m folder name (all links contents in one zipped folder uploaded to one destination)
so you can't set different upload destinations along with link incase you have added -m along with cmd
You can set start and end of the links from the bulk like seed, with -b start:end or only end by -b :end or only start by -b start.
The default start is from zero(first link) to inf."""

rlone_dl = """<b>Rclone Download</b>:

Treat rclone paths exactly like links
/cmd main:dump/ubuntu.iso or rcl(To select config, remote and path)
Users can add their own rclone from user settings
If you want to add path manually from your config add mrcc: before the path without space
/cmd mrcc:main:dump/ubuntu.iso
You can simply edit using owner/user config from usetting without adding mrcc: before the path"""

extract_zip = """<b>Extract/Zip</b>: -e -z

/cmd link -e password (extract password protected)
/cmd link -z password (zip password protected)
/cmd link -z password -e (extract and zip password protected)
Note: When both extract and zip added with cmd it will extract first and then zip, so always extract first"""

join = """<b>Join Splitted Files</b>: -j

This option will only work before extract and zip, so mostly it will be used with -m argument (samedir)
By Reply:
/cmd -i 3 -j -m folder name
/cmd -b -j -m folder name
if u have link(folder) have splitted files:
/cmd link -j"""

tg_links = """<b>TG Links</b>:

Treat links like any direct link
Some links need user access so you must add USER_SESSION_STRING for it.
Three types of links:
Public: https://t.me/channel_name/message_id
Private: tg://openmessage?user_id=xxxxxx&message_id=xxxxx
Super: https://t.me/c/channel_id/message_id
Range: https://t.me/channel_name/first_message_id-last_message_id
Range Example: tg://openmessage?user_id=xxxxxx&message_id=555-560 or https://t.me/channel_name/100-150
Note: Range link will work only by replying cmd to it"""

sample_video = """<b>Sample Video</b>: -sv

Create sample video for one video or folder of videos.
/cmd -sv (it will take the default values which 60sec sample duration and part duration is 4sec).
You can control those values. Example: /cmd -sv 70:5(sample-duration:part-duration) or /cmd -sv :5 or /cmd -sv 70."""

screenshot = """<b>ScreenShots</b>: -ss

Create screenshots for one video or folder of videos.
/cmd -ss (it will take the default values which is 10 photos).
You can control this value. Example: /cmd -ss 6."""

seed = """<b>Bittorrent seed</b>: -d

/cmd link -d ratio:seed_time or by replying to file/link
To specify ratio and seed time add -d ratio:time.
Example: -d 0.7:10 (ratio and time) or -d 0.7 (only ratio) or -d :10 (only time) where time in minutes"""

zip_arg = """<b>Zip</b>: -z password

/cmd link -z (zip)
/cmd link -z password (zip password protected)"""

qual = """<b>Quality Buttons</b>: -s

In case default quality added from yt-dlp options using format option and you need to select quality for specific link or links with multi links feature.
/cmd link -s"""

yt_opt = """<b>Options</b>: -opt

/cmd link -opt {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}

Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options."""

convert_media = """<b>Convert Media</b>: -ca -cv
/cmd link -ca mp3 -cv mp4 (convert all audios to mp3 and all videos to mp4)
/cmd link -ca mp3 (convert all audios to mp3)
/cmd link -cv mp4 (convert all videos to mp4)
/cmd link -ca mp3 + flac ogg (convert only flac and ogg audios to mp3)
/cmd link -cv mkv - webm flv (convert all videos to mp4 except webm and flv)"""

force_start = """<b>Force Start</b>: -f -fd -fu
/cmd link -f (force download and upload)
/cmd link -fd (force download only)
/cmd link -fu (force upload directly after download finish)"""

gdrive = """<b>Gdrive</b>: link
If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
/cmd gdriveLink or gdl or gdriveId -up gdl or gdriveId or gd
/cmd tp:gdriveLink or tp:gdriveId -up tp:gdriveId or gdl or gd (to use token.pickle if service account enabled)
/cmd sa:gdriveLink or sa:gdriveId -p sa:gdriveId or gdl or gd (to use service account if service account disabled)
/cmd mtp:gdriveLink or mtp:gdriveId -up mtp:gdriveId or gdl or gd(if you have added upload gdriveId from usetting) (to use user token.pickle that uploaded by usetting)
You can simply edit using owner/user token from usetting without adding mtp: before the id"""

rclone_cl = """<b>Rclone</b>: path
If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.
/cmd rcl/rclone_path -up rcl/rclone_path/rc -rcf flagkey:flagvalue|flagkey|flagkey:flagvalue
/cmd rcl or rclone_path -up rclone_path or rc or rcl
/cmd mrcc:rclone_path -up rcl or rc(if you have add rclone path from usetting) (to use user config)
You can simply edit using owner/user config from usetting without adding mrcc: before the path"""

name_sub = r"""<b>Name Substitution</b>: -ns
/cmd link -ns script/code/s | mirror/leech | tea/ /s | clone | cpu/ | \[mltb\]/mltb | \\text\\/text/s
This will affect on all files. Format: wordToReplace/wordToReplaceWith/sensitiveCase
Word Subtitions. You can add pattern instead of normal text. Timeout: 60 sec
NOTE: You must add \ before any character, those are the characters: \^$.|?*+()[]{}-
1. script will get replaced by code with sensitive case
2. mirror will get replaced by leech
4. tea will get replaced by space with sensitive case
5. clone will get removed
6. cpu will get replaced by space
7. [mltb] will get replaced by mltb
8. \text\ will get replaced by text with sensitive case
"""

transmission = """<b>Tg transmission</b>: -hl -ut -bt
/cmd link -hl (leech by user and bot session with respect to size) (Hybrid Leech)
/cmd link -bt (leech by bot session)
/cmd link -ut (leech by user)"""

thumbnail_layout = """Thumbnail Layout: -tl
/cmd link -tl 3x3 (widthxheight) 3 photos in row and 3 photos in column"""

leech_as = """<b>Leech as</b>: -doc -med
/cmd link -doc (Leech as document)
/cmd link -med (Leech as media)"""

ffmpeg_cmds = """<b>FFmpeg Commands</b>: -ff
list of lists of ffmpeg commands. You can set multiple ffmpeg commands for all files before upload. Don't write ffmpeg at beginning, start directly with the arguments.
Notes:
1. Add <code>-del</code> to the list(s) which you want from the bot to delete the original files after command run complete!
3. To execute one of pre-added lists in bot like: ({"subtitle": ["-i mltb.mkv -c copy -c:s srt mltb.mkv"]}), you must use -ff subtitle (list key)
Examples: ["-i mltb.mkv -c copy -c:s srt mltb.mkv", "-i mltb.video -c copy -c:s srt mltb", "-i mltb.m4a -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb.audio -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb -map 0:a -c copy mltb.mka -map 0:s -c copy mltb.srt", "-i mltb -i tg://openmessage?user_id=5272663208&message_id=322801 -filter_complex 'overlay=W-w-10:H-h-10' -c:a copy mltb"]
Here I will explain how to use mltb.* which is reference to files you want to work on.
1. First cmd: the input is mltb.mkv so this cmd will work only on mkv videos and the output is mltb.mkv also so all outputs is mkv. -del will delete the original media after complete run of the cmd.
2. Second cmd: the input is mltb.video so this cmd will work on all videos and the output is only mltb so the extension is same as input files.
3. Third cmd: the input in mltb.m4a so this cmd will work only on m4a audios and the output is mltb.mp3 so the output extension is mp3.
4. Fourth cmd: the input is mltb.audio so this cmd will work on all audios and the output is mltb.mp3 so the output extension is mp3.
5. Fifth cmd: You can add telegram link for small size input like photo to set watermark"""

YT_HELP_DICT = {
    "main": yt,
    "New-Name": f"{new_name}\nNote: Don't add file extension",
    "Zip": zip_arg,
    "Quality": qual,
    "Options": yt_opt,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
    "Convert-Media": convert_media,
    "Force-Start": force_start,
    "Name-Substitute": name_sub,
    "TG-Transmission": transmission,
    "Thumb-Layout": thumbnail_layout,
    "Leech-Type": leech_as,
    "FFmpeg-Cmds": ffmpeg_cmds,
}

MIRROR_HELP_DICT = {
    "main": mirror,
    "New-Name": new_name,
    "DL-Auth": "<b>Direct link authorization</b>: -au -ap\n\n/cmd link -au username -ap password",
    "Headers": "<b>Direct link custom headers</b>: -h\n\n/cmd link -h key:value|key1:value1",
    "Extract/Zip": extract_zip,
    "Select-Files": "<b>Bittorrent/JDownloader/Sabnzbd File Selection</b>: -s\n\n/cmd link -s or by replying to file/link",
    "Torrent-Seed": seed,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Join": join,
    "Rclone-DL": rlone_dl,
    "Tg-Links": tg_links,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
    "Convert-Media": convert_media,
    "Force-Start": force_start,
    "User-Download": user_download,
    "Name-Substitute": name_sub,
    "TG-Transmission": transmission,
    "Thumb-Layout": thumbnail_layout,
    "Leech-Type": leech_as,
    "FFmpeg-Cmds": ffmpeg_cmds,
}

CLONE_HELP_DICT = {
    "main": clone,
    "Multi-Link": multi_link,
    "Bulk": bulk,
    "Gdrive": gdrive,
    "Rclone": rclone_cl,
}

RSS_HELP_MESSAGE = """
Use this format to add feed url:
Title1 link (required)
Title2 link -c cmd -inf xx -exf xx
Title3 link -c cmd -d ratio:time -z password

-c command -up mrcc:remote:path/subdir -rcf --buffer-size:8M|key|key:value
-inf For included words filter.
-exf For excluded words filter.
-stv true or false (sensitive filter)

Example: Title https://www.rss-url.com -inf 1080 or 720 or 144p|mkv or mp4|hevc -exf flv or web|xxx
This filter will parse links that its titles contain `(1080 or 720 or 144p) and (mkv or mp4) and hevc` and doesn't contain (flv or web) and xxx words. You can add whatever you want.

Another example: -inf  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contain ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080 to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without spaces after it.

Filter Notes:
1. | means and.
2. Add `or` between similar keys, you can add it between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web).
3. You can add `or` and `|` as much as you want.
4. Take a look at the title if it has a static special character after or before the qualities or extensions or whatever and use them in the filter to avoid wrong match.
Timeout: 60 sec.
"""

PASSWORD_ERROR_MESSAGE = """
<b>This link requires a password!</b>
- Insert <b>::</b> after the link and write the password after the sign.

<b>Example:</b> link::my password
"""

user_settings_text = {
    "LEECH_SPLIT_SIZE": f"Send Leech split size in bytes or use gb or mb. Example: 40000000 or 2.5gb or 1000mb. IS_PREMIUM_USER: {TgClient.IS_PREMIUM_USER}. Timeout: 60 sec",
    "LEECH_DUMP_CHAT": """"Send leech destination ID/USERNAME/PM. 
* b:id/@username/pm (b: means leech by bot) (id or username of the chat or write pm means private message so bot will send the files in private to you) when you should use b:(leech by bot)? When your default settings is leech by user and you want to leech by bot for specific task.
* u:id/@username(u: means leech by user) This incase OWNER added USER_STRING_SESSION.
* h:id/@username(hybrid leech) h: to upload files by bot and user based on file size.
* id/@username|topic_id(leech in specific chat and topic) add | without space and write topic id after chat id or username. Timeout: 60 sec""",
    "LEECH_FILENAME_PREFIX": r"Send Leech Filename Prefix. You can add HTML tags. Example: <code>@mychannel</code>. Timeout: 60 sec",
    "THUMBNAIL_LAYOUT": "Send thumbnail layout (widthxheight, 2x2, 3x3, 2x4, 4x4, ...). Example: 3x3. Timeout: 60 sec",
    "RCLONE_PATH": "Send Rclone Path. If you want to use your rclone config edit using owner/user config from usetting or add mrcc: before rclone path. Example mrcc:remote:folder. Timeout: 60 sec",
    "RCLONE_FLAGS": "key:value|key|key|key:value . Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>\nEx: --buffer-size:8M|--drive-starred-only",
    "GDRIVE_ID": "Send Gdrive ID. If you want to use your token.pickle edit using owner/user token from usetting or add mtp: before the id. Example: mtp:F435RGGRDXXXXXX . Timeout: 60 sec",
    "INDEX_URL": "Send Index URL. Timeout: 60 sec",
    "UPLOAD_PATHS": "Send Dict of keys that have path values. Example: {'path 1': 'remote:rclonefolder', 'path 2': 'gdrive1 id', 'path 3': 'tg chat id', 'path 4': 'mrcc:remote:', 'path 5': b:@username} . Timeout: 60 sec",
    "EXCLUDED_EXTENSIONS": "Send excluded extensions separated by space without dot at beginning. Timeout: 60 sec",
    "INCLUDED_EXTENSIONS": "Send included extensions separated by space without dot at beginning. Timeout: 60 sec",
    "NAME_SUBSTITUTE": r"""Word Subtitions. You can add pattern instead of normal text. Timeout: 60 sec
NOTE: You must add \ before any character, those are the characters: \^$.|?*+()[]{}-
Example: script/code/s | mirror/leech | tea/ /s | clone | cpu/ | \[mltb\]/mltb | \\text\\/text/s
1. script will get replaced by code with sensitive case
2. mirror will get replaced by leech
4. tea will get replaced by space with sensitive case
5. clone will get removed
6. cpu will get replaced by space
7. [mltb] will get replaced by mltb
8. \text\ will get replaced by text with sensitive case
""",
    "YT_DLP_OPTIONS": """Send dict of YT-DLP Options. Timeout: 60 sec
Format: {key: value, key: value, key: value}.
Example: {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.""",
    "FFMPEG_CMDS": """Dict of list values of ffmpeg commands. You can set multiple ffmpeg commands for all files before upload. Don't write ffmpeg at beginning, start directly with the arguments.
Examples: {"subtitle": ["-i mltb.mkv -c copy -c:s srt mltb.mkv", "-i mltb.video -c copy -c:s srt mltb"], "convert": ["-i mltb.m4a -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb.audio -c:a libmp3lame -q:a 2 mltb.mp3"], "extract": ["-i mltb -map 0:a -c copy mltb.mka -map 0:s -c copy mltb.srt"], "metadata": ["-i mltb.mkv -map 0 -map -0:v:1 -map -0:s -map 0:s:0 -map -0:v:m:attachment -c copy -metadata:s:v:0 title={title} -metadata:s:a:0 title={title} -metadata:s:a:1 title={title2} -metadata:s:a:2 title={title2} -c:s srt -metadata:s:s:0 title={title3} mltb -y -del"], "watermark": ["-i mltb -i tg://openmessage?user_id=5272663208&message_id=322801 -filter_complex 'overlay=W-w-10:H-h-10' -c:a copy mltb"]}
Notes:
- Add `-del` to the list which you want from the bot to delete the original files after command run complete!
- To execute one of those lists in bot for example, you must use -ff subtitle (list key) or -ff convert (list key)
Here I will explain how to use mltb.* which is reference to files you want to work on.
1. First cmd: the input is mltb.mkv so this cmd will work only on mkv videos and the output is mltb.mkv also so all outputs is mkv. -del will delete the original media after complete run of the cmd.
2. Second cmd: the input is mltb.video so this cmd will work on all videos and the output is only mltb so the extension is same as input files.
3. Third cmd: the input in mltb.m4a so this cmd will work only on m4a audios and the output is mltb.mp3 so the output extension is mp3.
4. Fourth cmd: the input is mltb.audio so this cmd will work on all audios and the output is mltb.mp3 so the output extension is mp3.
5. FFmpeg Variables in last cmd which is metadata ({title}, {title2}, etc...), you can edit them in usetting
6. Telegram link for small size inputs like photo to set watermark.""",
}


help_string = build_help_home_text()

# Enhanced with Interactive UI/UX and Queue Manager
# Modified by: justadi

# Archive Management Help - Modified by: justadi
archive_help = """<b>Archive Management Commands</b>

<b>Create ZIP/TAR Archive</b>: /zip
Usage: /zip <source_path> [format] [level]

Formats:
  • zip      - Universal format (fast compression)
  • tar      - Uncompressed TAR
  • tar.gz   - TAR with GZIP (good compression)
  • tar.bz2  - TAR with BZIP2 (better compression)
  • 7z       - Best compression ratio

Compression Levels (0-9):
  • 0       - No compression
  • 1-5     - Light to medium compression
  • 6       - Default (balanced speed/ratio)
  • 7-9     - High compression (slower)

Examples:
  /zip /downloads/folder
  /zip /downloads/video.mp4 zip 9
  /zip /downloads/files tar.gz

<b>Extract Archive</b>: /unzip
Usage: /unzip <archive_path> [destination] [password]

Examples:
  /unzip /downloads/archive.zip
  /unzip archive.zip /tmp/extracted
  /unzip secure.zip /tmp password123

<b>List Archive Contents</b>: /zipinfo
Usage: /zipinfo <archive_path>

Shows:
  • Number of files in archive
  • Original and compressed size
  • Compression ratio
  • File listing

Example:
  /zipinfo archive.zip
"""

# Media Information Help - Modified by: justadi
media_help = """<b>Media Information Extraction</b>

<b>Get Media Details</b>: /mediainfo
Usage: /mediainfo <file_path> [brief]

Detailed Output:
  • Container format (MP4, MKV, AVI, etc.)
  • Video streams (codec, resolution, fps, bitrate)
  • Audio streams (codec, channels, sample rate)
  • Subtitle tracks
  • Duration and file size
  • Metadata (title, artist, album, etc.)
  • Quality rating

Examples:
  /mediainfo /downloads/movie.mkv
  /mediainfo video.mp4 brief

<b>Extract Video Thumbnail</b>: /thumbnail
Usage: /thumbnail <file_path> [timestamp]

Extracts a frame from video at specified time.
Timestamp Format: HH:MM:SS (default: 00:00:05)

Examples:
  /thumbnail video.mp4                    (extract at 5 seconds)
  /thumbnail movie.mkv 00:00:30           (extract at 30 seconds)
  /thumbnail film.avi 00:02:15            (extract at 2 min 15 sec)

<b>Quick Media Stats</b>: /mstats
Usage: /mstats <file_path>

Shows essential information:
  • Resolution and FPS
  • Duration and file size
  • Codecs (video & audio)
  • Quality rating

Useful for quick checks without detailed analysis.

Example:
  /mstats video.mp4
"""

# Web Dashboard Help - Modified by: justadi
dashboard_web_help = """<b>Web-Based Dashboard</b>

Access real-time download monitoring at:
http://your-bot-domain:8000/dashboard

<b>Features</b>:
  • Real-time task status updates
  • Download/upload progress visualization
  • Speed monitoring (live bitrate)
  • Multi-task management interface
  • System statistics (CPU, RAM, Disk)
  • Task control (pause, resume, cancel)
  • Responsive design for mobile/desktop
  • WebSocket for instant updates

<b>Dashboard Metrics</b>:
  • Active Tasks - Number of running downloads
  • Total Speed - Combined download speed
  • Total Downloads - Count of mirror tasks
  • Total Uploads - Count of leech tasks

<b>Task Controls</b>:
  • Pause - Temporarily stop a task
  • Resume - Continue paused task
  • Cancel - Stop and delete task

<b>System Info</b>:
  • CPU Usage percentage
  • Memory (RAM) usage
  • Disk space usage
  • Bot uptime

<b>WebSocket Updates</b>:
Real-time progress updates without page refresh.
Automatic reconnection on connection loss.
"""

