from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import json

class LocalMemory:
    """Persistent memory system using Qdrant for local knowledge storage."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collections = {
            "facts": "user_facts",
            "preferences": "user_preferences",
            "code_snippets": "code_snippets",
            "conversations": "conversation_history",
            "learnings": "learned_patterns"
        }
        self.vector_size = 768  # nomic-embed-text output size
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Create collections if they don't exist."""
        for collection_name in self.collections.values():
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection: {collection_name}")
    
    def add_fact(self, fact: str, category: str = "facts", embedding: List[float] = None) -> str:
        """Store a fact in memory with vector embedding."""
        fact_id = str(uuid.uuid4())
        
        if embedding is None:
            embedding = [0.0] * self.vector_size  # Placeholder
        
        point = PointStruct(
            id=uuid.UUID(fact_id).int,
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
    
    def add_preference(self, key: str, value: str, embedding: List[float] = None) -> str:
        """Store user preferences."""
        pref_id = str(uuid.uuid4())
        
        if embedding is None:
            embedding = [0.0] * self.vector_size
        
        point = PointStruct(
            id=uuid.UUID(pref_id).int,
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
    
    def add_code_snippet(self, language: str, code: str, description: str, embedding: List[float] = None) -> str:
        """Store code snippets for future reference."""
        snippet_id = str(uuid.uuid4())
        
        if embedding is None:
            embedding = [0.0] * self.vector_size
        
        point = PointStruct(
            id=uuid.UUID(snippet_id).int,
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
    
    def add_conversation_turn(self, user_input: str, assistant_response: str, embedding: List[float] = None) -> str:
        """Store conversation history."""
        conv_id = str(uuid.uuid4())
        
        if embedding is None:
            embedding = [0.0] * self.vector_size
        
        point = PointStruct(
            id=uuid.UUID(conv_id).int,
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
