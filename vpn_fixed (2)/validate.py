#!/usr/bin/env python3
"""
Comprehensive system test and validation for LocalAgent.
Verifies all components are working correctly.
"""

import sys
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

from local_agent import LocalAgent
import json
import time

class SystemValidator:
    """Validate all LocalAgent components."""
    
    def __init__(self):
        self.results = {
            "test_time": None,
            "tests": {},
            "summary": {"passed": 0, "failed": 0}
        }
    
    def test_ollama_health(self) -> bool:
        """Test Ollama LLM availability."""
        print("Testing Ollama LLM...")
        try:
            agent = LocalAgent()
            is_healthy = agent.ollama.health_check()
            
            if is_healthy:
                print("  ✓ Ollama is running and accessible")
                self.results["tests"]["ollama"] = "PASS"
                return True
            else:
                print("  ✗ Ollama is not responding")
                self.results["tests"]["ollama"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ Ollama test failed: {e}")
            self.results["tests"]["ollama"] = f"ERROR: {str(e)}"
            return False
    
    def test_qdrant_connectivity(self) -> bool:
        """Test Qdrant vector database."""
        print("Testing Qdrant Vector Database...")
        try:
            agent = LocalAgent()
            stats = agent.memory.get_collection_stats()
            
            if stats:
                print(f"  ✓ Qdrant connected with {len(stats)} collections")
                for col_name, col_stats in stats.items():
                    if 'error' not in col_stats:
                        print(f"    - {col_name}: {col_stats.get('point_count', 0)} items")
                self.results["tests"]["qdrant"] = "PASS"
                return True
            else:
                print("  ✗ Qdrant collections not accessible")
                self.results["tests"]["qdrant"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ Qdrant test failed: {e}")
            self.results["tests"]["qdrant"] = f"ERROR: {str(e)}"
            return False
    
    def test_embedding_generation(self) -> bool:
        """Test embedding generation."""
        print("Testing Embedding Generation...")
        try:
            agent = LocalAgent()
            test_text = "This is a test string for embedding"
            embedding = agent.ollama.embed(test_text)
            
            if embedding and len(embedding) == 768:
                print(f"  ✓ Generated embedding with {len(embedding)} dimensions")
                self.results["tests"]["embeddings"] = "PASS"
                return True
            else:
                print(f"  ✗ Embedding generation failed or wrong size")
                self.results["tests"]["embeddings"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ Embedding test failed: {e}")
            self.results["tests"]["embeddings"] = f"ERROR: {str(e)}"
            return False
    
    def test_memory_operations(self) -> bool:
        """Test memory storage and retrieval."""
        print("Testing Memory Operations...")
        try:
            agent = LocalAgent()
            
            # Test storing a fact
            test_fact = "Test fact: System validation in progress"
            fact_id = agent.add_fact(test_fact)
            
            print(f"  ✓ Stored fact with ID: {fact_id}")
            
            # Test storing a preference
            pref_id = agent.add_preference("test_key", "test_value")
            print(f"  ✓ Stored preference with ID: {pref_id}")
            
            self.results["tests"]["memory"] = "PASS"
            return True
        except Exception as e:
            print(f"  ✗ Memory test failed: {e}")
            self.results["tests"]["memory"] = f"ERROR: {str(e)}"
            return False
    
    def test_query_generation(self) -> bool:
        """Test query processing with reasoning."""
        print("Testing Query Generation...")
        try:
            agent = LocalAgent()
            
            test_query = "What is 2+2?"
            print(f"  Processing query: '{test_query}'")
            
            result = agent.process_query(test_query)
            
            if result["success"]:
                response_preview = result["response"][:100] + "..."
                print(f"  ✓ Query processed successfully")
                print(f"    Response: {response_preview}")
                self.results["tests"]["query_generation"] = "PASS"
                return True
            else:
                print(f"  ✗ Query processing failed: {result.get('error')}")
                self.results["tests"]["query_generation"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ Query test failed: {e}")
            self.results["tests"]["query_generation"] = f"ERROR: {str(e)}"
            return False
    
    def test_rag_indexing(self) -> bool:
        """Test RAG codebase indexing."""
        print("Testing RAG Codebase Indexing...")
        try:
            agent = LocalAgent()
            
            # Index the current directory
            stats = agent.index_codebase(_BASE_DIR)
            
            if stats["indexed"] > 0:
                print(f"  ✓ Indexed {stats['indexed']} chunks from {stats['total']} files")
                self.results["tests"]["rag"] = "PASS"
                return True
            else:
                print(f"  ✗ RAG indexing returned no results")
                self.results["tests"]["rag"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ RAG test failed: {e}")
            self.results["tests"]["rag"] = f"ERROR: {str(e)}"
            return False
    
    def test_conversation_history(self) -> bool:
        """Test conversation history tracking."""
        print("Testing Conversation History...")
        try:
            agent = LocalAgent()
            
            # Process a query
            agent.process_query("Test query 1")
            agent.process_query("Test query 2")
            
            history_len = len(agent.conversation_history)
            
            if history_len >= 4:  # 2 queries + 2 responses
                print(f"  ✓ Conversation history tracked ({history_len} turns)")
                summary = agent.get_conversation_summary()
                print(f"    Sample: {summary[:100]}...")
                self.results["tests"]["history"] = "PASS"
                return True
            else:
                print(f"  ✗ Conversation history not tracking properly")
                self.results["tests"]["history"] = "FAIL"
                return False
        except Exception as e:
            print(f"  ✗ History test failed: {e}")
            self.results["tests"]["history"] = f"ERROR: {str(e)}"
            return False
    
    def run_all_tests(self) -> dict:
        """Run all validation tests."""
        print("\n" + "="*60)
        print("🧪 LocalAgent System Validation")
        print("="*60 + "\n")
        
        start_time = time.time()
        
        tests = [
            self.test_ollama_health,
            self.test_qdrant_connectivity,
            self.test_embedding_generation,
            self.test_memory_operations,
            self.test_query_generation,
            self.test_rag_indexing,
            self.test_conversation_history
        ]
        
        for test_func in tests:
            try:
                passed = test_func()
                if passed:
                    self.results["summary"]["passed"] += 1
                else:
                    self.results["summary"]["failed"] += 1
            except Exception as e:
                print(f"\n❌ Test {test_func.__name__} crashed: {e}")
                self.results["summary"]["failed"] += 1
            print()
        
        self.results["test_time"] = time.time() - start_time
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        total = self.results["summary"]["passed"] + self.results["summary"]["failed"]
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        
        print("="*60)
        print("📊 Test Summary")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        print(f"Execution Time: {self.results['test_time']:.2f}s")
        print("="*60)
        
        if failed == 0:
            print("\n✅ ALL TESTS PASSED!")
            print("Your LocalAgent system is ready for use!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Check output above.")
        
        print("\nNext steps:")
        print("  Interactive:  python3 agent_cli.py")
        print("  Daemon:       python3 agent_daemon.py")
        print("  Examples:     python3 examples.py")

def main():
    validator = SystemValidator()
    validator.run_all_tests()
    validator.print_summary()

if __name__ == "__main__":
    main()
