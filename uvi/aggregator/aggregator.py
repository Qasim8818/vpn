"""
UVI Aggregator – Collects, verifies, and aggregates gradient updates from devices
"""

import time
import json
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import defaultdict

@dataclass
class GradientUpdate:
    """A gradient update submission from a device"""
    device_id: str
    model_version: int
    gradient_hash: str
    batch_hash: str
    batch_size: int
    proof_hash: str
    signature: str
    timestamp: int

class Aggregator:
    """
    Main aggregator service:
    - Listens for gradient proofs from devices
    - Verifies proofs and signatures
    - Aggregates valid gradients
    - Publishes new model version
    """
    
    def __init__(self, model_version: int = 1):
        self.model_version = model_version
        self.seen_messages = set()  # Prevent duplicates
        self.current_gradients: Dict[int, List[GradientUpdate]] = defaultdict(list)
        self.aggregation_threshold = 5  # Min gradients to aggregate
        self.aggregation_timeout = 60  # Seconds
        self.last_aggregation_time = time.time()
        
        # Statistics
        self.total_submissions = 0
        self.valid_submissions = 0
        self.invalid_submissions = 0
        self.aggregation_count = 0
        
    def submit_gradient(self, device_id: str, gradient_hash: str, 
                       batch_hash: str, batch_size: int,
                       proof_hash: str, signature: str) -> bool:
        """
        Receive gradient from device
        """
        update = GradientUpdate(
            device_id=device_id,
            model_version=self.model_version,
            gradient_hash=gradient_hash,
            batch_hash=batch_hash,
            batch_size=batch_size,
            proof_hash=proof_hash,
            signature=signature,
            timestamp=int(time.time())
        )
        
        # Check for duplicates
        update_id = hashlib.sha256(
            f"{device_id}{gradient_hash}{int(time.time())//60}".encode()
        ).hexdigest()
        
        if update_id in self.seen_messages:
            print(f"⚠ Duplicate gradient from {device_id}")
            return False
        
        self.seen_messages.add(update_id)
        self.total_submissions += 1
        
        # Verify (simulated – in real system, verify ZK proof and sig)
        if self._verify_gradient(update):
            self.current_gradients[self.model_version].append(update)
            self.valid_submissions += 1
            print(f"✓ Valid gradient from {device_id} "
                  f"(hash: {gradient_hash[:12]}..., batch_size: {batch_size})")
            return True
        else:
            self.invalid_submissions += 1
            print(f"✗ Invalid gradient from {device_id}")
            return False
    
    def _verify_gradient(self, update: GradientUpdate) -> bool:
        """
        Verify gradient update:
        1. Check ZK proof is valid
        2. Check signature is valid
        3. Check gradient format is correct
        """
        # In real system:
        # - Call gnark verifier for ZK proof
        # - Call Dilithium verifier for signature
        
        # For MVP: basic validation
        if not update.gradient_hash or not update.batch_hash:
            return False
        if update.batch_size <= 0 or update.batch_size > 10000:
            return False
        if not update.proof_hash or not update.signature:
            return False
        
        # Simulate verification (always passes for MVP)
        return True
    
    def check_aggregation_needed(self) -> bool:
        """
        Determine if we should aggregate now
        """
        gradients = self.current_gradients[self.model_version]
        elapsed = time.time() - self.last_aggregation_time
        
        # Aggregate if threshold reached or timeout
        if len(gradients) >= self.aggregation_threshold:
            return True
        
        if elapsed > self.aggregation_timeout and len(gradients) > 0:
            return True
        
        return False
    
    def aggregate_and_publish(self) -> Dict:
        """
        Aggregate valid gradients and publish new model version
        """
        gradients = self.current_gradients[self.model_version]
        
        if not gradients:
            print("⚠ No gradients to aggregate")
            return {}
        
        print(f"\n🔄 Aggregating {len(gradients)} gradients...")
        
        # Collect contributor info
        contributors = list(set(g.device_id for g in gradients))
        total_samples = sum(g.batch_size for g in gradients)
        
        # Compute aggregated model hash (simplified – normally average gradients)
        aggregation_data = {
            "contributors": contributors,
            "gradient_count": len(gradients),
            "total_samples": total_samples,
            "timestamp": int(time.time())
        }
        
        aggregation_str = json.dumps(aggregation_data, sort_keys=True)
        new_model_hash = hashlib.sha256(aggregation_str.encode()).hexdigest()
        
        # Publish new model version
        new_version = self.model_version + 1
        
        result = {
            "old_version": self.model_version,
            "new_version": new_version,
            "new_model_hash": new_model_hash,
            "contributors": len(contributors),
            "gradients_used": len(gradients),
            "total_samples": total_samples,
            "timestamp": int(time.time())
        }
        
        print(f"✓ Model v{self.model_version} → v{new_version}")
        print(f"  Contributors: {len(contributors)}")
        print(f"  Hash: {new_model_hash[:16]}...")
        print(f"  Samples: {total_samples}")
        
        # Simulate IOTA submission
        message_id = self._submit_to_iota(f"model:v{new_version}", result)
        result["message_id"] = message_id
        
        # Update state
        self.model_version = new_version
        self.current_gradients[self.model_version] = []
        self.last_aggregation_time = time.time()
        self.aggregation_count += 1
        
        # Distribute tokens (governance)
        self._distribute_rewards(contributors)
        
        return result
    
    def _submit_to_iota(self, index: str, payload: Dict) -> str:
        """Simulate IOTA submission"""
        message_id = f"iota:{hashlib.sha256(str(payload).encode()).hexdigest()[:16]}"
        print(f"  [IOTA] Index: {index}")
        print(f"         ID: {message_id}")
        return message_id
    
    def _distribute_rewards(self, contributors: List[str]):
        """Distribute tokens to contributors"""
        reward_per_contributor = 1.0  # 1 token
        print(f"💰 Distributing {len(contributors)} tokens to contributors")
        for device_id in contributors:
            print(f"   → {device_id}: +{reward_per_contributor} token")
    
    def get_status(self) -> Dict:
        """Get aggregator status"""
        gradients = self.current_gradients[self.model_version]
        
        return {
            "current_model_version": self.model_version,
            "pending_gradients": len(gradients),
            "aggregation_threshold": self.aggregation_threshold,
            "total_submissions": self.total_submissions,
            "valid_submissions": self.valid_submissions,
            "invalid_submissions": self.invalid_submissions,
            "aggregations_completed": self.aggregation_count,
            "acceptance_rate": (
                self.valid_submissions / self.total_submissions * 100
                if self.total_submissions > 0 else 0
            )
        }
    
    def run_continuous(self, max_duration: int = 300):
        """
        Run aggregator continuously for testing
        """
        print("\n🚀 Aggregator running (continuous mode)...")
        start = time.time()
        
        while time.time() - start < max_duration:
            # Check if aggregation needed
            if self.check_aggregation_needed():
                self.aggregate_and_publish()
            
            time.sleep(5)  # Check every 5 seconds
        
        print("\n⏸ Aggregator stopped")


# ==================== Example Usage ====================

if __name__ == "__main__":
    print("=" * 70)
    print("📊 UVI Aggregator – Demo")
    print("=" * 70)
    
    agg = Aggregator(model_version=1)
    
    # Simulate gradient submissions from 5 devices
    print("\n1️⃣  Simulating gradient submissions...")
    for i in range(5):
        device_id = f"device-{i:03d}"
        gradient_hash = hashlib.sha256(f"grad-{i}".encode()).hexdigest()
        batch_hash = hashlib.sha256(f"batch-{i}".encode()).hexdigest()
        
        agg.submit_gradient(
            device_id=device_id,
            gradient_hash=gradient_hash,
            batch_hash=batch_hash,
            batch_size=32,
            proof_hash="proof123",
            signature="sig456"
        )
    
    # Check status
    print("\n2️⃣  Aggregator Status")
    status = agg.get_status()
    print(json.dumps(status, indent=2))
    
    # Trigger aggregation
    print("\n3️⃣  Triggering Aggregation...")
    if agg.check_aggregation_needed():
        result = agg.aggregate_and_publish()
        print(json.dumps(result, indent=2))
    
    # Final status
    print("\n4️⃣  Final Status")
    status = agg.get_status()
    print(json.dumps(status, indent=2))
    
    print("\n" + "=" * 70)
    print("✓ Demo complete")
    print("=" * 70)
