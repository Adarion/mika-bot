"""
IM Adapter Factory - Creates IM adapters based on configuration.
"""

from typing import Any, Callable, Dict, List

from .base import BaseIMAdapter, IncomingMessage


# Registry of adapter classes
_ADAPTER_REGISTRY: Dict[str, type] = {}


def register_adapter(name: str, adapter_class: type) -> None:
    """Register a custom IM adapter class."""
    _ADAPTER_REGISTRY[name] = adapter_class


def _ensure_builtin_adapters():
    """Lazy-load built-in adapters to avoid circular imports."""
    if "qq" not in _ADAPTER_REGISTRY:
        from .qq_adapter import QQAdapter
        _ADAPTER_REGISTRY["qq"] = QQAdapter


def create_adapter(
    platform_type: str, 
    config: Dict[str, Any],
    on_message: Callable[[IncomingMessage], Any]
) -> BaseIMAdapter:
    """
    Create an IM adapter based on platform type.
    
    Args:
        platform_type: Type of platform (qq, discord, telegram, etc.)
        config: Configuration dict for the adapter.
        on_message: Callback for incoming messages.
    
    Returns:
        An instance of the appropriate adapter.
    
    Raises:
        ValueError: If the platform type is not supported.
    """
    _ensure_builtin_adapters()
    platform_type = platform_type.lower()
    
    if platform_type not in _ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown IM platform: {platform_type}. "
            f"Available: {list(_ADAPTER_REGISTRY.keys())}"
        )
    
    adapter_class = _ADAPTER_REGISTRY[platform_type]
    return adapter_class(config, on_message)


class IMManager:
    """
    Manages multiple IM platform adapters.
    
    Usage:
        manager = IMManager(config, on_message_callback)
        await manager.connect_all()
    """
    
    def __init__(self, config: List[Dict[str, Any]], on_message: Callable[[IncomingMessage], Any]):
        """
        Initialize with config from the "im" section.
        
        Expected config format (list):
        [
            {"type": "qq", "app_id": "...", "token": "..."},
            {"type": "discord", "token": "..."}
        ]
        """
        self.config = config
        self.on_message = on_message
        self._adapters: Dict[str, BaseIMAdapter] = {}
    
    async def connect_all(self) -> None:
        """Connect all configured IM platforms."""
        for platform_config in self.config:
            platform_type = platform_config.get("type")
            if not platform_type:
                print("Skipping IM config without 'type' field")
                continue
            
            try:
                adapter = create_adapter(platform_type, platform_config, self.on_message)
                await adapter.connect()
                self._adapters[platform_type] = adapter
                print(f"Connected to IM platform: {platform_type}")
            except Exception as e:
                print(f"Failed to connect to {platform_type}: {e}")
    
    async def disconnect_all(self) -> None:
        """Disconnect all IM platforms."""
        for name, adapter in self._adapters.items():
            try:
                await adapter.disconnect()
                print(f"Disconnected from: {name}")
            except Exception as e:
                print(f"Error disconnecting from {name}: {e}")
        self._adapters.clear()
    
    def get_adapter(self, platform: str) -> BaseIMAdapter:
        """Get a specific adapter by platform name."""
        if platform not in self._adapters:
            raise ValueError(f"IM platform not connected: {platform}")
        return self._adapters[platform]
    
    @property
    def connected_platforms(self) -> List[str]:
        """List of connected platform names."""
        return list(self._adapters.keys())
