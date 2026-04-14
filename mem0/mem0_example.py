from mem0 import Memory

config = {
    "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
    "llm": {"provider": "ollama", "config": {"model": "deepseek-r1:14b"}},
    "embedder": {"provider": "ollama", "config": {"model": "nomic-embed-text"}}
}

m = Memory.from_config(config)

# Example: Store a fact
m.add_fact("User prefers Python 3.12 for backend projects.")

# Example: Retrieve memory
results = m.search("What Python version do I use?")
print(results)
