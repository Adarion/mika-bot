"""
Base IM Adapter - Abstract interface for IM platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class User:
    """Represents a user in the IM platform."""
    id: str
    name: str
    avatar_url: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Channel:
    """Represents a channel/group in the IM platform."""
    id: str
    name: str
    type: str = "group"  # "group", "private", "guild"
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IncomingMessage:
    """Represents an incoming message from the IM platform."""
    id: str
    content: str
    author: User
    channel: Channel
    timestamp: datetime = field(default_factory=datetime.now)
    mentions_bot: bool = False
    reply_to: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    
    # Platform identifier
    platform: str = "unknown"


@dataclass
class OutgoingMessage:
    """Represents an outgoing message to send."""
    content: str
    channel_id: str
    reply_to: Optional[str] = None
    attachments: List[str] = field(default_factory=list)


class BaseIMAdapter(ABC):
    """
    Abstract base class for IM platform adapters.
    
    All IM platforms should implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any], on_message: Callable[[IncomingMessage], Any]):
        """
        Initialize the adapter.
        
        Args:
            config: Platform-specific configuration.
            on_message: Callback function when a message is received.
        """
        self.config = config
        self.on_message = on_message
        self.platform_name = "unknown"
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to the IM platform."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the IM platform."""
        pass
    
    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> bool:
        """
        Send a message to a channel.
        
        Args:
            message: The message to send.
        
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def reply(self, original: IncomingMessage, content: str, **kwargs) -> bool:
        """
        Reply to a specific message.
        
        Args:
            original: The message to reply to.
            content: The reply content.
            **kwargs: Additional platform-specific arguments (e.g., msg_seq).
        
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if the adapter is connected."""
        return False
