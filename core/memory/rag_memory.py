"""
RAG Memory - Vector-based semantic memory using Chroma.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class RAGMemory:
    """
    Vector database memory for semantic retrieval.
    
    Uses Chroma for local vector storage and similarity search.
    Falls back gracefully if Chroma is not installed.
    """
    
    def __init__(
        self,
        storage_path: str = "data/chroma",
        collection_name: str = "conversations",
        embedding_function: Optional[Any] = None
    ):
        """
        Initialize RAG memory.
        
        Args:
            storage_path: Path to store Chroma data
            collection_name: Name of the collection
            embedding_function: Custom embedding function (optional)
        """
        self.enabled = CHROMA_AVAILABLE
        self.storage_path = Path(storage_path)
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        
        if self.enabled:
            self._init_chroma(embedding_function)
    
    def _init_chroma(self, embedding_function: Optional[Any] = None) -> None:
        """Initialize Chroma client and collection."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=str(self.storage_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Use default embedding function if none provided
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            
        except Exception as e:
            print(f"Failed to initialize Chroma: {e}")
            self.enabled = False
    
    def _generate_id(self, user_id: str, content: str) -> str:
        """Generate unique ID for a document."""
        hash_input = f"{user_id}:{content}:{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def add(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Add a conversation snippet to vector store.
        
        Args:
            user_id: Unique user identifier
            content: Text content to index
            metadata: Optional metadata
            
        Returns:
            Document ID or None if failed
        """
        if not self.enabled or not content.strip():
            return None
        
        try:
            doc_id = self._generate_id(user_id, content)
            
            doc_metadata = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            self._collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            return doc_id
            
        except Exception as e:
            print(f"Failed to add to RAG memory: {e}")
            return None
    
    def add_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, str]],
        chunk_size: int = 3
    ) -> List[str]:
        """
        Add conversation messages in chunks.
        
        Args:
            user_id: Unique user identifier
            messages: List of message dicts
            chunk_size: Number of messages per chunk
            
        Returns:
            List of document IDs
        """
        if not self.enabled or not messages:
            return []
        
        doc_ids = []
        
        # Create overlapping chunks
        for i in range(0, len(messages), max(1, chunk_size - 1)):
            chunk = messages[i:i + chunk_size]
            if not chunk:
                continue
                
            # Format chunk as conversation
            content = "\n".join([
                f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
                for m in chunk
            ])
            
            doc_id = self.add(user_id, content, {"chunk_index": i})
            if doc_id:
                doc_ids.append(doc_id)
        
        return doc_ids
    
    def search(
        self,
        user_id: str,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar memories.
        
        Args:
            user_id: Unique user identifier (for filtering)
            query: Search query
            top_k: Number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of matching documents with scores
        """
        if not self.enabled or not query.strip():
            return []
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": user_id} if user_id else None,
                include=["documents", "metadatas", "distances"]
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            # Convert distance to similarity score (cosine)
            formatted = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                score = 1 - (dist / 2)  # Convert cosine distance to similarity
                if score >= min_score:
                    formatted.append({
                        "content": doc,
                        "metadata": meta,
                        "score": score
                    })
            
            return formatted
            
        except Exception as e:
            print(f"RAG search failed: {e}")
            return []
    
    def search_formatted(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> str:
        """
        Search and format results as context string.
        
        Args:
            user_id: Unique user identifier
            query: Search query
            top_k: Number of results
            
        Returns:
            Formatted context string
        """
        results = self.search(user_id, query, top_k)
        
        if not results:
            return ""
        
        lines = ["[相关历史记忆]"]
        for i, r in enumerate(results, 1):
            lines.append(f"记忆{i}:\n{r['content']}")
        
        return "\n\n".join(lines)
    
    def delete_user(self, user_id: str) -> int:
        """
        Delete all memories for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Number of deleted documents
        """
        if not self.enabled:
            return 0
        
        try:
            # Get all IDs for user
            results = self._collection.get(
                where={"user_id": user_id},
                include=[]
            )
            
            ids = results.get("ids", [])
            if ids:
                self._collection.delete(ids=ids)
            
            return len(ids)
            
        except Exception as e:
            print(f"Failed to delete user memories: {e}")
            return 0
    
    def count(self, user_id: Optional[str] = None) -> int:
        """Get total document count."""
        if not self.enabled:
            return 0
        
        try:
            if user_id:
                results = self._collection.get(
                    where={"user_id": user_id},
                    include=[]
                )
                return len(results.get("ids", []))
            return self._collection.count()
        except:
            return 0
