# Enhanced Features - API Reference & Class Glossary

## Table of Contents
1. [ProgressBar Class](#progressbar-class)
2. [HealthIndicator Class](#healthindicator-class)
3. [SystemStats Class](#systemstats-class)
4. [TaskStats Class](#taskstats-class)
5. [StatsFormatter Class](#statsformatter-class)
6. [FeedbackLevel Enum](#feedbacklevel-enum)
7. [Notification Class](#notification-class)
8. [NotificationCenter Class](#notificationcenter-class)
9. [ProgressTracker Class](#progresstracker-class)
10. [FeedbackFormatter Class](#feedbackformatter-class)
11. [RealtimeFeedback Class](#realtimefeedback-class)
12. [EnhancedStatusBuilder Class](#enhancedstatusbuilder-class)
13. [EnhancedDashboard Class](#enhanceddashboard-class)
14. [MessageEnhancer Class](#messageenhancer-class)

---

## ProgressBar Class
**Module**: `bot.core.enhanced_stats`  
**Purpose**: Create visual progress bars with multiple styles  

### Methods

#### `filled_bar(percentage: float, length: int = 10, show_percent: bool = True) -> str`
Creates a filled progress bar using block characters.

**Parameters**:
- `percentage` (float): Progress value 0-100
- `length` (int): Number of blocks (default: 10)
- `show_percent` (bool): Show percentage text (default: True)

**Returns**: String representation of progress bar

**Examples**:
```python
ProgressBar.filled_bar(85.5)           # "████████░░ 85.5%"
ProgressBar.filled_bar(50, length=20)  # "██████████░░░░░░░░░░ 50.0%"
ProgressBar.filled_bar(75, show_percent=False)  # "███████░░░"
```

#### `emoji_bar(percentage: float) -> str`
Creates an emoji-based progress bar.

**Parameters**:
- `percentage` (float): Progress value 0-100

**Returns**: String with emoji blocks

**Examples**:
```python
ProgressBar.emoji_bar(75)   # "🟦🟦🟦🟦🟦🟦🟦🟦⬜"
ProgressBar.emoji_bar(50)   # "🟦🟦🟦🟦🟦⬜⬜⬜⬜⬜"
```

#### `blocks_bar(percentage: float, length: int = 20) -> str`
Creates a block-based progress bar with rounded corners.

**Parameters**:
- `percentage` (float): Progress value 0-100
- `length` (int): Total block length (default: 20)

**Returns**: String with block characters and percentage

**Examples**:
```python
ProgressBar.blocks_bar(60)  # "[▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱] 60%"
```

---

## HealthIndicator Class
**Module**: `bot.core.enhanced_stats`  
**Purpose**: Provide health status indicators based on resource metrics  

### Constants
- `STATUS_EXCELLENT` = "🟢" (≥80%)
- `STATUS_GOOD` = "🟡" (50-80%)
- `STATUS_WARNING` = "🟠" (20-50%)
- `STATUS_CRITICAL` = "🔴" (<20%)
- `STATUS_OFFLINE` = "⚫" (0%)

### Methods

#### `get_health_indicator(percentage: int) -> str`
Get health indicator emoji based on usage percentage.

**Parameters**:
- `percentage` (int): Resource usage 0-100

**Returns**: Emoji indicator

**Examples**:
```python
HealthIndicator.get_health_indicator(85)   # "🟢"
HealthIndicator.get_health_indicator(65)   # "🟡"
HealthIndicator.get_health_indicator(35)   # "🟠"
HealthIndicator.get_health_indicator(10)   # "🔴"
```

#### `get_resource_status(name: str, value: float, max_value: Optional[float] = None) -> str`
Get formatted resource status with indicator.

**Parameters**:
- `name` (str): Resource name (CPU, RAM, etc.)
- `value` (float): Current value
- `max_value` (float, optional): Maximum value for percentage

**Returns**: Formatted status string

**Examples**:
```python
HealthIndicator.get_resource_status("CPU", 75)    # "🟡 CPU: 75.0%"
HealthIndicator.get_resource_status("RAM", 16, 32) # "🟡 RAM: 50.0%"
```

---

## SystemStats Class
**Module**: `bot.core.enhanced_stats`  
**Purpose**: Collect and format system statistics  

### Methods

#### `get_cpu_stats() -> Dict`
Get comprehensive CPU statistics.

**Returns**: Dictionary with keys:
- `overall`: Overall CPU percentage
- `per_cpu`: List of per-core percentages
- `cores_total`: Total logical cores
- `cores_physical`: Physical cores

**Example**:
```python
stats = SystemStats.get_cpu_stats()
print(stats['overall'])     # 45.5
print(stats['per_cpu'])     # [42.0, 48.0, 45.5, 44.0]
print(stats['cores_total']) # 4
```

#### `get_memory_stats() -> Dict`
Get comprehensive memory statistics.

**Returns**: Dictionary with keys:
- `total`: Total memory bytes
- `used`: Used memory bytes
- `available`: Available memory bytes
- `percent`: Usage percentage
- `percent_readable`: Formatted percentage string

#### `get_disk_stats(path: str = "/") -> Dict`
Get disk statistics for specified path.

**Parameters**:
- `path` (str): Disk path to check (default: "/")

**Returns**: Dictionary with keys:
- `total`: Total disk bytes
- `used`: Used disk bytes
- `free`: Free disk bytes
- `percent`: Usage percentage
- `percent_readable`: Formatted percentage

#### `get_network_stats() -> Dict`
Get network I/O statistics.

**Returns**: Dictionary with keys:
- `bytes_sent`: Total bytes sent
- `bytes_recv`: Total bytes received
- `packets_sent`: Total packets sent
- `packets_recv`: Total packets received

#### `format_cpu_details() -> str`
Get formatted CPU information.

**Returns**: HTML formatted string with CPU details

#### `format_memory_details() -> str`
Get formatted memory information.

**Returns**: HTML formatted string with memory details

#### `format_disk_details(path: str = "/") -> str`
Get formatted disk information.

**Returns**: HTML formatted string with disk details

#### `format_network_stats() -> str`
Get formatted network statistics.

**Returns**: HTML formatted string with network info

---

## TaskStats Class
**Module**: `bot.core.enhanced_stats`  
**Purpose**: Calculate aggregate statistics from multiple tasks  

### Methods

#### `calculate_total_speed(tasks: list) -> str`
Calculate combined speed from all tasks.

**Parameters**:
- `tasks` (list): List of task objects

**Returns**: Formatted speed string (e.g., "15.5 MB/s")

#### `calculate_total_size(tasks: list) -> str`
Calculate combined size of all tasks.

**Parameters**:
- `tasks` (list): List of task objects

**Returns**: Formatted size string (e.g., "250 GB")

#### `estimate_total_eta(tasks: list) -> str`
Estimate combined ETA from all tasks.

**Parameters**:
- `tasks` (list): List of task objects

**Returns**: Formatted time string (e.g., "2h 30m")

---

## StatsFormatter Class
**Module**: `bot.core.enhanced_stats`  
**Purpose**: Format statistics for beautiful display  

### Methods

#### `format_system_dashboard(bot_start_time: float, download_dir: str = "/") -> str`
Create a beautiful system dashboard.

**Parameters**:
- `bot_start_time` (float): Bot start timestamp
- `download_dir` (str): Download directory path

**Returns**: HTML formatted dashboard string

#### `format_quick_stats(active_tasks: int, total_downloaded: str, total_uploaded: str, cpu_percent: float, mem_percent: float, free_disk: str) -> str`
Create quick stats summary card.

**Returns**: HTML formatted quick stats

#### `format_detailed_stats(tasks: list, cpu_percent: float, mem_percent: float, disk_percent: float, free_disk: str) -> str`
Create detailed statistics report.

**Returns**: HTML formatted detailed stats

---

## FeedbackLevel Enum
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Define feedback severity levels  

### Values
- `INFO` = "ℹ️"
- `SUCCESS` = "✅"
- `WARNING` = "⚠️"
- `ERROR` = "❌"
- `PROGRESS` = "⏳"
- `CRITICAL` = "🚨"

**Usage**:
```python
level = FeedbackLevel.SUCCESS
print(level.value)  # "✅"
```

---

## Notification Class
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Represent a single notification  

### Constructor
```python
Notification(
    title: str,
    message: str,
    notif_type: NotificationType = NotificationType.CUSTOM,
    level: FeedbackLevel = FeedbackLevel.INFO,
    timestamp: Optional[float] = None,
    data: Optional[Dict] = None
)
```

### Properties
- `title` (str): Notification title
- `message` (str): Notification message
- `notif_type` (NotificationType): Type of notification
- `level` (FeedbackLevel): Severity level
- `timestamp` (float): When notification was created
- `data` (Dict): Custom data
- `read` (bool): Read status

### Methods

#### `format_text() -> str`
Format notification for display.

**Returns**: Formatted string

#### `to_dict() -> Dict`
Convert notification to dictionary.

**Returns**: Dictionary representation

---

## NotificationCenter Class
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Centralized notification management  

### Constructor
```python
NotificationCenter(max_notifications: int = 100)
```

### Methods

#### `async send(notification: Notification) -> None`
Send a notification.

**Parameters**:
- `notification`: Notification object

#### `async get_notifications(count: int = 10) -> List[Notification]`
Get recent notifications.

**Parameters**:
- `count` (int): Number of notifications to retrieve

#### `subscribe(notification_type: str, callback: Callable) -> None`
Subscribe to notifications.

**Parameters**:
- `notification_type` (str): Type to subscribe to
- `callback`: Function to call

#### `async get_unread_count() -> int`
Get count of unread notifications.

**Returns**: Integer count

#### `async mark_as_read(index: int) -> None`
Mark notification as read.

**Parameters**:
- `index` (int): Notification index

#### `async clear_notifications() -> None`
Clear all notifications.

---

## ProgressTracker Class
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Track and display progress  

### Constructor
```python
ProgressTracker(
    task_id: str,
    task_name: str,
    total: float = 100
)
```

### Properties
- `task_id` (str): Unique task identifier
- `task_name` (str): Task display name
- `total` (float): Total value to reach
- `current` (float): Current progress
- `speed` (float): Current speed
- `eta_seconds` (float): Estimated time remaining
- `status` (str): Current status
- `substatus` (str): Additional status info

### Methods

#### `update(current: float) -> None`
Update progress value.

**Parameters**:
- `current` (float): Current progress

#### `get_progress_percentage() -> float`
Get progress as percentage (0-100).

**Returns**: Float percentage

#### `get_elapsed_time() -> float`
Get elapsed time in seconds.

**Returns**: Float seconds

#### `format_progress_bar(length: int = 20) -> str`
Format progress bar.

**Parameters**:
- `length` (int): Bar length

**Returns**: Formatted bar string

#### `format_details() -> str`
Format detailed progress information.

**Returns**: HTML formatted details

#### `format_compact() -> str`
Format compact progress display.

**Returns**: Compact string

---

## FeedbackFormatter Class
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Format feedback messages for users  

### Static Methods

#### `format_task_started(task_name: str, source: str = "") -> str`
Format task started message.

#### `format_task_progress(task_name: str, progress: float, speed: str = "", eta: str = "") -> str`
Format task progress message.

#### `format_task_completed(task_name: str, size: str = "", time_taken: str = "") -> str`
Format task completed message.

#### `format_task_failed(task_name: str, error: str = "") -> str`
Format task failed message.

#### `format_resource_warning(resource_name: str, current: float, threshold: float) -> str`
Format resource warning.

#### `format_system_alert(alert_title: str, alert_message: str) -> str`
Format system alert.

#### `format_inline_feedback(status_emoji: str, title: str, details: str = "") -> str`
Format inline feedback message.

#### `format_action_summary(action: str, success_count: int = 0, failed_count: int = 0, duration: str = "") -> str`
Format action summary.

---

## RealtimeFeedback Class
**Module**: `bot.core.enhanced_feedback`  
**Purpose**: Manage real-time feedback sessions  

### Methods

#### `async start_feedback(feedback_id: str, title: str, initial_message: str = "") -> None`
Start a new feedback session.

#### `async update_feedback(feedback_id: str, message: str, append: bool = False) -> None`
Update active feedback.

**Parameters**:
- `feedback_id` (str): Session ID
- `message` (str): Update message
- `append` (bool): Append to existing (True) or replace (False)

#### `async end_feedback(feedback_id: str, final_message: str = "") -> Dict`
End feedback session.

**Returns**: Feedback history dictionary

#### `async get_active_feedback(feedback_id: str) -> Optional[Dict]`
Get active feedback by ID.

#### `async get_all_active() -> Dict`
Get all active feedbacks.

#### `async cancel_feedback(feedback_id: str) -> None`
Cancel a feedback session.

---

## EnhancedStatusBuilder Class
**Module**: `bot.core.enhanced_status_integration`  
**Purpose**: Build enhanced status messages  

### Static Methods

#### `async build_task_message(task, index: int = 1, include_progress_bar: bool = True, include_health: bool = True, compact: bool = False) -> str`
Build enhanced status for single task.

#### `build_status_header(download_count: int, upload_count: int, paused_count: int, queued_count: int, other_count: int) -> str`
Build status overview header.

#### `build_resource_footer(cpu_percent: float, mem_percent: float, disk_free: str, uptime: str, include_health: bool = True) -> str`
Build resource footer.

#### `async build_full_status_message(tasks: List, task_counts: Dict, cpu_percent: float, mem_percent: float, disk_free: str, uptime: str, include_progress_bars: bool = True, compact: bool = False) -> str`
Build complete status message.

---

## EnhancedDashboard Class
**Module**: `bot.core.enhanced_status_integration`  
**Purpose**: Create enhanced dashboard views  

### Static Methods

#### `create_quick_view(active_tasks: int, cpu_percent: float, ram_percent: float, disk_free: str) -> str`
Create quick dashboard view.

#### `create_detailed_view(tasks: List, bot_start_time: float, download_dir: str = "/") -> str`
Create detailed dashboard view.

#### `create_analytics_view(tasks: List) -> str`
Create analytics dashboard view.

---

## MessageEnhancer Class
**Module**: `bot.core.enhanced_status_integration`  
**Purpose**: Enhance existing messages  

### Static Methods

#### `add_buttons_to_message(message_text: str, task_count: int, include_refresh: bool = True, include_view_modes: bool = True) -> str`
Add button hints to message.

#### `enhance_task_display(task_message: str, warning_threshold: float = 85.0, critical_threshold: float = 95.0) -> str`
Enhance task message with warnings.

#### `format_error_with_feedback(error_title: str, error_message: str, suggestion: str = "") -> str`
Format error messages with help.

#### `format_success_with_feedback(action: str, result: str = "", duration: str = "") -> str`
Format success messages.

---

## Quick Command Reference

### New Telegram Commands

| Command | Handler | Purpose |
|---------|---------|---------|
| `/estats` | `enhanced_stats_handler` | Enhanced statistics |
| `/edash` | `enhanced_dashboard_handler` | Detailed dashboard |
| `/equick` | `enhanced_quick_status_handler` | Quick status |
| `/eanalytics` | `enhanced_analytics_handler` | Task analytics |
| `/rmon` | `resource_monitor_handler` | Resource monitor |
| `/health` | `system_health_handler` | System health |
| `/psummary` | `progress_summary_handler` | Progress summary |
| `/cstats` | `comparison_stats_handler` | Comparison stats |

---

## Enum Reference

### NotificationType
```python
TASK_STARTED = "task_started"
TASK_PROGRESS = "task_progress"
TASK_COMPLETED = "task_completed"
TASK_FAILED = "task_failed"
TASK_PAUSED = "task_paused"
TASK_RESUMED = "task_resumed"
SYSTEM_ALERT = "system_alert"
RESOURCE_WARNING = "resource_warning"
CUSTOM = "custom"
```

---

## Common Patterns

### Pattern 1: Show Progress
```python
tracker = ProgressTracker("id", "Task", 100)
tracker.update(50)
print(tracker.format_progress_bar())
```

### Pattern 2: Send Notification
```python
center = NotificationCenter()
notif = Notification("Title", "Message", level=FeedbackLevel.SUCCESS)
await center.send(notif)
```

### Pattern 3: Display System Status
```python
text = StatsFormatter.format_system_dashboard(bot_start_time)
await send_message(message, text)
```

### Pattern 4: Real-time Feedback
```python
feedback = RealtimeFeedback()
await feedback.start_feedback("op1", "Operation")
await feedback.update_feedback("op1", "Step 1...")
await feedback.end_feedback("op1", "Done!")
```

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| ProgressBar creation | <1ms | Very fast |
| HealthIndicator lookup | <1ms | Instant |
| SystemStats collection | ~1-2s | Includes psutil interval |
| TaskStats calculation | <50ms | Linear with task count |
| Formatting | <10ms | String building |
| Notification send | <5ms | Async operation |

---

**Last Updated**: February 7, 2026  
**API Version**: 1.0.0  
**Status**: Production Ready
