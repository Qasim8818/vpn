from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime

class LocalMemory:
    """Persistent memory system using Qdrant for local knowledge storage."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.client: Optional[QdrantClient] = None
        self.available = False
        self.collections = {
            "facts": "user_facts",
            "preferences": "user_preferences",
            "code_snippets": "code_snippets",
            "conversations": "conversation_history",
            "learnings": "learned_patterns"
        }
        self.vector_size = 768  # nomic-embed-text output size
        
        self._connect()
    
    def _connect(self):
        """Connect to Qdrant with error handling."""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._initialize_collections()
            self.available = True
            print("Qdrant memory ready")
        except Exception as e:
            print("Qdrant not available:", str(e)[:100])
            print("Start Qdrant: docker run -d -p 6333:6333 qdrant/qdrant")
            print("Continuing without persistent memory")
            self.client = None
            self.available = False
    
    def _initialize_collections(self):
        """Create collections if they don't exist."""
        if self.client is None:
            return
        for collection_name in self.collections.values():
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print("Created collection:", collection_name)
    
    def add_fact(self, fact: str, embedding: Optional[List[float]] = None, category: str = "facts") -> Optional[str]:
        """Store a fact in memory with vector embedding."""
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        fact_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=fact_id,
            vector=embedding,
            payload={
                "fact": fact,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "fact_id": fact_id,
                    "source": "user_input"
                }
            }
        )
        
        self.client.upsert(
            collection_name=self.collections["facts"],
            points=[point]
        )
        return fact_id
    
    def add_preference(self, key: str, value: str, embedding: Optional[List[float]] = None) -> Optional[str]:
        """Store user preferences."""
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        pref_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=pref_id,
            vector=embedding,
            payload={
                "key": key,
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "pref_id": pref_id,
                    "category": "preference"
                }
            }
        )
        
        self.client.upsert(
            collection_name=self.collections["preferences"],
            points=[point]
        )
        return pref_id
    
    def add_code_snippet(self, language: str, code: str, description: str, embedding: Optional[List[float]] = None) -> Optional[str]:
        """Store code snippets for future reference."""
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        snippet_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=snippet_id,
            vector=embedding,
            payload={
                "language": language,
                "code": code,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "snippet_id": snippet_id,
                    "category": "code"
                }
            }
        )
        
        self.client.upsert(
            collection_name=self.collections["code_snippets"],
            points=[point]
        )
        return snippet_id
    
    def search(self, query_embedding: List[float], collection: str = "facts", limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory for relevant information."""
        if self.client is None:
            return []
        collection_name = self.collections.get(collection, self.collections["facts"])
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.5
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            }
            for hit in results
        ]
    
    def add_conversation_turn(self, user_input: str, assistant_response: str, embedding: Optional[List[float]] = None) -> Optional[str]:
        """Store conversation history."""
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        conv_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=conv_id,
            vector=embedding,
            payload={
                "user_input": user_input,
                "assistant_response": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "conversation_id": conv_id,
                    "category": "conversation"
                }
            }
        )
        
        self.client.upsert(
            collection_name=self.collections["conversations"],
            points=[point]
        )
        return conv_id
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections."""
        if self.client is None:
            return {"status": "Qdrant unavailable", "available": False}
        stats = {}
        for collection_name in self.collections.values():
            try:
                info = self.client.get_collection(collection_name)
                stats[collection_name] = {
                    "point_count": info.points_count,
                    "vector_size": self.vector_size
                }
            except Exception:
                stats[collection_name] = {"error": "Collection not found"}
        
        return stats
    
    def clear_collection(self, collection: str):
        """Clear a specific collection."""
        if self.client is None:
            return
        collection_name = self.collections.get(collection)
        if collection_name:
            try:
                self.client.delete_collection(collection_name)
            except:
                pass
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )

