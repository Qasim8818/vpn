import sys
sys.path.insert(0, "/home/killer123/Desktop/vpn/ollama")
sys.path.insert(0, "/home/killer123/Desktop/vpn/qdrant")
sys.path.insert(0, "/home/killer123/Desktop/vpn/continue")

from ollama_client import OllamaClient
from local_memory import LocalMemory
from local_rag import LocalRAG
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class LocalAgent:
    """
    24/7 Self-Improving Local Agent.
    - Runs entirely locally with no data leakage.
    - Uses Ollama for reasoning, Qdrant for memory, and RAG for codebase context.
    - Chain-of-Thought for human-like reasoning.
    - Persistent memory that learns from interactions.
    """
    
    def __init__(self):
        self.ollama = OllamaClient()
        self.memory = LocalMemory()
        self.rag = LocalRAG()
        self.conversation_history: List[Dict[str, str]] = []
        self.agent_name = "LocalAgent"
        self.version = "1.0.0"
        print(f"✓ {self.agent_name} initialized (v{self.version})")
    
    def health_check(self) -> Dict[str, Any]:
        """Check overall system health."""
        ollama_ok = self.ollama.health_check()
        
        try:
            memory_stats = self.memory.get_collection_stats()
            memory_ok = True
        except:
            memory_ok = False
            memory_stats = {}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_name,
            "ollama_running": ollama_ok,
            "memory_available": memory_ok,
            "memory_stats": memory_stats
        }
    
    def process_query(self, user_input: str, use_codebase: bool = False) -> Dict[str, Any]:
        """
        Process a user query with chain-of-thought reasoning.
        
        Args:
            user_input: The user's question or task
            use_codebase: Whether to include codebase context in the response
        
        Returns:
            Dictionary with thinking, response, and metadata
        """
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build context
        context = self._build_context(user_input, use_codebase)
        
        # Create prompt with chain-of-thought
        prompt = self._create_cot_prompt(user_input, context)
        
        # Generate response
        result = self.ollama.generate(prompt)
        
        if result["success"]:
            response_text = result["response"]
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            
            # Store in memory
            embedding = self.ollama.embed(user_input + " " + response_text[:200])
            self.memory.add_conversation_turn(
                user_input=user_input,
                assistant_response=response_text[:500],
                embedding=embedding
            )
            
            return {
                "success": True,
                "user_input": user_input,
                "response": response_text,
                "model": result.get("model"),
                "timestamp": datetime.now().isoformat(),
                "context_length": len(context)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "user_input": user_input
            }
    
    def _build_context(self, query: str, use_codebase: bool = False) -> str:
        """Build context for the query from memory and optionally codebase."""
        context_parts = []
        
        # Add system context
        context_parts.append("=== SYSTEM CONTEXT ===")
        context_parts.append(f"Agent: {self.agent_name} v{self.version}")
        context_parts.append(f"Time: {datetime.now().isoformat()}")
        context_parts.append("")
        
        # Add relevant memory
        query_embedding = self.ollama.embed(query)
        if query_embedding:
            relevant_facts = self.memory.search(query_embedding, collection="facts", limit=3)
            if relevant_facts:
                context_parts.append("=== RELEVANT FACTS ===")
                for fact in relevant_facts:
                    context_parts.append(f"- {fact['payload'].get('fact', '')}")
                context_parts.append("")
        
        # Add codebase context if requested
        if use_codebase:
            rag_results = self.rag.search_codebase(query_embedding, limit=3)
            if rag_results:
                context_parts.append("=== CODEBASE CONTEXT ===")
                for result in rag_results:
                    context_parts.append(f"File: {result['file_path']}")
                    context_parts.append(f"Language: {result['language']}")
                    context_parts.append(f"Content:\n{result['content'][:300]}...\n")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _create_cot_prompt(self, user_input: str, context: str) -> str:
        """Create a chain-of-thought prompt for reasoning."""
        return f"""You are a highly intelligent local AI agent that thinks step-by-step.

{context}

USER QUERY: {user_input}

Please think through this step-by-step:
1. First, understand what the user is asking
2. Identify any relevant information from context
3. Break down the solution into steps
4. Provide a clear, reasoned answer

RESPONSE:"""
    
    def add_fact(self, fact: str) -> str:
        """Store a fact in persistent memory."""
        embedding = self.ollama.embed(fact)
        fact_id = self.memory.add_fact(fact, embedding=embedding)
        print(f"✓ Stored fact: {fact[:50]}...")
        return fact_id
    
    def add_preference(self, key: str, value: str) -> str:
        """Store a user preference."""
        embedding = self.ollama.embed(f"{key}: {value}")
        pref_id = self.memory.add_preference(key, value, embedding=embedding)
        print(f"✓ Stored preference: {key}={value}")
        return pref_id
    
    def index_codebase(self, root_path: str) -> Dict[str, int]:
        """Index a local codebase for RAG."""
        print(f"Indexing codebase at {root_path}...")
        stats = self.rag.index_directory(
            root_path,
            embedding_func=self.ollama.embed
        )
        print(f"✓ Indexed {stats['indexed']} chunks from {stats['total']} files")
        return stats
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.conversation_history:
            return "No conversations yet."
        
        summary = [f"Conversation Summary ({len(self.conversation_history)} turns):"]
        for i, turn in enumerate(self.conversation_history[-5:], 1):  # Last 5 turns
            role = turn["role"].upper()
            content = turn["content"][:100]
            summary.append(f"{i}. [{role}] {content}...")
        
        return "\n".join(summary)
    
    def show_status(self) -> None:
        """Display system status."""
        health = self.health_check()
        print("\n" + "="*50)
        print(f"🤖 {self.agent_name} Status")
        print("="*50)
        print(f"Version: {self.version}")
        print(f"Ollama: {'✓ Running' if health['ollama_running'] else '✗ Offline'}")
        print(f"Memory: {'✓ Available' if health['memory_available'] else '✗ Unavailable'}")
        print(f"Memory Collections: {len(health['memory_stats'])}")
        
        for col_name, col_stats in health['memory_stats'].items():
            if 'error' not in col_stats:
                print(f"  - {col_name}: {col_stats.get('point_count', 0)} points")
        
        print(f"Conversation Turns: {len(self.conversation_history)}")
        print("="*50 + "\n")
