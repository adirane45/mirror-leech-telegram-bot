"""
Configuration Manager - Compatibility Shim

This module provides backwards compatibility for code importing from config_manager.
All configuration is now centralized in config/main_config.py which reads from .env files.
"""

from typing import Callable, Dict, List, Tuple

# Import Config class from centralized config location
# Try local import first, then Docker fallback
try:
    from config.main_config import Config
except (ImportError, ModuleNotFoundError):
    from config import Config


REQUIRED_CONFIG_RULES: Dict[str, Callable[[object], bool]] = {
    "BOT_TOKEN": lambda v: isinstance(v, str) and len(v) > 10 and not v.startswith("YOUR_"),
    "OWNER_ID": lambda v: isinstance(v, int) and v > 0,
    "TELEGRAM_API": lambda v: isinstance(v, int) and v > 0,
    "TELEGRAM_HASH": lambda v: isinstance(v, str) and len(v) > 0,
    "MONGODB_URL": lambda v: isinstance(v, str) and "mongodb" in v,
    "REDIS_HOST": lambda v: isinstance(v, str) and len(v) > 0,
    "REDIS_PORT": lambda v: isinstance(v, int) and v > 0,
    "CELERY_BROKER_URL": lambda v: isinstance(v, str) and len(v) > 0,
    "API_HOST": lambda v: isinstance(v, str) and len(v) > 0,
    "API_PORT": lambda v: isinstance(v, int) and v > 0,
    "ENVIRONMENT": lambda v: v in ("production", "development"),
}


def validate_required_config(strict: bool = True) -> Tuple[bool, List[str]]:
    """Validate required configuration values.

    Returns:
        (is_valid, missing_or_invalid_keys)
    """
    missing_or_invalid: List[str] = []
    for key, rule in REQUIRED_CONFIG_RULES.items():
        value = getattr(Config, key, None)
        if not rule(value):
            missing_or_invalid.append(key)

    is_valid = not missing_or_invalid
    if strict and not is_valid:
        raise RuntimeError(
            f"Missing or invalid required config values: {', '.join(missing_or_invalid)}"
        )

    return is_valid, missing_or_invalid


__all__ = ["Config", "validate_required_config", "REQUIRED_CONFIG_RULES"]
