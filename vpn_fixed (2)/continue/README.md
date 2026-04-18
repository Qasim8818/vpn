# Continue.dev (RAG) Setup

This folder is for configuration and logs related to the Continue.dev VS Code extension.

## Usage
- Install the Continue extension in VS Code.
- Configure to use local Ollama and nomic-embed-text for embeddings.
- Index your codebase for local RAG.

## Example config.json
```json
{
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  }
}
```

## How to Index Codebase
- In the Continue chat, type `@codebase` to index your local files.
- Data is stored in a local SQLite DB (no cloud).

## Privacy
All code and embeddings are processed locally.
