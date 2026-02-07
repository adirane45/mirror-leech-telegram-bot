"""
Configuration Manager - Compatibility Shim

This module provides backwards compatibility for code importing from config_manager.
All configuration is now centralized in config/main_config.py which reads from .env files.
"""

# Import Config class from centralized config location
from config.main_config import Config

__all__ = ["Config"]
