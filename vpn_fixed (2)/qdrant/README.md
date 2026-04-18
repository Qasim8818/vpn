# Qdrant Vector Database Setup

This folder is for configuration and data related to your local Qdrant vector database.

## Usage
- Qdrant is used for fast, local vector search (RAG, memory, embeddings).
- Run via Docker:
  ```sh
  docker run -d -p 6333:6333 qdrant/qdrant
  ```
- Data is persisted in Docker volume by default.

## Example: Python Client
```python
from qdrant_client import QdrantClient
client = QdrantClient(host="localhost", port=6333)
# Use client to create collections, insert vectors, search, etc.
```

## Privacy
All data is stored and queried locally. No cloud access.
