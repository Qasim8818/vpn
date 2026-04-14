import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import uuid
from datetime import datetime

class LocalRAG:
    """Retrieval-Augmented Generation system using local codebase and documents."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "codebase_index"
        self.vector_size = 384
        self._initialize_collection()
        self.supported_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".md": "markdown",
            ".txt": "text",
            ".sql": "sql",
            ".yaml": "yaml",
            ".json": "json"
        }
    
    def _initialize_collection(self):
        """Create codebase index collection."""
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✓ Created codebase index collection")
    
    def index_directory(self, root_path: str, embedding_func=None) -> Dict[str, int]:
        """Index all code files in a directory."""
        indexed_count = 0
        failed_count = 0
        root_path = Path(root_path)
        
        # Common directories to skip
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
        
        for filepath in root_path.rglob("*"):
            # Skip directories
            if filepath.is_dir():
                if any(skip in filepath.parts for skip in skip_dirs):
                    continue
                continue
            
            # Check file extension
            if filepath.suffix in self.supported_extensions:
                try:
                    indexed_count += self._index_file(filepath, embedding_func)
                except Exception as e:
                    print(f"✗ Failed to index {filepath}: {e}")
                    failed_count += 1
        
        return {
            "indexed": indexed_count,
            "failed": failed_count,
            "total": indexed_count + failed_count
        }
    
    def _index_file(self, filepath: Path, embedding_func=None) -> int:
        """Index a single file by chunking it."""
        language = self.supported_extensions.get(filepath.suffix, "text")
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            return 0
        
        # Split into chunks (e.g., 500 characters per chunk)
        chunk_size = 500
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        indexed_count = 0
        for chunk_idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            
            chunk_id = str(uuid.uuid4())
            embedding = embedding_func(chunk) if embedding_func else [0.0] * self.vector_size
            
            point = PointStruct(
                id=hash(chunk_id) % (2**31),
                vector=embedding,
                payload={
                    "file_path": str(filepath),
                    "language": language,
                    "chunk_index": chunk_idx,
                    "content": chunk[:1000],  # Store first 1000 chars
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "chunk_id": chunk_id,
                        "chunk_size": len(chunk),
                        "relative_path": str(filepath.relative_to(filepath.parent.parent))
                    }
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            indexed_count += 1
        
        return indexed_count
    
    def search_codebase(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search indexed codebase for relevant code."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.5
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "file_path": hit.payload.get("file_path"),
                "language": hit.payload.get("language"),
                "content": hit.payload.get("content"),
                "chunk_index": hit.payload.get("chunk_index")
            }
            for hit in results
        ]
    
    def get_file_context(self, filepath: str, limit: int = 5) -> Optional[str]:
        """Get context from a specific file."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return content[:5000]  # Return first 5000 chars
        except:
            return None
    
    def clear_index(self):
        """Clear the codebase index."""
        self.client.delete_collection(self.collection_name)
        self._initialize_collection()
        print("✓ Codebase index cleared")
