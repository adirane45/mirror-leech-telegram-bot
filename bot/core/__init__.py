"""
Bot Core Module
Centralized imports for core components
"""

from logging import getLogger
from bot.core.config_manager import Config

LOGGER = getLogger(__name__)

__all__ = ["LOGGER", "Config"]

