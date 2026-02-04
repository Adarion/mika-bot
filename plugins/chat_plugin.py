"""
Chat Plugin - Handles general chat messages using LLM with memory support.
"""

from typing import Any, Dict, Optional

from core.event_bus import Event
from core.plugin_manager import BasePlugin
from core.memory import MemoryManager


# 默认角色提示词
DEFAULT_PROMPT = "You are a helpful and friendly assistant."


class ChatPlugin(BasePlugin):
    """
    Chat plugin that responds to messages using an LLM.
    
    Supports conversation memory with:
    - Short-term context (recent messages)
    - Long-term summaries
    - RAG semantic retrieval
    - Role switching with persistence
    
    Config:
        system_prompt: Custom system prompt for the LLM.
        llm_provider: Which LLM provider to use (optional).
        memory: Memory configuration (optional).
    """
    
    memory_manager: Optional[MemoryManager] = None
    
    async def on_load(self) -> None:
        """Register event handlers."""
        self.default_prompt = self.config.get("system_prompt", DEFAULT_PROMPT)
        
        # Per-user system prompts (for role switching)
        self._user_prompts: Dict[str, str] = {}
        
        # Initialize memory manager
        memory_config = self.config.get("memory", {
            "short_term": {"max_messages": 10},
            "long_term": {"summarize_threshold": 20},
            "rag": {"enabled": True, "top_k": 3}
        })
        
        # Memory manager will be fully initialized when llm_manager is available
        self._memory_config = memory_config
        self._llm_manager = None
        
        # Subscribe to events
        self.subscribe("message.received", self.handle_message)
        self.subscribe("role.changed", self.handle_role_change)
        self.subscribe("memory.clear", self.handle_memory_clear)
        
        print(f"ChatPlugin loaded with system prompt: {self.default_prompt[:50]}...")
    
    def _ensure_memory(self, llm_manager: Any) -> None:
        """Ensure memory manager is initialized."""
        if self.memory_manager is None and llm_manager:
            self._llm_manager = llm_manager
            self.memory_manager = MemoryManager(
                config=self._memory_config,
                llm_manager=llm_manager
            )
            print("ChatPlugin: Memory system initialized")
    
    def get_system_prompt(self, user_id: str) -> str:
        """Get system prompt for user (considering role)."""
        # 1. Check in-memory cache
        if user_id in self._user_prompts:
            return self._user_prompts[user_id]
        
        # 2. Check persistent memory
        if self.memory_manager:
            saved_prompt = self.memory_manager.get_setting(user_id, "role_prompt")
            if saved_prompt:
                self._user_prompts[user_id] = saved_prompt
                return saved_prompt
        
        # 3. Default
        return self.default_prompt
    
    async def handle_role_change(self, event: Event) -> None:
        """Handle role change from command plugin."""
        user_id = event.data.get("user_id")
        system_prompt = event.data.get("system_prompt")
        role_name = event.data.get("role_name")
        
        if user_id and system_prompt:
            self._user_prompts[user_id] = system_prompt
            
            # Persist role prompt
            if self.memory_manager:
                self.memory_manager.set_setting(user_id, "role_prompt", system_prompt)
                self.memory_manager.set_setting(user_id, "role_name", role_name)
                # Clear short-term memory when switching roles
                self.memory_manager.short_term.clear(user_id)
            
            print(f"ChatPlugin: Role saved for user {user_id[:20]}...")
    
    async def handle_memory_clear(self, event: Event) -> None:
        """Handle memory clear request."""
        user_id = event.data.get("user_id")
        if user_id and self.memory_manager:
            await self.memory_manager.clear(user_id)
            print(f"ChatPlugin: Memory cleared for user {user_id[:20]}...")
    
    async def handle_message(self, event: Event) -> None:
        """Handle incoming messages."""
        message = event.data.get("message")
        llm_manager = event.data.get("llm_manager")
        
        if not message or not llm_manager:
            return
        
        # Skip if it's a command (starts with /)
        content = message.content.strip()
        if content.startswith("/"):
            return
        
        # Initialize memory if needed
        self._ensure_memory(llm_manager)
        
        # Get user ID
        user_id = f"{message.platform}:{message.author.id}"
        
        try:
            # Add user message to memory
            if self.memory_manager:
                await self.memory_manager.add_message(user_id, "user", content)
            
            # Build context with memory
            context = ""
            if self.memory_manager:
                context = await self.memory_manager.get_context(user_id, content)
            
            # Get user's current system prompt (considers role)
            base_prompt = self.get_system_prompt(user_id)
            system_prompt = base_prompt
            if context:
                system_prompt = f"{base_prompt}\n\n{context}"
            
            # Get LLM response
            provider = self.config.get("llm_provider")
            messages = []
            
            # Use conversation history if available
            if self.memory_manager:
                messages = self.memory_manager.get_messages_for_llm(user_id)
            
            if messages and hasattr(llm_manager, 'chat_with_history'):
                response = await llm_manager.chat_with_history(
                    messages=messages,
                    system_prompt=system_prompt,
                    provider=provider
                )
            else:
                response = await llm_manager.chat(
                    prompt=content,
                    system_prompt=system_prompt,
                    provider=provider
                )
            
            # Add assistant response to memory
            if self.memory_manager:
                await self.memory_manager.add_message(user_id, "assistant", response)
            
            # Smart Bubble Splitting
            # If no code blocks, split by newlines to simulate distinct messages
            final_content = response
            if "```" not in response:
                parts = [p.strip() for p in response.split('\n') if p.strip()]
                if len(parts) > 1:
                    final_content = parts

            # Publish reply event
            await self.publish("message.reply", {
                "original": message,
                "content": final_content
            })
            
        except Exception as e:
            print(f"ChatPlugin error: {e}")
            await self.publish("message.reply", {
                "original": message,
                "content": "抱歉，处理消息时出错了。"
            })
    
    async def on_unload(self) -> None:
        """Cleanup on unload."""
        # Memory is persistent, no cleanup needed
        pass
