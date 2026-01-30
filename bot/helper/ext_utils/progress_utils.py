# Progress Bar Utilities for Downloads
# Enhanced visual progress indicators
# Modified by: justadi

def get_progress_bar(current: float, total: float, width: int = 20) -> str:
    """
    Generate a simple progress bar with percentage
    
    Args:
        current: Current progress value
        total: Total value
        width: Width of the progress bar
        
    Returns:
        Progress bar string in format: [████░░░░] 40%
    """
    if total == 0:
        return "[" + "█" * width + "] 100%"
    
    percentage = (current / total) * 100
    filled = int(width * current / total)
    
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


def get_horizontal_progress(current: float, total: float, width: int = 20) -> str:
    """Generate horizontal progress bar without percentage"""
    if total == 0:
        return "█" * width
    
    filled = int(width * current / total)
    return "█" * filled + "░" * (width - filled)


def get_download_progress_text(download) -> str:
    """
    Generate progress text for a download with all details
    
    Args:
        download: Download object with progress information
        
    Returns:
        Formatted progress text
    """
    if not hasattr(download, 'progress') or not hasattr(download, 'size'):
        return ""
    
    try:
        progress = download.progress()
        total_size = download.size()
        
        if total_size == 0:
            return ""
        
        current_size = (progress / 100) * total_size if isinstance(progress, (int, float)) else 0
        
        progress_text = f"{get_progress_bar(current_size, total_size)}\n"
        progress_text += f"<code>{current_size:.1f}MB / {total_size:.1f}MB</code>"
        
        return progress_text
    except Exception:
        return ""


def get_estimated_time(current: float, total: float, speed: float) -> str:
    """
    Calculate estimated time remaining
    
    Args:
        current: Current progress in bytes
        total: Total size in bytes
        speed: Current speed in bytes per second
        
    Returns:
        Formatted time string
    """
    if speed <= 0 or total <= current:
        return "N/A"
    
    remaining_bytes = total - current
    seconds_remaining = remaining_bytes / speed
    
    hours = int(seconds_remaining // 3600)
    minutes = int((seconds_remaining % 3600) // 60)
    seconds = int(seconds_remaining % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
