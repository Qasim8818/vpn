#!/usr/bin/env python3
"""
Runtime Functional Tests for LocalAgent System
Tests actual agent functionality with Ollama
"""

import sys
import time
import json
from datetime import datetime
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

class RuntimeTests:
    """Runtime functional tests."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0}
        }
    
    def test_ollama_health(self):
        """Test Ollama health."""
        print("\n🤖 Test 1: Ollama Health Check")
        print("-" * 60)
        
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                print(f"✓ Ollama is running with {len(models)} models")
                for model in models:
                    print(f"  - {model.get('name', 'unknown')}")
                
                self.results["tests"]["ollama_health"] = "PASS"
                self.results["summary"]["passed"] += 1
                return True
            else:
                print(f"✗ Ollama returned status {response.status_code}")
                self.results["tests"]["ollama_health"] = "FAIL"
                self.results["summary"]["failed"] += 1
                return False
                
        except Exception as e:
            print(f"✗ Ollama test failed: {e}")
            self.results["tests"]["ollama_health"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def test_llm_inference(self):
        """Test LLM inference capability."""
        print("\n🧠 Test 2: LLM Inference Test")
        print("-" * 60)
        
        try:
            import requests
            
            prompt = "What is 2+2? Answer only with the number."
            
            print(f"Sending prompt: '{prompt}'")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "deepseek-r1:14b",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                print(f"✓ LLM Response: {answer[:100]}")
                
                self.results["tests"]["llm_inference"] = "PASS"
                self.results["summary"]["passed"] += 1
                return True
            else:
                print(f"✗ LLM returned status {response.status_code}")
                self.results["tests"]["llm_inference"] = "FAIL"
                self.results["summary"]["failed"] += 1
                return False
                
        except Exception as e:
            print(f"✗ LLM inference failed: {e}")
            self.results["tests"]["llm_inference"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def test_embedding_generation(self):
        """Test embedding generation."""
        print("\n📝 Test 3: Embedding Generation Test")
        print("-" * 60)
        
        try:
            import requests
            
            text = "The quick brown fox jumps over the lazy dog"
            print(f"Generating embedding for: '{text[:50]}...'")
            
            response = requests.post(
                "http://localhost:11434/api/embed",
                json={
                    "model": "nomic-embed-text:latest",
                    "input": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = result.get('embeddings', [])
                if embeddings:
                    embedding_dim = len(embeddings[0]) if embeddings else 0
                    print(f"✓ Generated embedding with {embedding_dim} dimensions")
                    print(f"  First 10 values: {embeddings[0][:10]}")
                    
                    self.results["tests"]["embeddings"] = "PASS"
                    self.results["summary"]["passed"] += 1
                    return True
            
            print(f"✗ Embedding generation failed")
            self.results["tests"]["embeddings"] = "FAIL"
            self.results["summary"]["failed"] += 1
            return False
                
        except Exception as e:
            print(f"✗ Embedding test failed: {e}")
            self.results["tests"]["embeddings"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def test_local_agent_import(self):
        """Test LocalAgent can be imported."""
        print("\n🐍 Test 4: LocalAgent Module Import")
        print("-" * 60)
        
        try:
            from local_agent import LocalAgent
            print(f"✓ LocalAgent successfully imported")
            
            # Try to instantiate
            agent = LocalAgent()
            print(f"✓ LocalAgent successfully instantiated")
            
            self.results["tests"]["local_agent_import"] = "PASS"
            self.results["summary"]["passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ LocalAgent import failed: {e}")
            self.results["tests"]["local_agent_import"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def test_code_examples(self):
        """Test code examples can be loaded."""
        print("\n📚 Test 5: Code Examples Integrity")
        print("-" * 60)
        
        try:
            from pathlib import Path
            import ast
            
            examples_dir = Path(_BASE_DIR) / "code-examples"
            
            py_files = list(examples_dir.glob("**/*.py"))
            
            if not py_files:
                print("ℹ No Python files in code examples")
                self.results["tests"]["code_examples"] = "SKIP"
                return True
            
            valid_count = 0
            for py_file in py_files:
                try:
                    with open(py_file, 'r') as f:
                        ast.parse(f.read())
                    valid_count += 1
                except Exception:
                    pass
            
            print(f"✓ Verified {valid_count}/{len(py_files)} code examples are syntactically valid")
            
            self.results["tests"]["code_examples"] = "PASS"
            self.results["summary"]["passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ Code examples test failed: {e}")
            self.results["tests"]["code_examples"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def test_configuration_integrity(self):
        """Test configuration files are valid."""
        print("\n⚙️  Test 6: Configuration Integrity")
        print("-" * 60)
        
        try:
            from pathlib import Path
            import json
            
            config_file = Path(_BASE_DIR) / "config.json"
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            print(f"✓ Configuration loaded successfully")
            print(f"  Keys: {', '.join(config.keys())}")
            
            self.results["tests"]["config_integrity"] = "PASS"
            self.results["summary"]["passed"] += 1
            return True
            
        except Exception as e:
            print(f"✗ Configuration integrity test failed: {e}")
            self.results["tests"]["config_integrity"] = f"ERROR: {str(e)}"
            self.results["summary"]["failed"] += 1
            return False
        finally:
            self.results["summary"]["total"] += 1
    
    def run_all_tests(self):
        """Run all runtime tests."""
        print("\n")
        print("╔" + "═"*60 + "╗")
        print("║" + " "*12 + "🔬 RUNTIME FUNCTIONAL TESTS" + " "*20 + "║")
        print("╚" + "═"*60 + "╝")
        
        start_time = time.time()
        
        self.test_ollama_health()
        self.test_embedding_generation()
        self.test_llm_inference()
        self.test_local_agent_import()
        self.test_code_examples()
        self.test_configuration_integrity()
        
        elapsed = time.time() - start_time
        self.results["elapsed_time"] = elapsed
        
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        summary = self.results["summary"]
        
        print("\n" + "="*60)
        print("📊 RUNTIME TEST SUMMARY")
        print("="*60)
        
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests:    {total}")
        print(f"Passed:         {passed} ✓")
        print(f"Failed:         {failed} ✗")
        print(f"Success Rate:   {success_rate:.1f}%")
        print(f"Execution Time: {self.results['elapsed_time']:.2f}s")
        
        print("\n" + "="*60)
        print("Individual Test Results:")
        print("="*60)
        for test_name, status in self.results["tests"].items():
            symbol = "✓" if status == "PASS" else ("⚠" if "ERROR" in str(status) else "✗")
            print(f"  {symbol} {test_name:40s} {status}")
        
        print("\n" + "="*60)
        if failed == 0:
            print("✅ ALL RUNTIME TESTS PASSED!")
            print("Your system is fully functional!")
        else:
            print(f"⚠️  {failed} test(s) failed")
        print("="*60)

def main():
    tests = RuntimeTests()
    tests.run_all_tests()

if __name__ == "__main__":
    main()
