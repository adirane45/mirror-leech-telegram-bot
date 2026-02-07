"""
Bot Core Module
Centralized imports for core components
"""

from logging import getLogger

# Import config - handles both 'config.main_config' (local) and 'config' (Docker)
try:
    from config.main_config import Config
except (ImportError, ModuleNotFoundError):
    from config import Config

LOGGER = getLogger(__name__)

__all__ = ["LOGGER", "Config"]

