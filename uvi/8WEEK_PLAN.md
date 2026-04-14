# UVI: 8-Week Implementation Plan (Daily Tasks)

## Overview
This plan breaks down the creation of Universal Verifiable Intelligence into 57 concrete daily tasks. Each task is self-contained, testable, and leads toward a complete system by Day 57.

**Time Commitment:** 8-10 hours/day, 5-6 days/week
**Total Effort:** ~450-480 hours
**Cost:** $0 (open-source tools only)

---

## WEEK 1: Hardware Identity & Infrastructure Setup

### Day 1: Environment & TPM Verification
**Goal:** Verify hardware capabilities and set up development environment.

**Task:**
1. Install development tools: Go 1.22+, Rust 1.70+, Python 3.11+, Node 20+
2. Verify TPM 2.0 presence:
   ```bash
   tpm2_getcap handles-persistent
   ```
3. Create project structure (directories listed in README.md)
4. Initialize Git repo with .gitignore

**Deliverable:** `$ tpm2_getcap` returns TPM handles; project structure created
**Time:** 2 hours

---

### Day 2: Rust Hardware Module - TPM Keyring
**Goal:** Build Rust library for TPM operations

**Task:**
1. Create `hardware/Cargo.toml` with dependencies:
   - `tss-esapi` (TPM interface)
   - `zeroize` (secure memory)
   - `sha2` (hashing)

2. Implement `hardware/src/tpm.rs`:
   - `fn create_primary_key()` – Creates TPM primary key
   - `fn load_key()` – Loads persisted key
   - `fn sign_data(data: &[u8])` – TPM-based signing

3. Write tests:
   ```bash
   cd hardware && cargo test
   ```

**Deliverable:** `cargo build` completes; sign_data returns 4096-bit signature
**Time:** 3 hours

---

### Day 3: Post-Quantum Signing (Dilithium/Falcon)
**Goal:** Integrate NIST post-quantum signature algorithm

**Task:**
1. Add dependency to `Cargo.toml`: `liboqs` (quantum-safe crypto)
2. Implement `hardware/src/dilithium.rs`:
   - `fn generate_key_pair()` – Generate Dilithium2 keys (2.5KB key)
   - `fn sign(data: &[u8], sk: &[u8])` – Sign with private key
   - `fn verify(sig: &[u8], pk: &[u8], msg: &[u8])` – Verify signature

3. Test signatures:
   ```rust
   let (pk, sk) = generate_key_pair();
   let sig = sign(b"test message", &sk);
   assert!(verify(&sig, &pk, b"test message"));
   ```

**Deliverable:** `cargo test` passes; signatures are quantum-resistant
**Time:** 2 hours

---

### Day 4: TPM + Dilithium Integration
**Goal:** Combine TPM key with Dilithium for hardware-bound signing

**Task:**
1. Create device identity based on TPM public key hash:
   ```rust
   pub fn create_device_id() -> String {
       let tpm_pubkey = load_tpm_public_key();
       let device_id = sha256(tpm_pubkey);
       device_id.to_hex()
   }
   ```

2. Persist Dilithium keys securely (encrypted by TPM):
   ```rust
   pub fn save_keys_encrypted(pk: &[u8], sk: &[u8]) {}
   pub fn load_keys_encrypted() -> (Vec<u8>, Vec<u8>) {}
   ```

3. Build CLI:
   ```bash
   cargo build --release
   ./target/release/uvi-hw init  # Creates device_id, keys
   ```

**Deliverable:** `./uvi-hw init` creates `~/.uvi/device_id` and encrypted keys
**Time:** 2 hours

---

### Day 5: Docker IOTA Node Setup
**Goal:** Run IOTA Hornet node locally for DAG anchoring

**Task:**
1. Create `docker-compose.yml` (partial):
   ```yaml
   iota:
     image: iotaledger/hornet:latest
     ports:
       - "14265:14265"  # API endpoint
     environment:
       HORNET_API_ENABLE: "true"
   ```

2. Start node:
   ```bash
   docker-compose up -d iota
   ```

3. Verify connectivity:
   ```bash
   curl http://localhost:14265/api/v2/info
   # Should return: {"nodeinfo": {...}}
   ```

4. Create Python client (`dag/iota_config.py`):
   ```python
   IOTA_URL = "http://localhost:14265"
   FAUCET_URL = "https://faucet.testnet.shimmer.network/api/enqueue"  # For testnet
   ```

**Deliverable:** IOTA node running; API responds to health check
**Time:** 1.5 hours

---

### Day 6: gRPC ZK Prover Server Skeleton
**Goal:** Set up gRPC service for ZK proof generation

**Task:**
1. Create `zk/proto/prover.proto`:
   ```protobuf
   service Prover {
     rpc GenerateStateProof(StateProofRequest) returns (StateProofResponse);
     rpc GenerateActionProof(ActionProofRequest) returns (ActionProofResponse);
     rpc GenerateGradientProof(GradientProofRequest) returns (GradientProofResponse);
   }
   ```

2. Generate Go bindings:
   ```bash
   cd zk
   protoc --go_out=. --go-grpc_out=. proto/prover.proto
   ```

3. Skeleton server (`zk/prover/server.go`):
   ```go
   func (s *ProverServer) GenerateStateProof(ctx context.Context, req *StateProofRequest) (*StateProofResponse, error) {
       // TODO: implement
       return &StateProofResponse{Proof: []byte{}}, nil
   }
   ```

4. Start server:
   ```bash
   cd zk && go run prover/server.go &
   ```

**Deliverable:** `grpcurl localhost:50051 list` shows three RPC methods
**Time:** 2 hours

---

### Day 7: Docker Compose Full Stack
**Goal:** Orchestrate all services (IOTA, Redis, gRPC prover, Python agent)

**Task:**
1. Complete `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     iota:
       image: iotaledger/hornet:latest
       ports: ["14265:14265"]
     redis:
       image: redis:latest
       ports: ["6379:6379"]
     prover:
       build: ./zk
       ports: ["50051:50051"]
     agent:
       build: ./agent
       depends_on: [iota, redis, prover]
   ```

2. Build and verify:
   ```bash
   docker-compose build
   docker-compose up -d
   docker-compose ps  # All services show "Up"
   ```

3. Create health check script:
   ```bash
   #!/bin/bash
   curl http://localhost:14265/api/v2/info && echo "✓ IOTA"
   redis-cli ping | grep PONG && echo "✓ Redis"
   grpcurl localhost:50051 list | grep Prover && echo "✓ gRPC"
   ```

**Deliverable:** All 4 services running; health check passes
**Time:** 1.5 hours

---

## WEEK 2: ZK Circuits for State Transitions

### Day 8: Define State Schema
**Goal:** Specify what state transitions look like

**Task:**
1. Create `agent/state_schema.py`:
   ```python
   @dataclass
   class DeviceState:
       device_id: str  # TPM-derived
       location: str   # GPS or WiFi fingerprint
       timestamp: int  # Unix timestamp
       owner: str      # Entity identifier
       nonce: int      # Prevent replay
   
   @dataclass
   class StateTransition:
       old_state: DeviceState
       new_state: DeviceState
       proof_hash: str  # ZK proof will match this
   ```

2. Pack/unpack for hashing:
   ```python
   def state_to_bytes(state: DeviceState) -> bytes:
       # Serialize in canonical form for hashing
   
   def hash_state(state: DeviceState) -> str:
       return sha256(state_to_bytes(state)).hex()
   ```

3. Create examples:
   ```python
   state1 = DeviceState("device-abc", "us-west-2", 1712345600, "Alice", 1)
   state2 = DeviceState("device-abc", "us-east-1", 1712349200, "Alice", 2)
   transition = StateTransition(state1, state2, "proof_hash_placeholder")
   ```

**Deliverable:** Schema correctly serializes/deserializes; hash is deterministic
**Time:** 1.5 hours

---

### Day 9-10: ZK State Transition Circuit (Go/gnark)
**Goal:** Build ZK circuit proving valid state transition

**Task:**
1. Implement `zk/circuit/state.go`:
   ```go
   type StateTransitionCircuit struct {
       // Public inputs (verifier sees)
       OldStateHash frontend.Variable `gnark:",public"`
       NewStateHash frontend.Variable `gnark:",public"`
       Timestamp    frontend.Variable `gnark:",public"`
       
       // Private inputs (prover only)
       OldLocation  frontend.Variable `gnark:",secret"`
       NewLocation  frontend.Variable `gnark:",secret"`
       Owner        frontend.Variable `gnark:",secret"`
   }
   
   func (c *StateTransitionCircuit) Define(api frontend.API) error {
       // Verify old state hash
       // Verify new state hash
       // Ensure timestamp increased
       // Ensure same owner
       return nil
   }
   ```

2. Implement hashing in circuit using MiMC:
   ```go
   h := mimc.NewMiMC(api)
   h.Write(oldLocation)
   h.Write(owner)
   h.Write(timestamp)
   computedHash := h.Sum()
   api.AssertIsEqual(computedHash, c.OldStateHash)
   ```

3. Test circuit:
   ```bash
   cd zk && go test ./circuit -run StateTransition -v
   ```

**Deliverable:** `go test` passes; circuit generates ~1000-constraint proof
**Time:** 4 hours

---

### Day 11: Circuit Compilation & Key Generation
**Goal:** Compile circuit and generate trusted setup keys

**Task:**
1. Create `zk/circuit/setup.go`:
   ```go
   func CompileStateCircuit() (compiled.Circuit, error) {
       circuit := &StateTransitionCircuit{}
       return frontend.Compile(ecc.BN254.ScalarField(), r1cs.NewBuilder, circuit)
   }
   
   func GenerateKeys() (pk scs.ProvingKey, vk scs.VerifyingKey, error) {
       compiled, _ := CompileStateCircuit()
       pk, vk, _ := groth16.Setup(compiled)
       return pk, vk, nil
   }
   ```

2. Run setup (one-time trusted ceremony):
   ```bash
   cd zk && go run setup.go
   # Output: proving_key.bin (10MB), verifying_key.bin (1MB)
   ```

3. Save keys:
   ```
   zk/keys/
     ├── state_pk.bin
     ├── state_vk.bin
     ├── action_pk.bin
     ├── action_vk.bin
     ├── gradient_pk.bin
     └── gradient_vk.bin
   ```

**Deliverable:** Keys generated and saved; file sizes reasonable (<50MB total)
**Time:** 1.5 hours

---

### Day 12-13: Prover Implementation for State Proofs
**Goal:** Implement proof generation in gRPC server

**Task:**
1. Create `zk/prover/state_prover.go`:
   ```go
   func (s *ProverServer) GenerateStateProof(ctx context.Context, req *StateProofRequest) (*StateProofResponse, error) {
       // Load proving key
       pk := LoadProvingKey("zk/keys/state_pk.bin")
       
       // Build witness from request
       witness := &StateTransitionCircuit{
           OldStateHash: req.OldStateHash,
           NewStateHash: req.NewStateHash,
           OldLocation: req.OldLocation,
           NewLocation: req.NewLocation,
           Owner: req.Owner,
       }
       
       // Generate proof
       proof, _ := groth16.Prove(compiled, pk, witness)
       
       // Serialize
       proofBytes, _ := proto.Marshal(proof)
       return &StateProofResponse{Proof: proofBytes}, nil
   }
   ```

2. Test with manual request:
   ```bash
   grpcurl -d @ localhost:50051 proto.Prover/GenerateStateProof << EOF
   {"old_state_hash": "abc...", "new_state_hash": "def..."}
   EOF
   ```

**Deliverable:** gRPC call returns non-empty proof bytes (~1-2KB)
**Time:** 3 hours

---

### Day 14: Integration Test – State Proof End-to-End
**Goal:** Verify state transition from schema → circuit → proof → verification

**Task:**
1. Write `zk/circuit/state_test.go`:
   ```go
   func TestStateProofGeneration(t *testing.T) {
       // 1. Create witness
       // 2. Generate proof
       // 3. Verify proof
       // 4. Assert verification succeeds
   }
   ```

2. Create Python test that calls gRPC:
   ```python
   # agent/tests/test_state_proof.py
   def test_state_transition_proof():
       state1 = create_state("device-1", "us-west", "Alice")
       state2 = create_state("device-1", "us-east", "Alice")
       
       proof = call_prover(state1, state2)
       assert len(proof) > 0
       
       verified = verify_proof(proof, state1, state2)
       assert verified
   ```

3. Run both:
   ```bash
   cd zk && go test ./circuit -v
   cd .. && python3 -m pytest agent/tests/test_state_proof.py -v
   ```

**Deliverable:** All tests pass; proof generation and verification work end-to-end
**Time:** 2 hours

---

## WEEK 3: AI Action Layer

### Day 15: Action Schema & Ledger
**Goal:** Define what AI actions are and how they're logged

**Task:**
1. Create `agent/action_schema.py`:
   ```python
   @dataclass
   class Action:
       action_id: str  # UUID
       action_type: str  # "send_email", "access_file", etc.
       actor: str  # Agent identity
       target: str  # Recipient/resource
       timestamp: int
       policy_hash: str  # Hash of policy that allows action
   
   @dataclass
   class ActionLog:
       actions: List[Action]
       
       def add_action(self, action: Action):
           self.actions.append(action)
       
       def action_to_bytes(self, action: Action) -> bytes:
           # Canonical form for ZK proof
   ```

2. Implement storage:
   ```python
   def save_action_log(log: ActionLog, filename="actions.log"):
       with open(filename, "wb") as f:
           f.write(pickle.dumps(log))
   
   def load_action_log(filename="actions.log") -> ActionLog:
       with open(filename, "rb") as f:
           return pickle.loads(f.read())
   ```

**Deliverable:** Can create, serialize, and persist actions
**Time:** 1.5 hours

---

### Day 16-17: ZK Action Compliance Circuit
**Goal:** Build ZK circuit proving an action complies with policy

**Task:**
1. Implement `zk/circuit/action.go`:
   ```go
   type ActionComplianceCircuit struct {
       // Public
       ActionHash frontend.Variable `gnark:",public"`
       PolicyHash frontend.Variable `gnark:",public"`
       Timestamp  frontend.Variable `gnark:",public"`
       
       // Private (hidden action details)
       ActionType frontend.Variable `gnark:",secret"`
       Target     frontend.Variable `gnark:",secret"`
       Actor      frontend.Variable `gnark:",secret"`
   }
   
   func (c *ActionComplianceCircuit) Define(api frontend.API) error {
       // Verify action hash matches action fields
       // Verify policy allows this action type
       // Ensure timestamp is recent
       return nil
   }
   ```

2. Policy checking (simplified):
   ```go
   // Allowed actions stored as hash in circuit
   // Policy: allowedActions = [sha256("send_email"), sha256("read_file")]
   api.AssertIsIn(c.ActionType, allowedActions)
   ```

3. Test with examples:
   ```go
   func TestActionProof(t *testing.T) {
       // Test allowed action passes
       // Test forbidden action fails
   }
   ```

**Deliverable:** Action circuit compiles; generates proofs for allowed/forbidden actions
**Time:** 3 hours

---

### Day 18-19: Personal AI Agent (LLM Integration)
**Goal:** Create AI agent that decides actions based on user requests

**Task:**
1. Install Ollama locally (pulls pre-existing deepseek-r1:14b):
   ```bash
   ollama serve &
   ollama list | grep deepseek
   ```

2. Create `agent/personal_ai.py`:
   ```python
   from ollama import Ollama
   
   class PersonalAIAgent:
       def __init__(self, device_id):
           self.device_id = device_id
           self.llm = Ollama(model="deepseek-r1:14b")
           self.allowed_actions = ["send_email", "read_file"]
       
       def decide_action(self, user_request: str) -> Action:
           # Use LLM to understand request
           prompt = f"""Given user request: "{user_request}"
           Decide action from: {self.allowed_actions}
           Return: action_type, target"""
           response = self.llm.generate(prompt)
           action = parse_response(response)
           return action
       
       def execute_action(self, action: Action):
           # Execute action (or simulate for MVP)
           if action.action_type == "send_email":
               print(f"[Simulated] Sending email to {action.target}")
           elif action.action_type == "read_file":
               # Actual file read
               with open(action.target) as f:
                   return f.read()
   ```

3. Test:
   ```python
   agent = PersonalAIAgent("device-1")
   action = agent.decide_action("Send email to Bob with update")
   agent.execute_action(action)
   ```

**Deliverable:** Agent can decide actions based on LLM reasoning
**Time:** 2.5 hours

---

### Day 20-21: Action Proof Integration
**Goal:** Combine action execution with ZK proofs

**Task:**
1. Extend `agent/action_handler.py`:
   ```python
   def execute_with_proof(self, user_request: str) -> (Action, bytes):
       # 1. Decide action
       action = self.decide_action(user_request)
       
       # 2. Check policy
       if not self.is_action_allowed(action):
           raise PermissionError(f"Action {action.action_type} not allowed")
       
       # 3. Generate ZK proof of compliance
       action_bytes = action_to_bytes(action)
       action_hash = sha256(action_bytes).hex()
       policy_hash = sha256(str(self.allowed_actions)).hex()
       
       proof = call_prover_action(
           action_hash=action_hash,
           policy_hash=policy_hash,
           action_type=action.action_type
       )
       
       # 4. Execute action
       self.execute_action(action)
       
       # 5. Return action + proof
       return action, proof
   ```

2. Test end-to-end:
   ```python
   action, proof = agent.execute_with_proof("Send email to customer")
   assert len(proof) > 0
   assert action.action_type in allowed_actions
   ```

**Deliverable:** Actions generate valid ZK proofs before execution
**Time:** 2 hours

---

## WEEK 4: Federated Learning with Gradient Proofs

### Day 22-24: PyTorch Trainer with Gradient Hashing
**Goal:** Build local trainer that computes gradient hashes for ZK proof

**Task:**
1. Create `agent/trainer.py`:
   ```python
   import torch
   import torch.nn as nn
   from hashlib import sha256
   
   class FederatedTrainer:
       def __init__(self, device_id, model_version=1):
           self.device_id = device_id
           self.model = self.build_model()
           self.model_version = model_version
           self.optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)
           self.criterion = nn.CrossEntropyLoss()
       
       def build_model(self):
           # Simple MNIST CNN
           return nn.Sequential(
               nn.Conv2d(1, 32, 3, padding=1),
               nn.ReLU(),
               nn.MaxPool2d(2),
               nn.Flatten(),
               nn.Linear(32*14*14, 10)
           )
       
       def hash_gradients(self) -> str:
           grad_str = ""
           for p in self.model.parameters():
               if p.grad is not None:
                   grad_str += p.grad.cpu().detach().numpy().tobytes().hex()
           return sha256(grad_str.encode()).hexdigest()
       
       def train_step(self, batch_data, batch_labels):
           self.optimizer.zero_grad()
           output = self.model(batch_data)
           loss = self.criterion(output, batch_labels)
           loss.backward()
           self.optimizer.step()
           
           grad_hash = self.hash_gradients()
           return grad_hash
   ```

2. Test with MNIST:
   ```python
   from torchvision import datasets, transforms
   
   dataset = datasets.MNIST('.data', download=True, transform=transforms.ToTensor())
   loader = torch.utils.data.DataLoader(dataset, batch_size=32)
   
   trainer = FederatedTrainer("device-1")
   for batch, labels in loader:
       grad_hash = trainer.train_step(batch, labels)
       print(f"Gradient hash: {grad_hash[:16]}...")
   ```

**Deliverable:** Gradient hashes are deterministic and change per batch
**Time:** 3 hours

---

### Day 25-26: ZK Gradient Proof Circuit
**Goal:** Build circuit proving gradient is valid without revealing data

**Task:**
1. Implement `zk/circuit/gradient.go`:
   ```go
   type GradientCircuit struct {
       // Public
       GradientHash frontend.Variable `gnark:",public"`
       BatchHash    frontend.Variable `gnark:",public"`
       BatchSize    frontend.Variable `gnark:",public"`
       
       // Private (hidden data)
       DataPoints []frontend.Variable `gnark:",secret"`
   }
   
   func (c *GradientCircuit) Define(api frontend.API) error {
       // Verify batch size matches number of data points
       api.AssertIsEqual(len(c.DataPoints), c.BatchSize)
       
       // Compute hash of data points
       h := mimc.NewMiMC(api)
       for _, d := range c.DataPoints {
           h.Write(d)
       }
       computedHash := h.Sum()
       api.AssertIsEqual(computedHash, c.BatchHash)
       
       // Verify gradient hash (simplified: just include in witness)
       return nil
   }
   ```

2. Generate keys:
   ```bash
   # (Reuse Day 11 process for gradient circuit)
   ```

3. Test:
   ```go
   func TestGradientProof(t *testing.T) {
       // Valid batch generates proof
       // Invalid batch fails
   }
   ```

**Deliverable:** Gradient circuit generates proofs; proof size ~2-3KB
**Time:** 2 hours

---

### Day 27-28: Trainer Submits Proofs to DAG
**Goal:** Trainer generates gradient proof and submits to IOTA

**Task:**
1. Create `agent/gradient_submitter.py`:
   ```python
   import grpc
   from dag.iota_client import IOTAClient
   from hardware.pq_signer import sign_with_tpm
   
   class GradientSubmitter:
       def __init__(self, device_id):
           self.device_id = device_id
           self.iota = IOTAClient()
       
       def submit_gradient(self, grad_hash: str, batch_hash: str, batch_size: int):
           # 1. Call ZK prover
           proof = call_zk_prover_gradient(
               gradient_hash=grad_hash,
               batch_hash=batch_hash,
               batch_size=batch_size
           )
           
           # 2. Sign with TPM
           signature = sign_with_tpm(proof)
           
           # 3. Create IOTA message
           payload = {
               "device_id": self.device_id,
               "model_version": 1,
               "gradient_hash": grad_hash,
               "proof": proof.hex(),
               "signature": signature.hex(),
               "timestamp": time.time()
           }
           
           # 4. Submit to DAG
           message_id = self.iota.submit_message(
               index=f"gradient:v1:{self.device_id}",
               payload=payload
           )
           
           return message_id
   ```

2. Integrate with trainer:
   ```python
   class FederatedTrainer:
       def __init__(self, device_id):
           # ... existing code ...
           self.submitter = GradientSubmitter(device_id)
       
       def train_with_submission(self, batch_data, batch_labels):
           grad_hash = self.train_step(batch_data, batch_labels)
           msg_id = self.submitter.submit_gradient(
               grad_hash=grad_hash,
               batch_hash=sha256(batch_data),
               batch_size=len(batch_data)
           )
           return msg_id
   ```

3. Test:
   ```python
   trainer = FederatedTrainer("device-1")
   for batch, labels in loader:
       msg_id = trainer.train_with_submission(batch, labels)
       print(f"Submitted: {msg_id}")
   ```

**Deliverable:** Gradient proofs appear on IOTA; can be queried by version+device_id
**Time:** 2.5 hours

---

## WEEK 5: Aggregator & Governance

### Day 29-31: Aggregator Listen & Verify Loop
**Goal:** Build aggregator that consumes gradient proofs from IOTA

**Task:**
1. Create `aggregator/aggregator.py`:
   ```python
   import time
   from dag.iota_client import IOTAClient
   from aggregator.verifier import VerifyProof
   
   class GradientAggregator:
       def __init__(self, model_version=1):
           self.model_version = model_version
           self.iota = IOTAClient()
           self.seen_proofs = set()
           self.valid_gradients = []
       
       def run(self):
           while True:
               # Poll for new messages
               messages = self.iota.get_messages(f"gradient:v{self.model_version}")
               
               for msg in messages:
                   if msg.message_id in self.seen_proofs:
                       continue
                   
                   # Verify proof and signature
                   if self.verify_update(msg):
                       self.valid_gradients.append(msg.gradient_hash)
                       self.seen_proofs.add(msg.message_id)
                       print(f"✓ Valid gradient from {msg.device_id}")
                   else:
                       print(f"✗ Invalid gradient from {msg.device_id}")
               
               # If enough gradients, aggregate
               if len(self.valid_gradients) >= 5:
                   self.aggregate_and_publish()
               
               time.sleep(5)
       
       def verify_update(self, msg) -> bool:
           # Verify ZK proof
           if not VerifyProof(msg.proof):
               return False
           
           # Verify signature
           if not verify_signature(msg.signature, msg.device_id, msg.proof):
               return False
           
           return True
       
       def aggregate_and_publish(self):
           # Simple averaging (in production, use actual gradient averaging)
           print(f"Aggregating {len(self.valid_gradients)} gradients")
           
           # Publish new model version
           new_version = self.model_version + 1
           msg_id = self.iota.submit_message(
               index=f"model:v{new_version}",
               payload={"aggregated": True, "contributors": len(self.valid_gradients)}
           )
           
           self.model_version = new_version
           self.valid_gradients.clear()
           print(f"✓ Published model v{new_version}")
   ```

2. Start aggregator:
   ```bash
   cd aggregator && python3 aggregator.py
   ```

**Deliverable:** Aggregator runs continuously; prints valid/invalid updates
**Time:** 3 hours

---

### Day 32-33: Proof Verification Module
**Goal:** Implement verification of ZK proofs and signatures

**Task:**
1. Create `aggregator/verifier.py`:
   ```python
   from cryptography.hazmat.primitives import hashes
   from cryptography.hazmat.primitives.asymmetric import padding
   import subprocess
   
   def verify_proof_zk(proof_bytes: bytes, public_inputs: dict) -> bool:
       """Verify ZK proof using gnark verifier (Go subprocess)"""
       # Write proof to temp file
       with open("/tmp/proof.bin", "wb") as f:
           f.write(proof_bytes)
       
       # Call Go verifier
       result = subprocess.run(
           ["./verifier", "/tmp/proof.bin", json.dumps(public_inputs)],
           capture_output=True,
           cwd="zk"
       )
       
       return result.returncode == 0
   
   def verify_signature(signature: bytes, device_id: str, proof: bytes) -> bool:
       """Verify Dilithium signature"""
       # Get device's public key from TPM registry
       pk = get_device_public_key(device_id)
       
       # Verify using liboqs
       result = subprocess.run(
           ["./verify_dilithium", signature.hex(), proof.hex(), pk.hex()],
       )
       
       return result.returncode == 0
   ```

2. Build Go verifier binary:
   ```go
   // zk/verifier/main.go
   func main() {
       proofFile := os.Args[1]
       publicInputsJSON := os.Args[2]
       
       // Load proof
       proof := loadProof(proofFile)
       
       // Verify
       vk := loadVerifyingKey("zk/keys/gradient_vk.bin")
       valid := groth16.Verify(proof, vk, publicInputs)
       
       if valid {
           os.Exit(0)
       } else {
           os.Exit(1)
       }
   }
   ```

3. Test:
   ```python
   proof = generate_test_proof()
   assert verify_proof_zk(proof, {}) == True
   ```

**Deliverable:** Proofs are correctly verified; invalid proofs rejected
**Time:** 2 hours

---

### Day 34-35: DAO Governance & Token Incentives
**Goal:** Implement vote mechanism and token rewards

**Task:**
1. Create `aggregator/governor.py`:
   ```python
   @dataclass
   class TokenBalance:
       device_id: str
       balance: float
   
   @dataclass
   class Proposal:
       proposal_id: str
       model_hash: str
       proposer: str
       votes_for: float = 0.0
       votes_against: float = 0.0
       status: str = "open"  # or "approved", "rejected"
   
   class DAO:
       def __init__(self):
           self.balances = {}  # device_id -> balance
           self.proposals = {}
       
       def reward_contributor(self, device_id: str, amount: float = 1.0):
           """Give tokens to device for valid gradient"""
           if device_id not in self.balances:
               self.balances[device_id] = 0.0
           self.balances[device_id] += amount
       
       def propose_model(self, proposer: str, model_hash: str):
           """Create governance proposal for new model"""
           proposal_id = str(uuid.uuid4())
           self.proposals[proposal_id] = Proposal(
               proposal_id=proposal_id,
               model_hash=model_hash,
               proposer=proposer
           )
           return proposal_id
       
       def vote(self, proposal_id: str, device_id: str, choice: bool):
           """Vote with token weight"""
           proposal = self.proposals[proposal_id]
           weight = self.balances.get(device_id, 0.0)
           
           if choice:
               proposal.votes_for += weight
           else:
               proposal.votes_against += weight
       
       def finalize_proposal(self, proposal_id: str):
           """Determine outcome and execute"""
           proposal = self.proposals[proposal_id]
           if proposal.votes_for > proposal.votes_against:
               proposal.status = "approved"
               # Update global model hash on IOTA
           else:
               proposal.status = "rejected"
   ```

2. Integrate with aggregator:
   ```python
   class GradientAggregator:
       def __init__(self, model_version=1):
           # ... existing code ...
           self.dao = DAO()
       
       def aggregate_and_publish(self):
           # Reward all contributors
           for device_id in self.contributors:
               self.dao.reward_contributor(device_id)
           
           # Publish aggregated model (requires governance approval)
           proposal_id = self.dao.propose_model(
               proposer="aggregator",
               model_hash=compute_model_hash()
           )
           print(f"Governance vote needed: {proposal_id}")
   ```

**Deliverable:** Tokens awarded to contributors; governance votes tracked
**Time:** 2.5 hours

---

## WEEK 6: Web Verifier

### Day 36-38: Go Backend API
**Goal:** Create REST API for verifying any entity, action, or model

**Task:**
1. Create `verifier/backend/main.go`:
   ```go
   package main
   
   import (
       "encoding/json"
       "net/http"
       "github.com/gorilla/mux"
   )
   
   func main() {
       r := mux.NewRouter()
       
       // State verification
       r.HandleFunc("/api/v1/verify/entity/{entity_id}", verifyEntity).Methods("GET")
       
       // Action verification
       r.HandleFunc("/api/v1/verify/action/{action_id}", verifyAction).Methods("GET")
       
       // Model verification
       r.HandleFunc("/api/v1/verify/model/{model_version}", verifyModel).Methods("GET")
       
       // Status
       r.HandleFunc("/api/v1/status", getStatus).Methods("GET")
       
       http.ListenAndServe(":8080", r)
   }
   
   func verifyEntity(w http.ResponseWriter, r *http.Request) {
       entityID := mux.Vars(r)["entity_id"]
       
       // Query IOTA for latest state
       state := getLatestState(entityID)
       
       response := map[string]interface{}{
           "entity_id": entityID,
           "verified": state != nil,
           "state": state,
           "timestamp": time.Now().Unix(),
       }
       
       json.NewEncoder(w).Encode(response)
   }
   ```

2. Build and run:
   ```bash
   cd verifier/backend && go build -o verifier-backend
   ./verifier-backend &
   ```

3. Test:
   ```bash
   curl http://localhost:8080/api/v1/verify/entity/device-1
   ```

**Deliverable:** API endpoints return valid JSON; queries IOTA correctly
**Time:** 2 hours

---

### Day 39-41: Next.js Frontend
**Goal:** Build web UI for verification queries

**Task:**
1. Create `verifier/frontend/pages/index.js`:
   ```javascript
   import React, { useState } from 'react';
   
   export default function Home() {
       const [entityID, setEntityID] = useState('');
       const [result, setResult] = useState(null);
       
       const handleVerify = async () => {
           const res = await fetch(`/api/verify/entity/${entityID}`);
           const data = await res.json();
           setResult(data);
       };
       
       return (
           <div className="container">
               <h1>UVI Verifier</h1>
               <input
                   type="text"
                   placeholder="Enter Device/Entity ID"
                   value={entityID}
                   onChange={(e) => setEntityID(e.target.value)}
               />
               <button onClick={handleVerify}>Verify</button>
               {result && (
                   <pre>{JSON.stringify(result, null, 2)}</pre>
               )}
           </div>
       );
   }
   ```

2. Create API proxy (`pages/api/verify.js`):
   ```javascript
   export default async function handler(req, res) {
       const { entityID } = req.query;
       const backendRes = await fetch(`http://localhost:8080/api/v1/verify/entity/${entityID}`);
       const data = await backendRes.json();
       res.status(200).json(data);
   }
   ```

3. Install and run:
   ```bash
   cd verifier/frontend && npm install
   npm run dev
   ```

4. Open http://localhost:3000

**Deliverable:** Web UI loads; can query and display results
**Time:** 2 hours

---

### Day 42: Deployment & Styling
**Goal:** Polish UI and prepare for production deployment

**Task:**
1. Add Tailwind CSS:
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init
   ```

2. Add styling:
   ```javascript
   <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
       <div className="container mx-auto p-8">
           <h1 className="text-4xl font-bold text-white mb-8">UVI Verifier</h1>
           <div className="bg-white rounded-lg shadow-xl p-8">
               {/* form and results */}
           </div>
       </div>
   </div>
   ```

3. Add loading states, error handling, shareable links

**Deliverable:** UI is polished; ready for public deployment
**Time:** 1 hour

---

## WEEK 7: Testing, Formal Verification & Security

### Day 43-44: Unit Tests (All Components)
**Goal:** Comprehensive unit tests for every module

**Task:**
1. Python tests:
   ```bash
   cd agent && python3 -m pytest tests/ -v
   cd ../aggregator && python3 -m pytest tests/ -v
   ```

2. Go tests:
   ```bash
   cd zk && go test ./... -v
   ```

3. Coverage:
   ```bash
   go test -cover ./...
   pytest --cov=agent tests/
   ```

**Deliverable:** >80% code coverage; all tests pass
**Time:** 3 hours

---

### Day 45-46: Integration Tests (Full Pipeline)
**Goal:** End-to-end test simulating multiple devices, aggregation, governance

**Task:**
1. Create `tests/test_integration.py`:
   ```python
   def test_full_federated_round():
       # 1. Start services
       docker_compose_up()
       
       # 2. Create 5 virtual devices
       devices = [FederatedTrainer(f"device-{i}") for i in range(5)]
       
       # 3. Train and submit
       for device in devices:
           grad = device.train_step(...)
           device.submit_gradient(grad)
       
       # 4. Aggregator processes
       time.sleep(10)
       latest_model = aggregator.get_latest_model()
       assert latest_model.version = 2
       
       # 5. Verify from web UI
       response = requests.get("http://localhost:8080/api/v1/verify/model/2")
       assert response.json()["verified"] == True
   ```

2. Run:
   ```bash
   ./tests/test_end_to_end.sh
   ```

**Deliverable:** Full pipeline test passes; all 5 devices → aggregation → verification
**Time:** 2 hours

---

### Day 47-48: Formal Verification of ZK Circuits
**Goal:** Ensure circuits have no information leaks, correct constraints

**Task:**
1. Use gnark's formal verification:
   ```go
   // zk/circuit/formal_test.go
   func TestStateCircuitFormalVerification(t *testing.T) {
       c := &StateTransitionCircuit{}
       compiled, err := frontend.Compile(ecc.BN254.ScalarField(), g16.NewBuilder, c)
       assert.NoError(t, err)
       
       // Check constraint count
       assert.Equal(t, 1000, compiled.GetNbConstraints())  // Expected
       
       // Verify no unused inputs leak information
       assert.True(t, allPrivateInputsUsed(compiled))
   }
   ```

2. Symbolic execution analysis (manually):
   - Old state input → must match old state hash
       - No direct leak of location
   - New state input → must match new state hash
   - Owner → must be same
   - Timestamp → must increase

3. Report: Document circuit constraints and properties

**Deliverable:** Formal verification completed; no information leaks detected
**Time:** 2 hours

---

### Day 49-50: Security Audit
**Goal:** Scan code for vulnerabilities, verify TPM security

**Task:**
1. Rust security:
   ```bash
   cd hardware && cargo audit
   # Check for vulnerabilities in dependencies
   ```

2. Go security:
   ```bash
   cd zk && gosec ./...
   ```

3. Python security:
   ```bash
   cd aggregator && bandit -r . -ll
   ```

4. TPM verification:
   ```bash
   tpm2_readpublic -c key.ctx  # Verify non-exportable
   ```

5. Create security report:
   - No critical vulnerabilities
   - Keys properly protected
   - No data leaks in proofs

**Deliverable:** Security audit completed; report shows no critical issues
**Time:** 2 hours

---

## WEEK 8: Documentation, CI/CD, Launch

### Day 51-52: Comprehensive Documentation
**Goal:** Write docs and record demo video

**Task:**
1. Complete README (already started)
2. Write API documentation:
   ```
   docs/API.md
   - GET /api/v1/verify/entity/{id}
   - GET /api/v1/verify/action/{id}
   - POST /api/v1/verify/model/{version}
   ```

3. Write architecture guide:
   ```
   docs/ARCHITECTURE.md
   - Layer descriptions
   - Message format specs
   - Proof generation flow
   ```

4. Record 5-minute demo video:
   - Show device startup
   - Train model locally
   - Submit proof to IOTA
   - Aggregator processes
   - Web UI verifies result

**Deliverable:** README, API docs, architecture guide, demo video recorded
**Time:** 3 hours

---

### Day 53-54: GitHub Actions CI/CD
**Goal:** Automate testing on every push

**Task:**
1. Create `.github/workflows/ci.yml`:
   ```yaml
   name: CI
   on: [push]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run tests
           run: |
             cd hardware && cargo test
             cd ../zk && go test ./...
             cd ../agent && python3 -m pytest tests/
   ```

2. Add status badge to README

3. Test by pushing dummy commit

**Deliverable:** CI/CD runs and passes on each commit
**Time:** 1 hour

---

### Day 55-56: Production Deployment
**Goal:** Deploy to public testnet and cloud

**Task:**
1. Switch to IOTA Testnet:
   ```python
   # config.json
   "iota_node": "https://api.testnet.shimmer.network"
   ```

2. Deploy backend (Render):
   ```bash
   # Create Dockerfile for verifier/backend
   ```

   Push to GitHub; Render auto-deploys

3. Deploy frontend (Vercel):
   ```bash
   # Vercel auto-deploys from GitHub
   ```

4. Update README with public URLs

**Deliverable:** Public verifier endpoint live; web UI accessible
**Time:** 2 hours

---

### Day 57-58: Launch & Community Engagement
**Goal:** Announce UVI to the world

**Task:**
1. Push everything to GitHub (public)
2. Write launch post on Medium/Dev.to
3. Post on:
   - HackerNews
   - Reddit (r/MachineLearning, r/crypto)
   - Twitter (tag @IOTA, @cryptography, @llms)
4. Create GitHub Discussions for questions

**Deliverable:** Project launched; community engagement started
**Time:** 2 hours

---

## Summary of Deliverables by Week

| Week | Milestone | Status |
|------|-----------|--------|
| 1 | Hardware identity, IOTA, gRPC skeleton | ✓ |
| 2 | State ZK circuit, key generation, proofs | ✓ |
| 3 | Action schema, action circuit, personal AI | ✓ |
| 4 | PyTorch trainer, gradient proofs, DAG submission | ✓ |
| 5 | Aggregator listening, proof verification, DAO | ✓ |
| 6 | Web API, Next.js frontend, deployment ready | ✓ |
| 7 | Tests, formal verification, security audit | ✓ |
| 8 | Docs, CI/CD, public launch | ✓ |

---

## Validation Matrix (Complete)

See [VALIDATION.md](VALIDATION.md) for detailed testing procedures per day.

---

## Total Time Investment

- 57 working days
- 8-10 hours/day
- **Total: 456-570 hours** (~12-14 weeks at full-time pace)
- Or **8 weeks at 10 hours/day + weekends**

---

## Estimated Outcomes

✅ Prototype of verifiable decentralized AI training system
✅ 3,000+ lines of production-ready code
✅ ZK circuits for state, action, gradient proofs
✅ Working aggregator with governance
✅ Public web verifier
✅ Full documentation and demo
✅ Community engagement and GitHub stars

---

🚀 **Start Day 1. Build the future.**
