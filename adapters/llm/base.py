"""
Base LLM Adapter - Abstract interface for LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class Message:
    """Represents a chat message."""
    role: str  # "system", "user", "assistant"
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatResponse:
    """Represents a response from an LLM."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class StreamChunk:
    """Represents a streaming chunk from an LLM."""
    content: str
    finish_reason: Optional[str] = None


class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.
    
    All LLM providers should implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "default")
    
    @abstractmethod
    async def chat(
        self, 
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Send a chat completion request.
        
        Args:
            messages: List of chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Provider-specific options.
        
        Returns:
            ChatResponse with the completion.
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        Send a streaming chat completion request.
        
        Args:
            messages: List of chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            **kwargs: Provider-specific options.
        
        Yields:
            StreamChunk for each token/chunk.
        """
        pass
    
    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to dict format."""
        result = []
        for msg in messages:
            d = {"role": msg.role, "content": msg.content}
            if msg.name:
                d["name"] = msg.name
            if msg.tool_calls:
                d["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                d["tool_call_id"] = msg.tool_call_id
            result.append(d)
        return result
