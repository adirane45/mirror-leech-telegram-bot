"""
Plugin System - Extensible Framework for Custom Features
Allows users to extend bot functionality with custom plugins
Safe Innovation Path - Phase 3

Enhanced by: justadi
Date: February 5, 2026
"""

import asyncio
import importlib
from abc import ABC, abstractmethod
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeAlias

from bot.core import LOGGER, Config


class PluginMetadata:
    """Plugin metadata and information"""

    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        plugin_type: str,
    ) -> None:
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.plugin_type = plugin_type  # backup, alert, monitor, task, etc.
        self.enabled = True
        self.created_at = None


class BasePlugin(ABC):
    """Base class for all plugins"""

    def __init__(self, metadata: PluginMetadata) -> None:
        self.metadata = metadata
        self.is_enabled = True
        self.config: Dict[str, Any] = {}

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize plugin

        Returns:
            True if initialization successful
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown plugin - cleanup resources"""

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute plugin functionality"""

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set plugin configuration"""
        self.config = config

    def get_config(self) -> Dict[str, Any]:
        """Get plugin configuration"""
        return self.config

    def enable(self) -> None:
        """Enable plugin"""
        self.is_enabled = True

    def disable(self) -> None:
        """Disable plugin"""
        self.is_enabled = False


class BackupPlugin(BasePlugin):
    """Base class for backup plugins"""

    async def execute(self, source_path: str, backup_name: str) -> bool:
        """Execute backup

        Args:
            source_path: Path to backup
            backup_name: Name for backup

        Returns:
            True if backup successful
        """
        raise NotImplementedError


class AlertPlugin(BasePlugin):
    """Base class for alert plugins"""

    async def execute(self, alert_data: Dict[str, Any]) -> bool:
        """Execute alert notification

        Args:
            alert_data: Alert information

        Returns:
            True if alert sent successfully
        """
        raise NotImplementedError


class MonitorPlugin(BasePlugin):
    """Base class for monitoring plugins"""

    async def execute(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring

        Args:
            metrics: System metrics

        Returns:
            Monitoring results
        """
        raise NotImplementedError


HookCallback: TypeAlias = Callable[..., Any]


class PluginManager:
    """
    Manages plugin lifecycle and execution
    Handles loading, enabling, disabling, and executing plugins
    """

    _instance: Optional["PluginManager"] = None
    _plugins: Dict[str, BasePlugin] = {}
    _plugin_registry: Dict[str, type[BasePlugin]] = {}
    _hooks: Dict[str, List[HookCallback]] = {}

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._plugins = {}
            self._plugin_registry = {}
            self._hooks = {}
            self._initialized = True

    def enable(self) -> None:
        """Enable plugin manager"""
        enabled = getattr(Config, "ENABLE_PLUGIN_SYSTEM", False)

        if enabled:
            self._load_plugins()
            LOGGER.info("✅ Plugin system enabled")
        else:
            LOGGER.debug("Plugin system disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if plugin manager is enabled"""
        return getattr(Config, "ENABLE_PLUGIN_SYSTEM", False)

    def register_plugin_type(self, plugin_type: str, plugin_class: type[BasePlugin]) -> None:
        """Register a plugin type

        Args:
            plugin_type: Type identifier (e.g., 'backup', 'alert')
            plugin_class: Plugin class to register
        """
        self._plugin_registry[plugin_type] = plugin_class
        LOGGER.debug(f"Plugin type registered: {plugin_type}")

    async def load_plugin(self, plugin_path: str) -> Optional[str]:
        """Load a plugin from file

        Args:
            plugin_path: Path to plugin file or module

        Returns:
            Plugin name if successful, None otherwise
        """
        try:
            Path(plugin_path).parent
            plugin_name = Path(plugin_path).stem

            # Import plugin module
            spec = spec_from_file_location(
                plugin_name,
                plugin_path
            )
            if spec is None or spec.loader is None:
                LOGGER.error(f"Could not load plugin spec: {plugin_path}")
                return None
            module = module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get plugin class (convention: class name = PluginName)
            class_name = "".join(word.capitalize() for word in plugin_name.split("_"))
            plugin_class = getattr(module, class_name, None)

            if not plugin_class or not issubclass(plugin_class, BasePlugin):
                LOGGER.error(f"Invalid plugin class in {plugin_path}")
                return None

            # Instantiate and initialize
            metadata = PluginMetadata(
                name=plugin_name,
                version="1.0.0",
                author="Unknown",
                description="Custom plugin",
                plugin_type="custom",
            )

            plugin = plugin_class(metadata)
            if await plugin.initialize():
                self._plugins[plugin_name] = plugin
                LOGGER.info(f"Plugin loaded: {plugin_name}")
                return plugin_name

            return None

        except Exception as e:
            LOGGER.error(f"Error loading plugin {plugin_path}: {e}")
            return None

    def _load_plugins(self) -> None:
        """Load plugins from plugins directory"""
        plugin_dir = Path(getattr(Config, "PLUGINS_DIR", "plugins"))

        if not plugin_dir.exists():
            LOGGER.debug(f"Plugins directory not found: {plugin_dir}")
            return

        try:
            for plugin_file in plugin_dir.glob("**/*.py"):
                if plugin_file.name.startswith("_"):
                    continue

                # Load plugin synchronously (plugin loading is not async-critical)
                # Avoid asyncio.run() when event loop is already running
                try:
                    from .. import bot_loop
                    if bot_loop.is_running():
                        # Schedule plugin loading as a task
                        bot_loop.create_task(self.load_plugin(str(plugin_file)))
                    else:
                        # Synchronous loading for initialization phase
                        import asyncio
                        asyncio.run(self.load_plugin(str(plugin_file)))
                except Exception as e:
                    LOGGER.warning(f"Failed to load plugin {plugin_file}: {e}")

        except Exception as e:
            LOGGER.error(f"Error loading plugins: {e}")

    async def execute_plugin(self, plugin_name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a plugin

        Args:
            plugin_name: Name of plugin to execute
            *args: Arguments to pass to plugin
            **kwargs: Keyword arguments to pass to plugin

        Returns:
            Plugin execution result
        """
        if plugin_name not in self._plugins:
            LOGGER.error(f"Plugin not found: {plugin_name}")
            return None

        plugin = self._plugins[plugin_name]

        if not plugin.is_enabled:
            LOGGER.warning(f"Plugin is disabled: {plugin_name}")
            return None

        try:
            return await plugin.execute(*args, **kwargs)
        except Exception as e:
            LOGGER.error(f"Error executing plugin {plugin_name}: {e}")
            return None

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get plugin by name"""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all loaded plugins"""
        plugins_list = {}

        for name, plugin in self._plugins.items():
            plugins_list[name] = {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "author": plugin.metadata.author,
                "description": plugin.metadata.description,
                "type": plugin.metadata.plugin_type,
                "enabled": plugin.is_enabled,
            }

        return plugins_list

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].enable()
            LOGGER.info(f"Plugin enabled: {plugin_name}")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self._plugins:
            self._plugins[plugin_name].disable()
            LOGGER.info(f"Plugin disabled: {plugin_name}")
            return True
        return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self._plugins:
            await self._plugins[plugin_name].shutdown()
            del self._plugins[plugin_name]
            LOGGER.info(f"Plugin unloaded: {plugin_name}")
            return True
        return False

    # ============ Hook System ============

    def register_hook(self, hook_name: str, callback: HookCallback) -> None:
        """Register a callback for a hook

        Args:
            hook_name: Name of hook to register for
            callback: Function to call when hook fires
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append(callback)
        LOGGER.debug(f"Hook registered: {hook_name}")

    async def trigger_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Trigger a hook - call all registered callbacks

        Args:
            hook_name: Name of hook to trigger
            *args: Arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks

        Returns:
            List of results from all callbacks
        """
        if hook_name not in self._hooks:
            return []

        results = []

        for callback in self._hooks[hook_name]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                LOGGER.error(f"Error in hook callback: {e}")

        return results

    async def shutdown(self) -> None:
        """Shutdown all plugins"""
        for plugin_name in list(self._plugins.keys()):
            await self.unload_plugin(plugin_name)

        LOGGER.info("All plugins shut down")


# Singleton instance
plugin_manager = PluginManager()
