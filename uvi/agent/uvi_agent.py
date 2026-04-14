"""
UVI Unified Agent – Orchestrates state, actions, and training
"""

import time
import json
import uuid
import hashlib
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime

# Mock imports (in real system, these would be actual imports)
# from ollama import Ollama  # Local LLM
# from qdrant_client import QdrantClient  # Vector memory
# from iota_client import IotaClient  # DAG interface

@dataclass
class EntityState:
    """Represents device/entity state"""
    device_id: str
    version: int
    properties: Dict[str, Any]
    timestamp: int
    proof_hash: str = ""
    signature_bytes: bytes = b""

@dataclass
class Action:
    """Represents an AI action"""
    action_id: str
    action_type: str  # "send_email", "read_file", etc.
    actor: str  # Device ID
    target: str  # Recipient/resource
    parameters: Dict[str, Any]
    timestamp: int
    policy_hash: str = ""
    proof_hash: str = ""

@dataclass
class Gradient:
    """Represents gradient update from local training"""
    device_id: str
    model_version: int
    gradient_hash: str
    batch_hash: str
    batch_size: int
    timestamp: int
    proof_hash: str = ""

class UVIAgent:
    """
    Unified agent combining state, actions, and training
    """
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.current_state = None
        self.state_version = 0
        self.action_history = []
        self.gradient_history = []
        
        # Would normally initialize these
        # self.llm = Ollama(model="deepseek-r1:14b")
        # self.memory = QdrantClient(host="localhost", port=6333)
        # self.iota = IotaClient(node_url="http://localhost:14265")
        
    def initialize_state(self, initial_properties: Dict[str, Any]) -> EntityState:
        """
        Initialize device state
        """
        state = EntityState(
            device_id=self.device_id,
            version=0,
            properties=initial_properties,
            timestamp=int(time.time())
        )
        self.current_state = state
        return state
    
    def update_state_with_proof(self, new_properties: Dict[str, Any]) -> tuple:
        """
        Update state and generate ZK proof
        
        1. Create new state snapshot
        2. Call ZK prover for proof
        3. Sign with TPM
        4. Submit to IOTA
        """
        
        if self.current_state is None:
            raise RuntimeError("State not initialized")
        
        old_state = self.current_state
        new_state = EntityState(
            device_id=self.device_id,
            version=old_state.version + 1,
            properties={**old_state.properties, **new_properties},
            timestamp=int(time.time())
        )
        
        # Compute hashes
        old_hash = self._hash_state(old_state)
        new_hash = self._hash_state(new_state)
        
        # Call ZK prover (simulated)
        proof_data = self._call_zk_prover_state(old_hash, new_hash, new_state)
        proof_hash = hashlib.sha256(proof_data).hexdigest()
        
        # Sign with TPM (simulated)
        signature = self._sign_with_tpm(proof_data)
        
        # Submit to IOTA (simulated)
        message_id = self._submit_to_iota(
            index=f"state:v{new_state.version}:{self.device_id}",
            payload={
                "old_hash": old_hash,
                "new_hash": new_hash,
                "proof": proof_hash,
                "properties": new_state.properties,
                "timestamp": new_state.timestamp
            }
        )
        
        new_state.proof_hash = proof_hash
        new_state.signature_bytes = signature
        
        self.current_state = new_state
        
        print(f"✓ State updated from v{old_state.version} → v{new_state.version}")
        print(f"  Proof: {proof_hash[:16]}...")
        print(f"  Message ID: {message_id}")
        
        return new_state, proof_hash, signature
    
    def execute_action_with_proof(self, user_request: str) -> tuple:
        """
        Execute AI action with ZK proof of policy compliance
        
        1. Use LLM to decide action
        2. Check policy
        3. Generate proof
        4. Execute
        5. Log to IOTA
        """
        
        # Step 1: LLM decides action (simulated)
        action = self._llm_decide_action(user_request)
        
        # Step 2: Check policy
        policy_hash = self._get_policy_hash()
        if not self._is_action_allowed(action, policy_hash):
            raise PermissionError(f"Action {action.action_type} not allowed by policy")
        
        # Step 3: Generate ZK proof
        action_bytes = json.dumps(asdict(action)).encode()
        action_hash = hashlib.sha256(action_bytes).hexdigest()
        
        proof_data = self._call_zk_prover_action(action_hash, policy_hash, action)
        proof_hash = hashlib.sha256(proof_data).hexdigest()
        
        # Sign proof
        signature = self._sign_with_tpm(proof_data)
        
        # Step 4: Execute action (simulated)
        action_result = self._execute_action(action)
        
        # Step 5: Log to IOTA
        message_id = self._submit_to_iota(
            index=f"action:v1:{self.device_id}",
            payload={
                "action_id": action.action_id,
                "action_type": action.action_type,
                "target": action.target,
                "proof": proof_hash,
                "policy_hash": policy_hash,
                "timestamp": action.timestamp
            }
        )
        
        action.proof_hash = proof_hash
        self.action_history.append(action)
        
        print(f"✓ Action executed: {action.action_type}({action.target})")
        print(f"  Proof: {proof_hash[:16]}...")
        print(f"  Result: {action_result}")
        
        return action, proof_hash, action_result
    
    def contribute_gradient_with_proof(self, gradient_hash: str, batch_hash: str, 
                                      batch_size: int, model_version: int = 1) -> tuple:
        """
        Contribute gradient proof to federated training
        
        1. Validate gradient format
        2. Generate gradient proof
        3. Sign
        4. Submit to IOTA
        """
        
        gradient = Gradient(
            device_id=self.device_id,
            model_version=model_version,
            gradient_hash=gradient_hash,
            batch_hash=batch_hash,
            batch_size=batch_size,
            timestamp=int(time.time())
        )
        
        # Call ZK prover for gradient proof
        proof_data = self._call_zk_prover_gradient(
            gradient_hash, batch_hash, batch_size
        )
        proof_hash = hashlib.sha256(proof_data).hexdigest()
        
        # Sign
        signature = self._sign_with_tpm(proof_data)
        
        # Submit to IOTA
        message_id = self._submit_to_iota(
            index=f"gradient:v{model_version}:{self.device_id}",
            payload={
                "gradient_hash": gradient_hash,
                "batch_hash": batch_hash,
                "batch_size": batch_size,
                "proof": proof_hash,
                "timestamp": gradient.timestamp
            }
        )
        
        gradient.proof_hash = proof_hash
        self.gradient_history.append(gradient)
        
        print(f"✓ Gradient submitted to model v{model_version}")
        print(f"  Hash: {gradient_hash[:16]}...")
        print(f"  Proof: {proof_hash[:16]}...")
        
        return gradient, proof_hash, message_id
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get current state summary"""
        if self.current_state is None:
            return {"status": "not_initialized"}
        
        return {
            "device_id": self.device_id,
            "current_state_version": self.current_state.version,
            "properties": self.current_state.properties,
            "last_update": datetime.fromtimestamp(self.current_state.timestamp).isoformat(),
            "actions_count": len(self.action_history),
            "gradients_contributed": len(self.gradient_history)
        }
    
    # ========== Private Methods (Simulated) ==========
    
    def _hash_state(self, state: EntityState) -> str:
        """Deterministic hash of state"""
        state_str = json.dumps({
            "device_id": state.device_id,
            "version": state.version,
            "properties": state.properties,
            "timestamp": state.timestamp
        }, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()
    
    def _call_zk_prover_state(self, old_hash: str, new_hash: str, 
                              new_state: EntityState) -> bytes:
        """Call ZK prover for state transition proof"""
        # In real system: gRPC call to zk/prover/server.go
        # For MVP: return simulated proof
        proof_data = f"state_proof:{old_hash[:8]}→{new_hash[:8]}".encode()
        return proof_data
    
    def _call_zk_prover_action(self, action_hash: str, policy_hash: str, 
                               action: Action) -> bytes:
        """Call ZK prover for action compliance proof"""
        proof_data = f"action_proof:{action_hash[:8]}|{policy_hash[:8]}".encode()
        return proof_data
    
    def _call_zk_prover_gradient(self, grad_hash: str, batch_hash: str, 
                                batch_size: int) -> bytes:
        """Call ZK prover for gradient proof"""
        proof_data = f"gradient_proof:{grad_hash[:8]}|{batch_hash[:8]}|{batch_size}".encode()
        return proof_data
    
    def _sign_with_tpm(self, data: bytes) -> bytes:
        """Sign with TPM + Dilithium"""
        # In real system: subprocess call to hardware/target/release/uvi_sign
        # For MVP: return simulated signature
        return hashlib.sha256(data + b"signature_salt").digest()
    
    def _submit_to_iota(self, index: str, payload: Dict) -> str:
        """Submit message to IOTA DAG"""
        # In real system: IotaClient().send_message(index, payload)
        # For MVP: return simulated message ID
        message_id = f"iota:{uuid.uuid4().hex[:16]}"
        print(f"  [IOTA] {index}: {message_id}")
        return message_id
    
    def _llm_decide_action(self, user_request: str) -> Action:
        """Use LLM to decide action"""
        # In real system: use Ollama to generate action
        # For MVP: hardcoded responses
        action_id = str(uuid.uuid4())
        
        if "email" in user_request.lower():
            return Action(
                action_id=action_id,
                action_type="send_email",
                actor=self.device_id,
                target="recipient@example.com",
                parameters={"subject": "Update", "body": user_request},
                timestamp=int(time.time())
            )
        elif "read" in user_request.lower():
            return Action(
                action_id=action_id,
                action_type="read_file",
                actor=self.device_id,
                target="/path/to/file.txt",
                parameters={},
                timestamp=int(time.time())
            )
        else:
            return Action(
                action_id=action_id,
                action_type="execute_code",
                actor=self.device_id,
                target="python",
                parameters={"code": user_request},
                timestamp=int(time.time())
            )
    
    def _get_policy_hash(self) -> str:
        """Get hash of allowed actions policy"""
        # In real system: fetch from policy ledger
        allowed = ["send_email", "read_file", "execute_code"]
        policy_str = json.dumps(allowed, sort_keys=True)
        return hashlib.sha256(policy_str.encode()).hexdigest()
    
    def _is_action_allowed(self, action: Action, policy_hash: str) -> bool:
        """Check if action is allowed by policy"""
        # In real system: verify ZK proof of compliance
        # For MVP: simple whitelist
        allowed = ["send_email", "read_file", "execute_code"]
        return action.action_type in allowed
    
    def _execute_action(self, action: Action) -> str:
        """Execute the action (simulated)"""
        if action.action_type == "send_email":
            return f"✓ Email sent to {action.target}"
        elif action.action_type == "read_file":
            return f"✓ File read: {action.target}"
        elif action.action_type == "execute_code":
            return f"✓ Code executed: {action.target}"
        else:
            return "⚠ Unknown action"


# ==================== Example Usage ====================

if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("🤖 UVI Unified Agent – Demo")
    print("=" * 70)
    
    # Create agent
    agent = UVIAgent("device-demo-001")
    
    # Initialize state
    print("\n1️⃣  Initialize State")
    agent.initialize_state({
        "location": "us-west-2",
        "owner": "Alice",
        "permissions": ["read", "write"]
    })
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    # Update state
    print("\n2️⃣  Update State (with ZK Proof)")
    agent.update_state_with_proof({"location": "us-east-1"})
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    # Execute action
    print("\n3️⃣  Execute AI Action (with ZK Proof)")
    agent.execute_action_with_proof("Send email to Bob with the quarterly report")
    
    # Contribute gradient
    print("\n4️⃣  Contribute Gradient (with ZK Proof)")
    agent.contribute_gradient_with_proof(
        gradient_hash="abc123def456",
        batch_hash="batch789xyz",
        batch_size=32,
        model_version=1
    )
    
    # Final summary
    print("\n5️⃣  Final Summary")
    print(json.dumps(agent.get_state_summary(), indent=2))
    
    print("\n" + "=" * 70)
    print("✓ All operations completed with ZK proofs")
    print("=" * 70)
