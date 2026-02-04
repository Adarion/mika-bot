"""
Plugin Manager - Dynamic plugin loading and lifecycle management.
"""

import importlib
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.event_bus import EventBus, Event


class BasePlugin(ABC):
    """
    Base class for all plugins.
    
    Plugins should inherit from this class and implement the required methods.
    """
    
    def __init__(self, event_bus: EventBus, config: Dict[str, Any]):
        self.event_bus = event_bus
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def on_load(self) -> None:
        """Called when the plugin is loaded. Register event handlers here."""
        pass
    
    async def on_unload(self) -> None:
        """Called when the plugin is unloaded. Clean up resources here."""
        pass
    
    def subscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Convenience method to subscribe to events."""
        self.event_bus.subscribe(event_name, handler)
    
    async def publish(self, event_name: str, data: Dict[str, Any]) -> None:
        """Convenience method to publish events."""
        await self.event_bus.publish(event_name, data, source=self.name)


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.
    
    Usage:
        manager = PluginManager(event_bus, config)
        await manager.load_plugins(["chat_plugin", "command_plugin"])
    """
    
    def __init__(self, event_bus: EventBus, plugins_dir: str | Path = "plugins"):
        self.event_bus = event_bus
        self.plugins_dir = Path(plugins_dir)
        self._plugins: Dict[str, BasePlugin] = {}
    
    async def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> Optional[BasePlugin]:
        """Load a single plugin by name."""
        if plugin_name in self._plugins:
            print(f"Plugin {plugin_name} already loaded")
            return self._plugins[plugin_name]
        
        try:
            # Try to import as a module first
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            # Look for a class that inherits from BasePlugin
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr is not BasePlugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                print(f"No BasePlugin subclass found in {plugin_name}")
                return None
            
            # Instantiate and load
            plugin = plugin_class(self.event_bus, config or {})
            await plugin.on_load()
            
            self._plugins[plugin_name] = plugin
            print(f"Loaded plugin: {plugin_name}")
            return plugin
            
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            return None
    
    async def load_plugins(self, plugin_names: List[str], configs: Dict[str, Dict[str, Any]] = None) -> None:
        """Load multiple plugins."""
        configs = configs or {}
        for name in plugin_names:
            await self.load_plugin(name, configs.get(name, {}))
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self._plugins:
            return False
        
        try:
            plugin = self._plugins[plugin_name]
            await plugin.on_unload()
            del self._plugins[plugin_name]
            print(f"Unloaded plugin: {plugin_name}")
            return True
        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def unload_all(self) -> None:
        """Unload all plugins."""
        for name in list(self._plugins.keys()):
            await self.unload_plugin(name)
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)
    
    @property
    def loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names."""
        return list(self._plugins.keys())
