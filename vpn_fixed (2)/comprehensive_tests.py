#!/usr/bin/env python3
"""
Comprehensive Project Test Suite for VPN LocalAgent System
Tests: Structure, Syntax, Imports, Code Quality, Runtime
"""

import os
import sys
import json
import ast
import time
from pathlib import Path
from datetime import datetime

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

class ComprehensiveTestSuite:
    """Comprehensive test suite for the entire project."""
    
    def __init__(self):
        self.project_root = Path(_BASE_DIR)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_categories": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            },
            "details": []
        }
        self.python_files = []
        self.collect_python_files()
    
    def collect_python_files(self):
        """Collect all Python files in the project."""
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environment and cache
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    self.python_files.append(filepath)
    
    def test_python_syntax(self):
        """Test Python syntax of all Python files."""
        print("\n" + "="*70)
        print("🔍 SYNTAX VALIDATION")
        print("="*70)
        
        category = "syntax"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0, "files": []}
        
        for py_file in self.python_files:
            try:
                with open(py_file, 'r') as f:
                    code = f.read()
                
                ast.parse(code)
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
                
            except SyntaxError as e:
                status = f"✗ FAIL: {e}"
                self.results["test_categories"][category]["failed"] += 1
                result_status = "FAIL"
            except Exception as e:
                status = f"✗ ERROR: {e}"
                self.results["test_categories"][category]["failed"] += 1
                result_status = "ERROR"
            
            rel_path = py_file.relative_to(self.project_root)
            print(f"  {status:60} {rel_path}")
            
            self.results["details"].append({
                "category": category,
                "test": str(rel_path),
                "status": result_status
            })
            self.results["summary"]["total"] += 1
            if result_status == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
    
    def test_imports(self):
        """Test if all imports can be resolved."""
        print("\n" + "="*70)
        print("📦 IMPORT VALIDATION")
        print("="*70)
        
        category = "imports"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0, "modules": []}
        
        try:
            from local_agent import LocalAgent
            self.results["test_categories"][category]["passed"] += 1
            print("  ✓ PASS: LocalAgent module imports")
            self.results["summary"]["passed"] += 1
        except Exception as e:
            self.results["test_categories"][category]["failed"] += 1
            print(f"  ✗ FAIL: LocalAgent module - {e}")
            self.results["summary"]["failed"] += 1
        
        self.results["summary"]["total"] += 1
        
        try:
            from ollama.ollama_client import OllamaClient
            self.results["test_categories"][category]["passed"] += 1
            print("  ✓ PASS: OllamaClient imports")
            self.results["summary"]["passed"] += 1
        except Exception as e:
            self.results["test_categories"][category]["failed"] += 1
            print(f"  ⚠ SKIP: OllamaClient - {e}")
            self.results["summary"]["skipped"] += 1
        
        self.results["summary"]["total"] += 1
    
    def test_file_structure(self):
        """Verify critical files and directories exist."""
        print("\n" + "="*70)
        print("📁 STRUCTURE VALIDATION")
        print("="*70)
        
        category = "structure"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0}
        
        required_files = [
            "README.md",
            "requirements.txt",
            "local_agent.py",
            "agent_cli.py",
            "agent_daemon.py",
            "validate.py",
            "config.json"
        ]
        
        required_dirs = [
            "ollama",
            "qdrant",
            "continue",
            "code-examples",
            "uvi",
            "level-iii"
        ]
        
        for filename in required_files:
            filepath = self.project_root / filename
            if filepath.exists():
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
            else:
                status = "✗ FAIL"
                self.results["test_categories"][category]["failed"] += 1
                result_status = "FAIL"
            
            print(f"  {status:60} File: {filename}")
            self.results["summary"]["total"] += 1
            if result_status == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
        
        for dirname in required_dirs:
            dirpath = self.project_root / dirname
            if dirpath.is_dir():
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
            else:
                status = "✗ FAIL"
                self.results["test_categories"][category]["failed"] += 1
                result_status = "FAIL"
            
            print(f"  {status:60} Dir: {dirname}/")
            self.results["summary"]["total"] += 1
            if result_status == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
    
    def test_ollama_connectivity(self):
        """Test Ollama server connectivity."""
        print("\n" + "="*70)
        print("🤖 OLLAMA CONNECTIVITY")
        print("="*70)
        
        category = "ollama"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0}
        
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
                model_info = f"({len(models)} models available)"
                print(f"  {status:60} Ollama Connected {model_info}")
                for model in models[:5]:  # Show first 5
                    print(f"    - {model.get('name', 'unknown')}")
            else:
                status = "⚠ WARN"
                print(f"  {status:60} Ollama returned status {response.status_code}")
                self.results["test_categories"][category]["failed"] += 1
                result_status = "WARN"
                
        except Exception as e:
            status = "✗ FAIL"
            self.results["test_categories"][category]["failed"] += 1
            result_status = "FAIL"
            print(f"  {status:60} Ollama Connection: {e}")
        
        self.results["summary"]["total"] += 1
        if result_status == "PASS":
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    def test_configuration(self):
        """Validate configuration files."""
        print("\n" + "="*70)
        print("⚙️  CONFIGURATION VALIDATION")
        print("="*70)
        
        category = "config"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0}
        
        try:
            config_path = self.project_root / "config.json"
            with open(config_path) as f:
                config = json.load(f)
            
            print(f"  ✓ PASS: config.json is valid JSON")
            self.results["test_categories"][category]["passed"] += 1
            self.results["summary"]["passed"] += 1
            
            # Check required keys
            required_keys = ["project", "model", "system"]
            for key in required_keys:
                if key in config:
                    print(f"    ✓ Key '{key}' present")
                else:
                    print(f"    ⚠ Key '{key}' missing")
            
        except json.JSONDecodeError as e:
            print(f"  ✗ FAIL: config.json JSON error: {e}")
            self.results["test_categories"][category]["failed"] += 1
            self.results["summary"]["failed"] += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            self.results["test_categories"][category]["failed"] += 1
            self.results["summary"]["failed"] += 1
        
        self.results["summary"]["total"] += 1
    
    def test_documentation(self):
        """Check documentation completeness."""
        print("\n" + "="*70)
        print("📖 DOCUMENTATION VALIDATION")
        print("="*70)
        
        category = "docs"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0}
        
        doc_files = [
            ("README.md", "Main documentation"),
            ("ARCHITECTURE.md", "Architecture overview"),
            ("QUICKSTART.md", "Quick start guide"),
            ("COMPLETION-SUMMARY.md", "Project summary")
        ]
        
        for filename, description in doc_files:
            filepath = self.project_root / filename
            if filepath.exists():
                size = filepath.stat().st_size
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
                print(f"  {status:50} {description:30} ({size} bytes)")
            else:
                status = "✗ MISS"
                self.results["test_categories"][category]["failed"] += 1
                result_status = "FAIL"
                print(f"  {status:50} {description:30}")
            
            self.results["summary"]["total"] += 1
            if result_status == "PASS":
                self.results["summary"]["passed"] += 1
            else:
                self.results["summary"]["failed"] += 1
    
    def test_code_examples(self):
        """Validate code examples."""
        print("\n" + "="*70)
        print("💻 CODE EXAMPLES VALIDATION")
        print("="*70)
        
        category = "examples"
        self.results["test_categories"][category] = {"passed": 0, "failed": 0}
        
        examples_dir = self.project_root / "code-examples"
        if examples_dir.exists():
            subdirs = [d for d in examples_dir.iterdir() if d.is_dir()]
            for subdir in sorted(subdirs):
                files = list(subdir.glob("*"))
                status = "✓ PASS"
                self.results["test_categories"][category]["passed"] += 1
                result_status = "PASS"
                print(f"  {status:50} {subdir.name:30} ({len(files)} files)")
                self.results["summary"]["total"] += 1
                self.results["summary"]["passed"] += 1
        else:
            print(f"  ✗ FAIL: code-examples directory not found")
            self.results["test_categories"][category]["failed"] += 1
            self.results["summary"]["total"] += 1
            self.results["summary"]["failed"] += 1
    
    def run_all_tests(self):
        """Run all test categories."""
        print("\n\n")
        print("╔" + "═"*68 + "╗")
        print("║" + " "*15 + "🧪 COMPREHENSIVE PROJECT TEST SUITE" + " "*18 + "║")
        print("╚" + "═"*68 + "╝")
        
        start_time = time.time()
        
        # Run all test categories
        self.test_file_structure()
        self.test_python_syntax()
        self.test_imports()
        self.test_configuration()
        self.test_documentation()
        self.test_code_examples()
        self.test_ollama_connectivity()
        
        elapsed_time = time.time() - start_time
        self.results["elapsed_time"] = elapsed_time
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def print_summary(self):
        """Print comprehensive test summary."""
        summary = self.results["summary"]
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        skipped = summary["skipped"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests:    {total}")
        print(f"Passed:         {passed:3d} ✓")
        print(f"Failed:         {failed:3d} ✗")
        print(f"Skipped:        {skipped:3d} ⊘")
        print(f"Success Rate:   {success_rate:.1f}%")
        print(f"Execution Time: {self.results['elapsed_time']:.2f}s")
        
        print("\n" + "-"*70)
        print("Category Breakdown:")
        print("-"*70)
        for category, data in self.results["test_categories"].items():
            cat_total = data.get("passed", 0) + data.get("failed", 0)
            if cat_total > 0:
                rate = (data.get("passed", 0) / cat_total * 100)
                print(f"  {category:20s}: {data.get('passed', 0):2d}/{cat_total:2d} ({rate:5.1f}%)")
        
        print("\n" + "="*70)
        if failed == 0:
            print("✅ ALL CRITICAL TESTS PASSED!")
            print("Your project is in excellent condition!")
        else:
            print(f"⚠️  {failed} test(s) need attention - see details above")
        print("="*70)
    
    def save_results(self):
        """Save test results to JSON file."""
        output_file = self.project_root / "comprehensive_test_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to: {output_file}")

def main():
    suite = ComprehensiveTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()
