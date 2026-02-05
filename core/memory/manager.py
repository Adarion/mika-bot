"""
Memory Manager - Unified interface for all memory systems.
"""

from typing import Any, Dict, List, Optional

from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .rag_memory import RAGMemory
from .summarizer import Summarizer


class MemoryManager:
    """
    Unified memory management system.
    
    Coordinates short-term, long-term, and RAG memory layers
    to provide context-aware conversation memory.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        llm_manager: Any = None
    ):
        """
        Initialize memory manager.
        
        Args:
            config: Memory configuration dict
            llm_manager: LLM manager for summarization
        """
        self.config = config
        self.llm_manager = llm_manager
        
        # Short-term config
        st_config = config.get("short_term", {})
        self.short_term = ShortTermMemory(
            max_messages=st_config.get("max_messages", 10)
        )
        
        # Long-term config
        lt_config = config.get("long_term", {})
        self.long_term = LongTermMemory(
            db_path=lt_config.get("db_path", "data/memory.db")
        )
        self.summarize_threshold = lt_config.get("summarize_threshold", 20)
        
        # RAG config
        rag_config = config.get("rag", {})
        self.rag_enabled = rag_config.get("enabled", True)
        self.rag_top_k = rag_config.get("top_k", 3)
        
        if self.rag_enabled:
            self.rag = RAGMemory(
                storage_path=rag_config.get("storage_path", "data/chroma"),
                collection_name=rag_config.get("collection", "conversations")
            )
        else:
            self.rag = None
        
        # Summarizer
        self.summarizer = Summarizer(llm_manager) if llm_manager else None
        
        # Track message counts for summarization
        self._message_counts: Dict[str, int] = {}
    
    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add a message to memory.
        
        Args:
            user_id: Unique user identifier
            role: Message role ("user" or "assistant")
            content: Message content
        """
        # Add to short-term
        self.short_term.add(user_id, role, content)
        
        # Index to RAG immediately for semantic search
        # This ensures messages are searchable even before summarization
        if self.rag and self.rag.enabled and content.strip():
            recent = self.short_term.get_for_llm(user_id, limit=2)  # Get last 2 messages
            if len(recent) >= 2:  # Index user-assistant pairs
                self.rag.add_conversation(user_id, recent, chunk_size=2)
        
        # Track for summarization
        self._message_counts[user_id] = self._message_counts.get(user_id, 0) + 1
        
        # Check if summarization needed
        if self._should_summarize(user_id):
            await self._perform_summarization(user_id)
    
    def _should_summarize(self, user_id: str) -> bool:
        """Check if we should summarize the conversation."""
        count = self._message_counts.get(user_id, 0)
        # Summarize every 5 messages after reaching minimum threshold
        # This ensures facts are extracted before short-term memory drops them
        min_threshold = min(self.summarize_threshold, 10)
        return (
            count >= min_threshold 
            and self.summarizer is not None
            and count % 5 == 0  # Every 5 messages
        )
    
    async def _perform_summarization(self, user_id: str) -> None:
        """Perform conversation summarization."""
        if not self.summarizer:
            return
        
        try:
            # Get messages to summarize
            messages = self.short_term.get_for_llm(user_id)
            if len(messages) < 4:
                return
            
            # Get existing summary
            existing = self.long_term.get_summary(user_id)
            
            # Generate new summary
            new_summary = await self.summarizer.summarize(messages, existing)
            self.long_term.update_summary(user_id, new_summary)
            
            # Extract and save facts
            facts = await self.summarizer.extract_facts(messages)
            for fact in facts:
                self.long_term.add_fact(user_id, fact)
            
            # Index in RAG
            if self.rag and self.rag.enabled:
                self.rag.add_conversation(user_id, messages)
            
            # Save to history
            self.long_term.save_conversation(user_id, messages)
            
        except Exception as e:
            print(f"Summarization error: {e}")
    
    async def get_context(
        self,
        user_id: str,
        query: str = "",
        include_rag: bool = True
    ) -> str:
        """
        Get assembled context for LLM.
        
        Args:
            user_id: Unique user identifier
            query: Current query for RAG search
            include_rag: Whether to include RAG results
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # 1. Long-term summary and facts
        user_info = self.long_term.get_user_info(user_id)
        if user_info["summary"]:
            parts.append(f"[用户背景]\n{user_info['summary']}")
        if user_info["facts"]:
            facts_str = "\n".join(f"- {f}" for f in user_info["facts"])
            parts.append(f"[已知信息]\n{facts_str}")
        
        # 2. RAG search results
        if include_rag and self.rag and self.rag.enabled and query:
            rag_context = self.rag.search_formatted(user_id, query, self.rag_top_k)
            if rag_context:
                parts.append(rag_context)
        
        # 3. Recent conversation (short-term)
        recent = self.short_term.get_formatted(user_id)
        if recent:
            parts.append(f"[最近对话]\n{recent}")
        
        return "\n\n".join(parts) if parts else ""
    
    def get_messages_for_llm(self, user_id: str) -> List[dict]:
        """
        Get messages formatted for LLM API call.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of message dicts
        """
        return self.short_term.get_for_llm(user_id)
    
    async def clear(self, user_id: str) -> None:
        """
        Clear all memory for a user.
        
        Args:
            user_id: Unique user identifier
        """
        self.short_term.clear(user_id)
        self.long_term.clear_user(user_id)
        if self.rag:
            self.rag.delete_user(user_id)
        self._message_counts.pop(user_id, None)
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get memory statistics for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dict with stats
        """
        return {
            "short_term_count": self.short_term.count(user_id),
            "long_term_summary": bool(self.long_term.get_summary(user_id)),
            "facts_count": len(self.long_term.get_facts(user_id)),
            "rag_count": self.rag.count(user_id) if self.rag else 0,
            "total_messages": self._message_counts.get(user_id, 0)
        }

    def get_setting(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get a user setting."""
        return self.long_term.get_setting(user_id, key, default)

    def set_setting(self, user_id: str, key: str, value: Any) -> None:
        """Set a user setting."""
        self.long_term.set_setting(user_id, key, value)
