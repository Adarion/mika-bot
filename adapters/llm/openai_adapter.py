"""
OpenAI-compatible LLM Adapter.
Works with OpenAI, DeepSeek, Moonshot, and other compatible APIs.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from .base import BaseLLMAdapter, ChatResponse, Message, StreamChunk


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI-compatible LLM adapter.
    
    Config:
        api_key: API key for the provider.
        base_url: Base URL for the API (optional, defaults to OpenAI).
        model: Model name to use.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsyncOpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self._convert_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
            tool_calls=choice.message.tool_calls if hasattr(choice.message, 'tool_calls') else None
        )
    
    async def stream_chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request."""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self._convert_messages(messages),
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(
                    content=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason
                )
