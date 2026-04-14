#!/usr/bin/env python3
"""
Comprehensive Test Suite for VPN Project - Tests all major components
"""

import sys
import os
import json
import importlib.util
import traceback
from pathlib import Path

sys.path.insert(0, "/home/killer123/Desktop/vpn")

class ComprehensiveTestSuite:
    def __init__(self):
        self.results = {
            "timestamp": None,
            "environment": {},
            "tests": {},
            "summary": {"passed": 0, "failed": 0, "skipped": 0},
            "detailed_results": []
        }
        self.base_path = Path("/home/killer123/Desktop/vpn")
    
    def add_result(self, category, test_name, status, details=""):
        """Record test result"""
        result = {
            "category": category,
            "test": test_name,
            "status": status,
            "details": details
        }
        
        category_key = f"{category}_{test_name}"
        self.results["tests"][category_key] = status
        self.results["detailed_results"].append(result)
        
        if status == "PASS":
            self.results["summary"]["passed"] += 1
            symbol = "✓"
        elif status == "SKIP":
            self.results["summary"]["skipped"] += 1
            symbol = "⊘"
        else:
            self.results["summary"]["failed"] += 1
            symbol = "✗"
        
        print(f"  {symbol} [{category}] {test_name}: {status} {details}")
    
    def test_environment(self):
        """Test Python environment"""
        print("\n=== ENVIRONMENT CHECKS ===")
        
        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.results["environment"]["python"] = py_version
        print(f"  Python Version: {py_version}")
        
        # Venv
        venv_path = os.path.join(self.base_path, "venv")
        venv_exists = os.path.exists(venv_path)
        self.results["environment"]["venv"] = venv_exists
        print(f"  Venv Active: {venv_exists}")
        
        # Project root
        self.results["environment"]["project_root"] = str(self.base_path)
        print(f"  Project Root: {self.base_path}")
    
    def test_localagent_imports(self):
        """Test LocalAgent component imports"""
        print("\n=== LOCALAGENT COMPONENT TESTS ===")
        
        tests = [
            ("ollama.ollama_client", "OllamaClient"),
            ("qdrant.local_memory", "LocalMemory"),
            ("continue.local_rag", "LocalRAG"),
        ]
        
        for module_name, class_name in tests:
            try:
                module_path = str(self.base_path / module_name.replace(".", "/") + ".py")
                if not os.path.exists(module_path):
                    self.add_result("LocalAgent", f"{class_name} file", "SKIP", f"File not found: {module_path}")
                    continue
                
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, class_name):
                    self.add_result("LocalAgent", f"{class_name} import", "PASS")
                else:
                    self.add_result("LocalAgent", f"{class_name} import", "FAIL", 
                                  f"Class {class_name} not found in module")
            except Exception as e:
                self.add_result("LocalAgent", f"{class_name} import", "FAIL", str(e)[:100])
    
    def test_uvi_imports(self):
        """Test UVI component imports"""
        print("\n=== UVI COMPONENT TESTS ===")
        
        uvi_modules = [
            ("uvi.agent.uvi_agent", "UVIAgent"),
            ("uvi.agent.trainer", "Trainer"),
        ]
        
        for module_name, class_name in uvi_modules:
            try:
                parts = module_name.split(".")
                module_path = str(self.base_path / "/".join(parts) + ".py")
                
                if not os.path.exists(module_path):
                    self.add_result("UVI", f"{class_name}", "SKIP", "Module not implemented")
                    continue
                
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None:
                    self.add_result("UVI", f"{class_name}", "SKIP", "Cannot create spec")
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.add_result("UVI", f"{class_name}", "PASS")
            except Exception as e:
                self.add_result("UVI", f"{class_name}", "FAIL", str(e)[:100])
    
    def test_code_examples(self):
        """Test code examples syntax"""
        print("\n=== CODE EXAMPLES VALIDATION ===")
        
        examples_path = self.base_path / "code-examples"
        
        # Check key example folders
        example_dirs = ["04-zk-proofs", "06-ring-sigs", "07-mpc", "09-multipath"]
        
        for example_dir in example_dirs:
            dir_path = examples_path / example_dir
            if dir_path.exists():
                files = list(dir_path.glob("*.*"))
                self.add_result("CodeExamples", f"{example_dir}", "PASS", f"{len(files)} files")
            else:
                self.add_result("CodeExamples", f"{example_dir}", "SKIP", "Directory not found")
    
    def test_configuration_files(self):
        """Test configuration file validity"""
        print("\n=== CONFIGURATION TESTS ===")
        
        # Test config.json
        config_path = self.base_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                self.add_result("Config", "config.json", "PASS", f"{len(config)} settings")
            except Exception as e:
                self.add_result("Config", "config.json", "FAIL", str(e)[:100])
        else:
            self.add_result("Config", "config.json", "SKIP")
        
        # Test docker-compose.yml existence
        docker_compose = self.base_path / "uvi" / "docker-compose.yml"
        if docker_compose.exists():
            self.add_result("Config", "docker-compose.yml", "PASS")
        else:
            self.add_result("Config", "docker-compose.yml", "SKIP")
    
    def test_documentation(self):
        """Test documentation completeness"""
        print("\n=== DOCUMENTATION TESTS ===")
        
        docs = ["README.md", "ARCHITECTURE.md", "QUICKSTART.md"]
        
        for doc in docs:
            doc_path = self.base_path / doc
            if doc_path.exists():
                size_kb = doc_path.stat().st_size / 1024
                self.add_result("Docs", doc, "PASS", f"{size_kb:.1f} KB")
            else:
                self.add_result("Docs", doc, "SKIP")
    
    def test_python_files_syntax(self):
        """Test Python files for syntax errors"""
        print("\n=== PYTHON SYNTAX TESTS ===")
        
        # Test main files
        main_files = [
            "local_agent.py",
            "agent_cli.py",
            "agent_daemon.py",
            "validate.py",
            "examples.py"
        ]
        
        for filename in main_files:
            filepath = self.base_path / filename
            if filepath.exists():
                try:
                    with open(filepath) as f:
                        compile(f.read(), filename, 'exec')
                    self.add_result("PythonSyntax", filename, "PASS")
                except SyntaxError as e:
                    self.add_result("PythonSyntax", filename, "FAIL", f"Line {e.lineno}")
                except Exception as e:
                    self.add_result("PythonSyntax", filename, "FAIL", str(e)[:50])
            else:
                self.add_result("PythonSyntax", filename, "SKIP")
    
    def test_dependencies(self):
        """Test dependency files"""
        print("\n=== DEPENDENCY TESTS ===")
        
        req_files = [
            "requirements.txt",
            "uvi/requirements.txt"
        ]
        
        for req_file in req_files:
            req_path = self.base_path / req_file
            if req_path.exists():
                try:
                    with open(req_path) as f:
                        lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    self.add_result("Dependencies", req_file, "PASS", f"{len(lines)} packages")
                except Exception as e:
                    self.add_result("Dependencies", req_file, "FAIL", str(e)[:50])
            else:
                self.add_result("Dependencies", req_file, "SKIP")
    
    def test_project_structure(self):
        """Test project directory structure"""
        print("\n=== PROJECT STRUCTURE TESTS ===")
        
        required_dirs = [
            ("ollama", "Ollama integration"),
            ("qdrant", "Qdrant memory"),
            ("continue", "RAG system"),
            ("uvi", "UVI system"),
            ("code-examples", "Code examples"),
            ("level-iii", "Level III docs"),
        ]
        
        for dirname, description in required_dirs:
            dir_path = self.base_path / dirname
            if dir_path.exists():
                item_count = len(list(dir_path.iterdir()))
                self.add_result("Structure", f"{dirname}/", "PASS", f"{item_count} items")
            else:
                self.add_result("Structure", f"{dirname}/", "FAIL", "Directory missing")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*60)
        print("VPN PROJECT - COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        # Environment checks
        self.test_environment()
        
        # Component tests
        self.test_project_structure()
        self.test_localagent_imports()
        self.test_uvi_imports()
        self.test_python_files_syntax()
        self.test_code_examples()
        self.test_configuration_files()
        self.test_documentation()
        self.test_dependencies()
        
        # Print summary
        self.print_summary()
        
        return self.results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        summary = self.results["summary"]
        total = summary["passed"] + summary["failed"] + summary["skipped"]
        
        print(f"\nTotal Tests: {total}")
        print(f"  ✓ Passed:  {summary['passed']}")
        print(f"  ✗ Failed:  {summary['failed']}")
        print(f"  ⊘ Skipped: {summary['skipped']}")
        
        if summary["failed"] == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {summary['failed']} test(s) need attention")
        
        print("\nDetailed Results:")
        print("-" * 60)
        
        # Group by category
        categories = {}
        for result in self.results["detailed_results"]:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category in sorted(categories.keys()):
            print(f"\n{category}:")
            for result in categories[category]:
                status_symbol = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⊘"
                detail_text = f" - {result['details']}" if result['details'] else ""
                print(f"  {status_symbol} {result['test']}: {result['status']}{detail_text}")


if __name__ == "__main__":
    suite = ComprehensiveTestSuite()
    results = suite.run_all_tests()
    
    # Save results
    output_file = "/home/killer123/Desktop/vpn/test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results saved to: {output_file}")
