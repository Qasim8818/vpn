# Mem0 (Persistent Memory) Setup

This folder is for configuration and scripts related to Mem0, your local persistent memory agent.

## Usage
- Mem0 stores facts, preferences, and history for your agent.
- Uses Qdrant as the vector store and Ollama for LLM/embeddings.

## Example Python Setup
```python
from mem0 import Memory
config = {
    "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
    "llm": {"provider": "ollama", "config": {"model": "deepseek-r1:14b"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text"}}
}
m = Memory.from_config(config)
```

## Privacy
All memory and embeddings are stored and processed locally.

## Note
If Mem0 is not available via pip, clone from the official repo and install manually.
