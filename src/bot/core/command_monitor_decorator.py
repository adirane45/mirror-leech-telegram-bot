"""
Command Monitoring Decorator for Automatic Tracking

Wrap command handlers with @monitor_command() to automatically track execution.
"""

import time
import functools
from typing import Optional, Callable
from .. import LOGGER
from .command_health_monitor import command_health_monitor, CommandStatus


def monitor_command(command_name: Optional[str] = None):
    """
    Decorator to automatically monitor command execution.
    
    Usage:
        @monitor_command()
        async def my_handler(client, message):
            # Your command logic
            pass
    
        @monitor_command("customname")
        async def another_handler(client, message):
            # Override auto-detected command name
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            # Determine command name
            cmd_name = command_name
            if not cmd_name:
                # Try to extract from message
                try:
                    text = getattr(message, "text", "") or ""
                    if text.startswith("/"):
                        cmd_name = text.split()[0].lstrip("/")
                    else:
                        cmd_name = func.__name__.replace("_handler", "").replace("_", "")
                except Exception:
                    cmd_name = func.__name__
            
            # Get user ID
            try:
                user_id = message.from_user.id if message.from_user else 0
            except Exception:
                user_id = 0
            
            # Skip if monitoring disabled
            if not command_health_monitor._enabled:
                return await func(client, message, *args, **kwargs)
            
            # Track execution
            start_time = time.time()
            error_occurred = None
            error_type = None
            
            try:
                result = await func(client, message, *args, **kwargs)
                
                # Record success
                await command_health_monitor.record_execution(
                    command=cmd_name,
                    user_id=user_id,
                    status=CommandStatus.SUCCESS,
                    duration_ms=(time.time() - start_time) * 1000
                )
                
                return result
                
            except TimeoutError as e:
                error_occurred = str(e)
                error_type = "TimeoutError"
                
                await command_health_monitor.record_execution(
                    command=cmd_name,
                    user_id=user_id,
                    status=CommandStatus.TIMEOUT,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=error_occurred,
                    error_type=error_type
                )
                raise
                
            except Exception as e:
                error_occurred = str(e)
                error_type = type(e).__name__
                
                await command_health_monitor.record_execution(
                    command=cmd_name,
                    user_id=user_id,
                    status=CommandStatus.FAILURE,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=error_occurred,
                    error_type=error_type
                )
                raise
        
        return wrapper
    return decorator


def monitor_command_simple(func: Callable):
    """
    Simple decorator variant without parameters.
    
    Usage:
        @monitor_command_simple
        async def my_handler(client, message):
            pass
    """
    return monitor_command()(func)
