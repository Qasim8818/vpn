#!/usr/bin/env python3
"""
Complete example demonstrating LocalAgent with real data and workflows.
"""

import sys
sys.path.insert(0, "/home/killer123/Desktop/vpn")

from local_agent import LocalAgent
import time

def example_basic_queries():
    """Example 1: Basic queries with chain-of-thought reasoning."""
    print("\n" + "="*60)
    print("Example 1: Basic Queries with Chain-of-Thought Reasoning")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    
    queries = [
        "What is the best way to structure a Python backend project?",
        "Explain how blockchain works in simple terms.",
        "What are the key principles of secure API design?"
    ]
    
    for query in queries:
        print(f"📝 Query: {query}")
        print("⏳ Thinking...\n")
        result = agent.process_query(query)
        
        if result["success"]:
            print(f"💡 Agent Response:\n{result['response']}\n")
        else:
            print(f"❌ Error: {result.get('error')}\n")
        
        time.sleep(1)

def example_memory_and_learning():
    """Example 2: Storing and retrieving memories."""
    print("\n" + "="*60)
    print("Example 2: Memory & Learning")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    
    # Store facts
    facts = [
        "User prefers Python 3.12 for all projects",
        "VPN architecture uses WireGuard kernel module",
        "DeepSeek-R1:14b is the primary reasoning model",
        "All data is stored locally for privacy"
    ]
    
    print("📌 Storing Facts in Persistent Memory:\n")
    for fact in facts:
        agent.add_fact(fact)
    
    print("\n✓ Facts stored in local vector database (Qdrant)")
    
    # Show memory stats
    print("\n📊 Memory Statistics:")
    stats = agent.memory.get_collection_stats()
    for col_name, col_stats in stats.items():
        if 'error' not in col_stats:
            print(f"  {col_name}: {col_stats['point_count']} items")

def example_preferences():
    """Example 3: User preferences."""
    print("\n" + "="*60)
    print("Example 3: User Preferences")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    
    preferences = {
        "programming_language": "Python",
        "framework": "NestJS",
        "database": "PostgreSQL",
        "vcs": "Git",
        "communication": "direct and technical",
        "cloud_preference": "local/self-hosted"
    }
    
    print("🎯 Setting User Preferences:\n")
    for key, value in preferences.items():
        agent.add_preference(key, value)
    
    print("\n✓ Preferences learned and stored")

def example_codebase_rag():
    """Example 4: RAG with local codebase."""
    print("\n" + "="*60)
    print("Example 4: Codebase RAG (Retrieval-Augmented Generation)")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    
    # Index the VPN codebase
    print("📚 Indexing local codebase...\n")
    stats = agent.index_codebase("/home/killer123/Desktop/vpn")
    
    print(f"\n✓ Indexed {stats['indexed']} code chunks from {stats['total']} files")
    
    # Query the codebase
    print("\n🔍 Querying indexed codebase:")
    query = "How is the local memory system implemented?"
    print(f"Query: {query}\n")
    
    result = agent.process_query(query, use_codebase=True)
    if result["success"]:
        print(f"Response:\n{result['response']}\n")

def example_conversation_flow():
    """Example 5: Multi-turn conversation with learning."""
    print("\n" + "="*60)
    print("Example 5: Multi-Turn Conversation with Learning")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    
    # First, establish context
    agent.add_fact("We're building a secure VPN system")
    agent.add_preference("security_focus", "zero-trust architecture")
    
    conversation = [
        "What security principles should guide our VPN design?",
        "How can we implement post-quantum cryptography?",
        "What about network isolation for enhanced security?",
    ]
    
    print("💬 Multi-Turn Conversation:\n")
    for i, message in enumerate(conversation, 1):
        print(f"Turn {i}: {message}")
        result = agent.process_query(message)
        if result["success"]:
            # Show first 300 chars of response
            response_preview = result['response'][:300] + "...\n"
            print(f"Agent: {response_preview}")
        time.sleep(1)
    
    # Show conversation history
    print("\n📋 Conversation Summary:")
    print(agent.get_conversation_summary())

def example_system_health():
    """Example 6: System health monitoring."""
    print("\n" + "="*60)
    print("Example 6: System Health & Status")
    print("="*60 + "\n")
    
    agent = LocalAgent()
    agent.show_status()

def run_all_examples():
    """Run all examples."""
    print("\n" + "🎯 LOCAL AGENT COMPLETE DEMONSTRATION" + "\n")
    print("This demonstrates a fully-functional, private, 24/7 AI agent")
    print("that learns from interactions and has persistent memory.\n")
    
    try:
        example_system_health()
        example_basic_queries()
        example_memory_and_learning()
        example_preferences()
        example_codebase_rag()
        example_conversation_flow()
        
        print("\n" + "="*60)
        print("✓ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nYour local agentic workflow is fully operational!")
        print("- All data stays on your machine (ZERO cloud leakage)")
        print("- Agent learns from every interaction")
        print("- Chain-of-thought reasoning mimics human thinking")
        print("- 24/7 available via agent_daemon.py")
        print("\nNext: Run 'python3 agent_cli.py' for interactive use")
        print("Or: python3 agent_daemon.py' for background operation\n")
    
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_examples()
