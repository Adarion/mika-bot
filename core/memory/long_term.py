"""
Long-Term Memory - Persistent storage with conversation summaries.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class LongTermMemory:
    """
    SQLite-based persistent memory for user summaries and facts.
    
    Stores:
    - User conversation summaries
    - Important facts about users
    - Conversation metadata
    - User settings (e.g., role preference)
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        """
        Initialize long-term memory.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_summaries (
                    user_id TEXT PRIMARY KEY,
                    summary TEXT,
                    facts TEXT,
                    settings TEXT,
                    updated_at TEXT
                )
            """)
            # Check if settings column exists (migration for existing DB)
            try:
                conn.execute("SELECT settings FROM user_summaries LIMIT 1")
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE user_summaries ADD COLUMN settings TEXT")
                
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (user_id) REFERENCES user_summaries(user_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_user 
                ON conversation_history(user_id)
            """)
            conn.commit()
    
    def get_setting(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get a specific user setting.
        
        Args:
            user_id: Unique user identifier
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT settings FROM user_summaries WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    settings = json.loads(row[0])
                    return settings.get(key, default)
                except json.JSONDecodeError:
                    pass
            return default
            
    def set_setting(self, user_id: str, key: str, value: Any) -> None:
        """
        Set a specific user setting.
        
        Args:
            user_id: Unique user identifier
            key: Setting key
            value: Setting value
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get existing settings first
            cursor = conn.execute(
                "SELECT settings FROM user_summaries WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            settings = {}
            if row and row[0]:
                try:
                    settings = json.loads(row[0])
                except json.JSONDecodeError:
                    pass
            
            # Update setting
            settings[key] = value
            now = datetime.now().isoformat()
            
            conn.execute("""
                INSERT INTO user_summaries (user_id, summary, facts, settings, updated_at)
                VALUES (?, '', '[]', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    settings = excluded.settings,
                    updated_at = excluded.updated_at
            """, (user_id, json.dumps(settings, ensure_ascii=False), now))
            conn.commit()
    
    def get_summary(self, user_id: str) -> str:
        """
        Get user's conversation summary.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Summary string or empty string if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT summary FROM user_summaries WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else ""
    
    def update_summary(self, user_id: str, summary: str) -> None:
        """
        Update user's conversation summary.
        
        Args:
            user_id: Unique user identifier
            summary: New summary text
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_summaries (user_id, summary, facts, settings, updated_at)
                VALUES (?, ?, '[]', '{}', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    summary = excluded.summary,
                    updated_at = excluded.updated_at
            """, (user_id, summary, now))
            conn.commit()
    
    def get_facts(self, user_id: str) -> List[str]:
        """
        Get stored facts about a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of facts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT facts FROM user_summaries WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return []
            return []
    
    def add_fact(self, user_id: str, fact: str) -> None:
        """
        Add a fact about a user.
        
        Args:
            user_id: Unique user identifier
            fact: Fact to add
        """
        facts = self.get_facts(user_id)
        if fact not in facts:
            facts.append(fact)
        
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO user_summaries (user_id, summary, facts, settings, updated_at)
                VALUES (?, '', ?, '{}', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    facts = excluded.facts,
                    updated_at = excluded.updated_at
            """, (user_id, json.dumps(facts, ensure_ascii=False), now))
            conn.commit()
    
    def save_conversation(self, user_id: str, messages: List[Dict[str, str]]) -> None:
        """
        Save conversation messages to history.
        
        Args:
            user_id: Unique user identifier
            messages: List of message dicts with role and content
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for msg in messages:
                conn.execute("""
                    INSERT INTO conversation_history (user_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (user_id, msg["role"], msg["content"], now))
            conn.commit()
    
    def get_recent_history(self, user_id: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Get recent conversation history.
        
        Args:
            user_id: Unique user identifier
            limit: Maximum messages to retrieve
            
        Returns:
            List of message dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT role, content, timestamp FROM conversation_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            
            return [
                {"role": row[0], "content": row[1], "timestamp": row[2]}
                for row in reversed(rows)
            ]
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get all stored information about a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dict with summary, facts, and metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT summary, facts, updated_at FROM user_summaries WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                facts = []
                try:
                    facts = json.loads(row[1]) if row[1] else []
                except json.JSONDecodeError:
                    pass
                    
                return {
                    "summary": row[0] or "",
                    "facts": facts,
                    "updated_at": row[2]
                }
            
            return {"summary": "", "facts": [], "updated_at": None}
    
    def clear_user(self, user_id: str) -> None:
        """Clear all data for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_summaries WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM conversation_history WHERE user_id = ?", (user_id,))
            conn.commit()
