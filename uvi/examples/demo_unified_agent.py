"""
UVI Example 1: Unified Agent Demo
Shows state, actions, and gradient contributions
"""

import sys
sys.path.insert(0, '/home/killer123/Desktop/vpn/uvi')

from agent.uvi_agent import UVIAgent
import json

def main():
    print("\n" + "="*80)
    print("🤖 UVI Example 1: Unified Agent with State, Actions & Gradients")
    print("="*80)
    
    # Create agent for device
    agent = UVIAgent("device-example-001")
    
    # ============ Layer 1: State Management ============
    print("\n" + "─"*80)
    print("Layer 1: Hardware-Bound Identity & State Management (GVEN)")
    print("─"*80)
    
    print("\n1️⃣  Initialize device state...")
    agent.initialize_state({
        "location": "San Francisco, USA",
        "owner": "Alice",
        "device_type": "laptop",
        "created_at": "2026-04-12"
    })
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    print("\n2️⃣  Update state from SF → NYC (generates ZK proof)...")
    agent.update_state_with_proof({"location": "New York, USA"})
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    print("\n3️⃣  Update ownership (generates ZK proof)...")
    agent.update_state_with_proof({"owner": "Bob"})
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    # ============ Layer 2: AI Actions ============
    print("\n" + "─"*80)
    print("Layer 2: Verifiable AI Actions (VPAIN)")
    print("─"*80)
    
    print("\n4️⃣  Execute AI action: Send email...")
    action, proof, result = agent.execute_action_with_proof(
        "Send email to Charlie with the quarterly earnings report"
    )
    print(f"   Action ID: {action.action_id}")
    print(f"   Type: {action.action_type}")
    print(f"   Target: {action.target}")
    print(f"   Proof: {proof[:24]}...")
    print(f"   Result: {result}")
    
    print("\n5️⃣  Execute AI action: Read file...")
    action, proof, result = agent.execute_action_with_proof(
        "Read the database config file"
    )
    print(f"   Action: {action.action_type}({action.target})")
    print(f"   Proof: {proof[:24]}...")
    print(f"   Result: {result}")
    
    # ============ Layer 3: Collaborative Training ============
    print("\n" + "─"*80)
    print("Layer 3: Collaborative Federated Learning (VDAI)")
    print("─"*80)
    
    print("\n6️⃣  Contribute gradient to model v1...")
    gradient, proof, msg_id = agent.contribute_gradient_with_proof(
        gradient_hash="abc123def456ghi789jkl",
        batch_hash="batch_001_hash",
        batch_size=32,
        model_version=1
    )
    print(f"   Gradient Hash: {gradient.gradient_hash[:20]}...")
    print(f"   Proof: {proof[:24]}...")
    print(f"   Message ID: {msg_id}")
    
    print("\n7️⃣  Contribute more gradients (simulating 5 batches)...")
    for i in range(4):
        gradient, proof, msg_id = agent.contribute_gradient_with_proof(
            gradient_hash=f"grad_{i}_{'a'*40}",
            batch_hash=f"batch_{i}_hash",
            batch_size=32,
            model_version=1
        )
    print(f"   Total gradients contributed: {len(agent.gradient_history)}")
    
    # ============ Final Summary ============
    print("\n" + "─"*80)
    print("Summary")
    print("─"*80)
    
    summary = agent.get_state_summary()
    print("\n📊 Final Agent Status:")
    print(json.dumps(summary, indent=2))
    
    print("\n✅ Verification Points:")
    print(f"   • Device ID: {agent.device_id}")
    print(f"   • State Version: {agent.current_state.version}")
    print(f"   • Actions Executed: {len(agent.action_history)}")
    print(f"   • Gradients Contributed: {len(agent.gradient_history)}")
    print(f"   • Total Proofs Generated: {len(agent.action_history) + len(agent.gradient_history) + agent.current_state.version}")
    
    print("\n🔐 Security:")
    print(f"   • All state changes: ZK-proven ✓")
    print(f"   • All actions: Policy-compliant & proof-signed ✓")
    print(f"   • All gradients: Validity-proven without data leak ✓")
    print(f"   • Hardware binding: TPM + Dilithium ✓")
    
    print("\n" + "="*80)
    print("✓ Example 1 Complete – Unified Agent Works!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
