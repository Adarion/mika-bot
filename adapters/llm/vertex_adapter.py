"""
Google Vertex AI LLM Adapter.
Supports Gemini models via Vertex AI using REST API.
"""

import aiohttp
from typing import Any, AsyncIterator, Dict, List, Optional

from .base import BaseLLMAdapter, ChatResponse, Message, StreamChunk


class VertexAIAdapter(BaseLLMAdapter):
    """
    Google Vertex AI adapter for Gemini models using REST API.
    
    Config:
        project_id: GCP project ID.
        location: GCP region (e.g., "us-central1").
        model: Model name (e.g., "gemini-2.0-flash").
        api_key: API key for authentication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_id = config.get("project_id")
        self.location = config.get("location", "us-central1")
        self.api_key = config.get("api_key")
        
        # Gemini 3 models use global endpoint
        if self.model.startswith("gemini-3"):
            self.base_url = f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/global/publishers/google/models/{self.model}"
        else:
            self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model}"
    
    def _convert_to_gemini_format(self, messages: List[Message]) -> tuple:
        """Convert messages to Gemini format."""
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})
        
        return system_instruction, contents
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """Send a chat completion request to Vertex AI."""
        system_instruction, contents = self._convert_to_gemini_format(messages)
        
        # Build request body
        request_body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            request_body["generationConfig"]["maxOutputTokens"] = max_tokens
        
        if system_instruction:
            request_body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        # Make API request
        url = f"{self.base_url}:generateContent?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=request_body,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Vertex AI API error: {response.status} - {error_text}")
                
                result = await response.json()
        
        # Extract response
        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse Vertex AI response: {result}")
        
        return ChatResponse(
            content=content,
            model=self.model,
            usage={},
            finish_reason="stop"
        )
    
    async def stream_chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Send a streaming chat completion request to Vertex AI."""
        system_instruction, contents = self._convert_to_gemini_format(messages)
        
        request_body = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            request_body["generationConfig"]["maxOutputTokens"] = max_tokens
        
        if system_instruction:
            request_body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        url = f"{self.base_url}:streamGenerateContent?key={self.api_key}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=request_body,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Vertex AI API error: {response.status} - {error_text}")
                
                async for line in response.content:
                    line = line.decode("utf-8").strip()
                    if line:
                        try:
                            import json
                            data = json.loads(line.lstrip("[,"))
                            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            if text:
                                yield StreamChunk(content=text)
                        except:
                            pass
