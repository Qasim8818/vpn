# LocalAgent Critical Bug Fix TODO

## Status: In Progress

### 1. [DONE] Add necessary imports to files
   - qdrant/local_memory.py: from qdrant_client.http import models as qdrant_models
   - continue/local_rag.py: same

### 2. [DONE] Fix recreate_collection → collection_exists + create_collection in qdrant/local_memory.py
   - _initialize_collections()
   - clear_collection()

### 3. [DONE] Fix same in continue/local_rag.py (_initialize_collection)

### 4. [DONE] Fix hash IDs → uuid.UUID.int in qdrant/local_memory.py (4 methods: add_fact, add_preference, add_code_snippet, add_conversation_turn)

### 5. [DONE] Fix hash ID in continue/local_rag.py (_index_file)

### 6. [DONE] Fix embedding dim check in validate.py (384 → 768)

### 7. [DONE] Test: Run python validate.py

### 8. [DONE] Proceed to serious issues (daemon, etc.) if criticals pass

*Updated after each step completed.*

