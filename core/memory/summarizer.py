"""
Summarizer - Generate conversation summaries using LLM.
"""

from typing import Any, List, Optional


SUMMARIZE_PROMPT = """请根据以下对话内容，生成一个简洁的摘要，包含：
1. 对话的主要话题
2. 用户可能关心的关键信息
3. 任何值得记住的用户偏好或事实

对话内容：
{conversation}

请用1-3句话总结："""


EXTRACT_FACTS_PROMPT = """从以下对话中提取关于用户的重要信息（如偏好、习惯、个人情况等）。
每条信息用一行表示，最多提取3条最重要的信息。如果没有明确的个人信息，返回"无"。

对话内容：
{conversation}

用户信息："""


class Summarizer:
    """
    Generate conversation summaries and extract facts using LLM.
    """
    
    def __init__(self, llm_manager: Any):
        """
        Initialize summarizer.
        
        Args:
            llm_manager: LLM manager instance for generating summaries
        """
        self.llm_manager = llm_manager
    
    async def summarize(
        self,
        messages: List[dict],
        existing_summary: str = ""
    ) -> str:
        """
        Generate summary of conversation messages.
        
        Args:
            messages: List of message dicts
            existing_summary: Existing summary to incorporate
            
        Returns:
            New summary string
        """
        if not messages:
            return existing_summary
        
        # Format conversation
        conversation = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages
        ])
        
        # Include existing summary if present
        if existing_summary:
            conversation = f"[之前的摘要: {existing_summary}]\n\n{conversation}"
        
        prompt = SUMMARIZE_PROMPT.format(conversation=conversation)
        
        try:
            summary = await self.llm_manager.chat(prompt)
            return summary.strip()
        except Exception as e:
            print(f"Summarization failed: {e}")
            return existing_summary
    
    async def extract_facts(self, messages: List[dict]) -> List[str]:
        """
        Extract user facts from conversation.
        
        Args:
            messages: List of message dicts
            
        Returns:
            List of extracted facts
        """
        if not messages:
            return []
        
        # Format conversation
        conversation = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages
        ])
        
        prompt = EXTRACT_FACTS_PROMPT.format(conversation=conversation)
        
        try:
            response = await self.llm_manager.chat(prompt)
            response = response.strip()
            
            if response == "无" or not response:
                return []
            
            # Parse facts (one per line)
            facts = [
                line.strip().lstrip("•-123456789. ")
                for line in response.split("\n")
                if line.strip() and line.strip() != "无"
            ]
            
            return facts[:3]  # Limit to 3 facts
            
        except Exception as e:
            print(f"Fact extraction failed: {e}")
            return []
