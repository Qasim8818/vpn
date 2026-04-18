from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional, Any
import uuid
import json
import os
from datetime import datetime


def _load_config() -> dict:
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config.json"
    )
    try:
        with open(config_path) as f:
            return json.load(f)
    except Exception:
        return {}


class LocalMemory:
    """Persistent memory system using Qdrant for local knowledge storage."""

    def __init__(self, host: str = None, port: int = None):
        config = _load_config().get("qdrant", {})
        self.host = host or config.get("host", "localhost")
        self.port = port or config.get("port", 6333)
        self.client: Optional[QdrantClient] = None
        self.available = False
        self.collections = {
            "facts": "user_facts",
            "preferences": "user_preferences",
            "code_snippets": "code_snippets",
            "conversations": "conversation_history",
            "learnings": "learned_patterns"
        }
        self.vector_size = config.get("vector_size", 768)
        self._connect()

    def _connect(self):
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
        if self.client is None:
            return
        for collection_name in self.collections.values():
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
                print("Created collection:", collection_name)

    # ── WRITE OPERATIONS ──────────────────────────────────────────────────────

    def add_fact(self, fact: str, embedding: Optional[List[float]] = None,
                 category: str = "facts") -> Optional[str]:
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        fact_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collections["facts"],
            points=[PointStruct(
                id=fact_id, vector=embedding,
                payload={"fact": fact, "category": category,
                         "timestamp": datetime.now().isoformat(),
                         "metadata": {"fact_id": fact_id, "source": "user_input"}}
            )]
        )
        return fact_id

    def store_fact(self, fact: str, embedding: Optional[List[float]] = None) -> Optional[str]:
        """Alias for add_fact."""
        return self.add_fact(fact, embedding)

    def add_preference(self, key: str, value: str,
                       embedding: Optional[List[float]] = None) -> Optional[str]:
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        pref_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collections["preferences"],
            points=[PointStruct(
                id=pref_id, vector=embedding,
                payload={"key": key, "value": value,
                         "timestamp": datetime.now().isoformat(),
                         "metadata": {"pref_id": pref_id, "category": "preference"}}
            )]
        )
        return pref_id

    def store_preference(self, key: str, value: str,
                         embedding: Optional[List[float]] = None) -> Optional[str]:
        """Alias for add_preference."""
        return self.add_preference(key, value, embedding)

    def add_code_snippet(self, language: str, code: str, description: str,
                         embedding: Optional[List[float]] = None) -> Optional[str]:
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        snippet_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collections["code_snippets"],
            points=[PointStruct(
                id=snippet_id, vector=embedding,
                payload={"language": language, "code": code, "description": description,
                         "timestamp": datetime.now().isoformat(),
                         "metadata": {"snippet_id": snippet_id, "category": "code"}}
            )]
        )
        return snippet_id

    def add_conversation_turn(self, user_input: str, assistant_response: str,
                              embedding: Optional[List[float]] = None) -> Optional[str]:
        if self.client is None:
            return None
        if embedding is None:
            embedding = [0.0] * self.vector_size
        conv_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collections["conversations"],
            points=[PointStruct(
                id=conv_id, vector=embedding,
                payload={"user_input": user_input, "assistant_response": assistant_response,
                         "timestamp": datetime.now().isoformat(),
                         "metadata": {"conversation_id": conv_id, "category": "conversation"}}
            )]
        )
        return conv_id

    # ── READ OPERATIONS ───────────────────────────────────────────────────────

    def search(self, query_embedding: List[float], collection: str = "facts",
               limit: int = 5) -> List[Dict[str, Any]]:
        if self.client is None:
            return []
        collection_name = self.collections.get(collection, self.collections["facts"])
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.5
        )
        return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in results]

    def retrieve_by_id(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory item by its ID."""
        if self.client is None:
            return None
        collection_name = self.collections.get(collection)
        if not collection_name:
            print(f"Unknown collection: {collection}. Valid: {list(self.collections.keys())}")
            return None
        try:
            results = self.client.retrieve(collection_name=collection_name, ids=[item_id])
            if results:
                point = results[0]
                return {"id": str(point.id), "payload": point.payload}
            return None
        except Exception as e:
            print(f"retrieve_by_id error: {e}")
            return None

    def get_all_facts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return all stored facts up to limit."""
        if self.client is None:
            return []
        try:
            results, _ = self.client.scroll(
                collection_name=self.collections["facts"],
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            return [{"id": str(point.id), "payload": point.payload} for point in results]
        except Exception as e:
            print(f"get_all_facts error: {e}")
            return []

    def forget_memory(self, collection: str, item_id: str) -> bool:
        """Delete a specific memory item by ID. Returns True on success."""
        if self.client is None:
            return False
        collection_name = self.collections.get(collection)
        if not collection_name:
            print(f"Unknown collection: {collection}. Valid: {list(self.collections.keys())}")
            return False
        try:
            self.client.delete(collection_name=collection_name, points_selector=[item_id])
            return True
        except Exception as e:
            print(f"forget_memory error: {e}")
            return False

    # ── ADMIN OPERATIONS ──────────────────────────────────────────────────────

    def get_collection_stats(self) -> Dict[str, Any]:
        if self.client is None:
            return {"status": "Qdrant unavailable", "available": False}
        stats = {}
        for collection_name in self.collections.values():
            try:
                info = self.client.get_collection(collection_name)
                stats[collection_name] = {"point_count": info.points_count,
                                          "vector_size": self.vector_size}
            except Exception:
                stats[collection_name] = {"error": "Collection not found"}
        return stats

    def clear_collection(self, collection: str):
        if self.client is None:
            return
        collection_name = self.collections.get(collection)
        if collection_name:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
                )
