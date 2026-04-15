import requests
import json
from typing import Optional, Dict, Any, List
import time
import os

class OllamaClient:
    """Local LLM client for Ollama with chain-of-thought reasoning."""
    
    def __init__(self, host: str = None, port: int = None):
        config = self._load_config().get("ollama", {})
        _host = host or config.get("host", "localhost")
        _port = port or config.get("port", 11434)
        self.base_url = f"http://{_host}:{_port}"
        self.model = config.get("model", "deepseek-r1:14b")
        self.embedding_model = config.get("embedding_model", "nomic-embed-text")
        self.temperature = config.get("temperature", 0.7)
        self.top_p = config.get("top_p", 0.9)
        self.thinking_budget = config.get("thinking_budget", 8000)
    
    @staticmethod
    def _load_config() -> dict:
        """Load config.json from project root."""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.json"
        )
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            return {}
    
    def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def generate(self, prompt: str, thinking_budget: int = 8000) -> Dict[str, Any]:
        """Generate response with chain-of-thought reasoning."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "raw": False,
                    "options": {
                        "temperature": self.temperature,
                        "top_p": self.top_p,
                    }
                },
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "done": result.get("done", True),
                    "model": result.get("model", self.model)
                }
            else:
                return {"success": False, "error": f"Status {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def embed(self, text: str) -> Optional[List[float]]:
        """Generate embeddings using nomic-embed-text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.embedding_model,
                    "input": text
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("embeddings", [[]])[0]
            else:
                return None
        
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def batch_embed(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = self.embed(text)
            embeddings.append(embedding)
            time.sleep(0.1)  # Rate limiting
        return embeddings
