"""
Short-Term Memory - Buffer for recent conversation context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json


@dataclass
class Message:
    """A single message in memory."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


class ShortTermMemory:
    """
    In-memory buffer for recent conversation messages.
    
    Stores the most recent N messages per user for immediate context.
    """
    
    def __init__(self, max_messages: int = 10):
        """
        Initialize short-term memory.
        
        Args:
            max_messages: Maximum messages to keep per user
        """
        self.max_messages = max_messages
        self._store: Dict[str, List[Message]] = {}
    
    def add(self, user_id: str, role: str, content: str) -> None:
        """
        Add a message to user's memory.
        
        Args:
            user_id: Unique user identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        if user_id not in self._store:
            self._store[user_id] = []
        
        self._store[user_id].append(Message(role=role, content=content))
        
        # Trim if exceeds limit
        if len(self._store[user_id]) > self.max_messages:
            self._store[user_id] = self._store[user_id][-self.max_messages:]
    
    def get(self, user_id: str, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages for a user.
        
        Args:
            user_id: Unique user identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of messages, oldest first
        """
        messages = self._store.get(user_id, [])
        if limit:
            return messages[-limit:]
        return messages
    
    def get_formatted(self, user_id: str, limit: Optional[int] = None) -> str:
        """
        Get messages formatted as conversation string.
        
        Args:
            user_id: Unique user identifier
            limit: Optional limit on number of messages
            
        Returns:
            Formatted conversation string
        """
        messages = self.get(user_id, limit)
        if not messages:
            return ""
        
        lines = []
        for msg in messages:
            role_label = "用户" if msg.role == "user" else "助手"
            lines.append(f"{role_label}: {msg.content}")
        
        return "\n".join(lines)
    
    def get_for_llm(self, user_id: str, limit: Optional[int] = None) -> List[dict]:
        """
        Get messages formatted for LLM API.
        
        Args:
            user_id: Unique user identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of message dicts with role and content
        """
        messages = self.get(user_id, limit)
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def clear(self, user_id: str) -> None:
        """Clear all messages for a user."""
        if user_id in self._store:
            del self._store[user_id]
    
    def pop_oldest(self, user_id: str, count: int = 1) -> List[Message]:
        """
        Remove and return oldest messages.
        
        Args:
            user_id: Unique user identifier
            count: Number of messages to pop
            
        Returns:
            List of popped messages
        """
        if user_id not in self._store:
            return []
        
        messages = self._store[user_id][:count]
        self._store[user_id] = self._store[user_id][count:]
        return messages
    
    def count(self, user_id: str) -> int:
        """Get message count for a user."""
        return len(self._store.get(user_id, []))
    
    def is_full(self, user_id: str) -> bool:
        """Check if user's memory is at capacity."""
        return self.count(user_id) >= self.max_messages

    def pop_last(self, user_id: str) -> Optional[Message]:
        """
        Remove and return the most recent message.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            The removed message, or None if no messages
        """
        if user_id not in self._store or not self._store[user_id]:
            return None
        return self._store[user_id].pop()
