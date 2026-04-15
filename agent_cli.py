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
    print("  @query <text>        - Ask a question")
    print("  @codebase <path>     - Index a codebase")
    print("  @fact <text>         - Store a fact")
    print("  @pref <key> <value>  - Store a preference")
    print("  @status              - Show system status")
    print("  @history             - Show conversation history")
    print("  @exit                - Exit the program")
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
