"""
LLM Adapter Factory - Creates LLM adapters based on configuration.
"""

from typing import Any, Dict, Optional

from .base import BaseLLMAdapter
from .openai_adapter import OpenAIAdapter
from .vertex_adapter import VertexAIAdapter


# Registry of adapter classes
_ADAPTER_REGISTRY: Dict[str, type] = {
    "openai": OpenAIAdapter,
    "vertex": VertexAIAdapter,
    "vertex_ai": VertexAIAdapter,
    "deepseek": OpenAIAdapter,  # DeepSeek uses OpenAI-compatible API
    "moonshot": OpenAIAdapter,  # Moonshot uses OpenAI-compatible API
}


def register_adapter(name: str, adapter_class: type) -> None:
    """Register a custom adapter class."""
    _ADAPTER_REGISTRY[name] = adapter_class


def create_adapter(provider_type: str, config: Dict[str, Any]) -> BaseLLMAdapter:
    """
    Create an LLM adapter based on provider type.
    
    Args:
        provider_type: Type of provider (openai, vertex, deepseek, etc.)
        config: Configuration dict for the adapter.
    
    Returns:
        An instance of the appropriate adapter.
    
    Raises:
        ValueError: If the provider type is not supported.
    """
    provider_type = provider_type.lower()
    
    if provider_type not in _ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown LLM provider: {provider_type}. "
            f"Available: {list(_ADAPTER_REGISTRY.keys())}"
        )
    
    adapter_class = _ADAPTER_REGISTRY[provider_type]
    return adapter_class(config)


class LLMManager:
    """
    Manages multiple LLM adapters.
    
    Usage:
        manager = LLMManager(config)
        response = await manager.chat("Hello!")
        response = await manager.chat("Hello!", provider="vertex")
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with config from the "llm" section.
        
        Expected config format:
        {
            "default": "openai",
            "providers": {
                "openai": { "api_key": "...", "model": "..." },
                "vertex": { "project_id": "...", "model": "..." }
            }
        }
        """
        self.config = config
        self.default_provider = config.get("default", "openai")
        self._adapters: Dict[str, BaseLLMAdapter] = {}
        
        # Initialize adapters
        providers = config.get("providers", {})
        for name, provider_config in providers.items():
            try:
                self._adapters[name] = create_adapter(name, provider_config)
            except Exception as e:
                print(f"Failed to initialize LLM provider {name}: {e}")
    
    def get_adapter(self, provider: Optional[str] = None) -> BaseLLMAdapter:
        """Get an adapter by name, or the default."""
        name = provider or self.default_provider
        
        if name not in self._adapters:
            raise ValueError(f"LLM provider not configured: {name}")
        
        return self._adapters[name]
    
    async def chat(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful assistant.",
        provider: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface.
        
        Args:
            prompt: User message.
            system_prompt: System instruction.
            provider: Which provider to use (default if None).
            **kwargs: Additional options passed to the adapter.
        
        Returns:
            The assistant's response text.
        """
        from .base import Message
        
        adapter = self.get_adapter(provider)
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=prompt)
        ]
        
        response = await adapter.chat(messages, **kwargs)
        return response.content
    
    @property
    def available_providers(self) -> list:
        """List of configured providers."""
        return list(self._adapters.keys())
