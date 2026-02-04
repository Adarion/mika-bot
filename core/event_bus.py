"""
Event Bus - Central message broker for the application.
Supports async event handlers with publish/subscribe pattern.
"""

import asyncio
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Event:
    """Represents an event in the system."""
    name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"


class EventBus:
    """
    Async Event Bus implementation.
    
    Usage:
        bus = EventBus()
        
        async def handler(event: Event):
            print(event.data)
        
        bus.subscribe("message.received", handler)
        await bus.publish("message.received", {"content": "Hello"})
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._global_handlers: List[Callable[[Event], Any]] = []
    
    def subscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe a handler to a specific event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def subscribe_all(self, handler: Callable[[Event], Any]) -> None:
        """Subscribe a handler to all events (useful for logging)."""
        self._global_handlers.append(handler)
    
    def unsubscribe(self, event_name: str, handler: Callable[[Event], Any]) -> None:
        """Unsubscribe a handler from a specific event."""
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name] if h != handler
            ]
    
    async def publish(self, event_name: str, data: Dict[str, Any], source: str = "unknown") -> None:
        """Publish an event to all subscribed handlers."""
        event = Event(name=event_name, data=data, source=source)
        
        # Collect all handlers
        handlers = self._handlers.get(event_name, []) + self._global_handlers
        
        # Run all handlers concurrently
        if handlers:
            await asyncio.gather(
                *[self._safe_call(handler, event) for handler in handlers],
                return_exceptions=True
            )
    
    async def _safe_call(self, handler: Callable[[Event], Any], event: Event) -> Any:
        """Safely call a handler, catching exceptions."""
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            print(f"Error in event handler for {event.name}: {e}")
            return None


# Singleton instance
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
