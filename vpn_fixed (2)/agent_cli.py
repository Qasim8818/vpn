#!/usr/bin/env python3
import sys
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BASE_DIR)

from local_agent import LocalAgent
import json

def main():
    """Interactive CLI for the local agent."""
    agent = LocalAgent()
    agent.show_status()
    
    print("\n🎯 Local Agent Ready for Interaction")
    print("Commands:")
    print("  @query <text>              - Ask a question")
    print("  @codebase <path>           - Index a codebase")
    print("  @fact <text>               - Store a fact")
    print("  @pref <key> <value>        - Store a preference")
    print("  @forget <collection> <id>  - Delete a memory item")
    print("  @facts                     - List all stored facts")
    print("  @status                    - Show system status")
    print("  @history                   - Show conversation history")
    print("  @exit                      - Exit the program")
    print("-" * 50 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "@exit":
                print("👋 Goodbye!")
                break
            
            elif user_input.startswith("@query "):
                query = user_input[7:]
                print("\n⏳ Thinking...\n")
                result = agent.process_query(query, use_codebase=False)
                
                if result["success"]:
                    print(f"Agent: {result['response']}\n")
                else:
                    print(f"❌ Error: {result.get('error')}\n")
            
            elif user_input.startswith("@codebase "):
                path = user_input[10:]
                stats = agent.index_codebase(path)
                print(f"✓ Indexed {stats['indexed']} chunks\n")
            
            elif user_input.startswith("@fact "):
                fact = user_input[6:]
                agent.add_fact(fact)
                print()
            
            elif user_input.startswith("@pref "):
                parts = user_input[6:].split(" ", 1)
                if len(parts) == 2:
                    agent.add_preference(parts[0], parts[1])
                else:
                    print("Usage: @pref <key> <value>\n")
            
            elif user_input == "@status":
                agent.show_status()

            elif user_input == "@history":
                print("\n" + agent.get_conversation_summary() + "\n")

            elif user_input.startswith("@forget "):
                parts = user_input[8:].strip().split(" ", 1)
                if len(parts) == 2:
                    collection, item_id = parts
                    success = agent.memory.forget_memory(collection, item_id)
                    if success:
                        print(f"✓ Deleted item {item_id} from '{collection}'\n")
                    else:
                        print(f"✗ Could not delete. Check collection name and ID.\n")
                        print(f"  Valid collections: facts, preferences, code_snippets, conversations, learnings\n")
                else:
                    print("Usage: @forget <collection> <id>\n")
                    print("  e.g. @forget facts abc-123-def\n")

            elif user_input == "@facts":
                facts = agent.memory.get_all_facts()
                if facts:
                    print(f"\n📚 Stored Facts ({len(facts)}):")
                    for f in facts:
                        fact_text = f["payload"].get("fact", "")
                        print(f"  [{f['id'][:8]}...] {fact_text[:80]}")
                    print()
                else:
                    print("No facts stored yet.\n")
            
            else:
                # Treat as a regular query
                print("\n⏳ Thinking...\n")
                result = agent.process_query(user_input, use_codebase=False)
                
                if result["success"]:
                    print(f"Agent: {result['response']}\n")
                else:
                    print(f"❌ Error: {result.get('error')}\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()
