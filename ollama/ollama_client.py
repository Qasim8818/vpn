import requests
import json
from typing import Optional, Dict, Any, List
import time

class OllamaClient:
    """Local LLM client for Ollama with chain-of-thought reasoning."""
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.base_url = f"http://{host}:{port}"
        self.model = "deepseek-r1:14b"
        self.embedding_model = "nomic-embed-text"
    
    def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
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
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "eos_token_id": 100000,
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
