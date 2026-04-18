# Ollama Local LLM Setup

This folder is for configuration and logs related to your local Ollama LLM server.

## Usage
- Ollama is installed and running locally.
- DeepSeek-R1:14b and nomic-embed-text models are pulled.
- To run as a service: `ollama serve`
- To interact: `ollama run deepseek-r1:14b`

## Example Command
```
ollama run deepseek-r1:14b --prompt "Write a Python function to reverse a string."
```

## Privacy
All inference is local. No data leaves your machine.
