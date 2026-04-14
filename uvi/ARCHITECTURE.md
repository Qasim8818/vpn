# UVI Architecture Guide – Technical Deep Dive

## Table of Contents
1. System Layers
2. Component Interaction
3. Data Structures
4. Cryptographic Primitives
5. Message Format Specifications
6. Verification Procedures
7. Scalability & Performance

---

## 1. System Layers (Detailed)

### Layer 1: Identity & State (GVEN)

**Purpose:** Every entity (device, agent, user) has a cryptographic identity rooted in hardware.

**Components:**
- TPM 2.0: Hardware root of trust
- Dilithium: Post-quantum signature algorithm
- Device ID: SHA256(TPM public key)

**Data Structure:**
```python
@dataclass
class EntityIdentity:
    device_id: str              # sha256(tpm_pubkey)
    tpm_pubkey: bytes           # 32 bytes
    dilithium_pk: bytes         # 1,312 bytes
    dilithium_sk: bytes         # 2,544 bytes (encrypted in TPM)
    created_at: int             # Unix timestamp
    trusted_until: int          # Expiry (optional)
```

**State Representation:**
```python
@dataclass
class EntityState:
    device_id: str
    version: int                # Incremented per transition
    properties: Dict[str, Any]  # location, ownership, permissions, etc.
    timestamp: int
    proof_hash: str             # ZK proof that matches this state
    signature: bytes            # Dilithium signature over proof
```

**State Transition:** A device moves from State V to State V+1 by:
1. Creating new state snapshot
2. Computing hash of new state
3. Generating ZK proof (circuit verifies state transition was valid)
4. Signing proof with Dilithium
5. Submitting to IOTA under index `state:v{n+1}:{device_id}`

---

### Layer 2: AI Actions (VPAIN)

**Purpose:** Personal/industrial AI agents produce verifiable, policy-compliant actions.

**Components:**
- LLM (local, via Ollama)
- Action Schema
- Policy Engine
- ZK Action Compliance Circuit

**Action Representation:**
```python
@dataclass
class Action:
    action_id: str              # UUID
    action_type: str            # "send_email", "read_file", "execute_code", etc.
    actor: str                  # Device ID of agent
    target: str                 # Recipient, resource, or command
    parameters: Dict            # Action-specific params
    timestamp: int
    policy_hash: str            # Hash of policy that allows this
    policy_id: str              # Which policy applied
```

**Policy Representation:**
```python
@dataclass
class Policy:
    policy_id: str              # UUID
    version: int
    allowed_actions: List[str]  # ["send_email", "read_file"]
    rate_limits: Dict           # {"send_email": 10/hour}
    resource_whitelist: List    # Allowed targets
    hash: str                   # SHA256 of entire policy
```

**Execution Flow:**
1. User requests action: "Send email to Bob"
2. LLM decides: Action = send_email(target="bob@example.com")
3. Policy engine checks: Is send_email allowed?
   - Yes → proceed
   - No → reject, return error
4. ZK circuit generates proof:
   - Input: action_hash, policy_hash (public)
   - Private witness: action details, policy ID
   - Proves: "This action is allowed by this policy without revealing action details"
5. Sign proof with Dilithium
6. Submit to IOTA under index `action:v{n}:{actor_id}`
7. Execute action (with proof in audit log)

---

### Layer 3: Collaborative Training (VDAI)

**Purpose:** Devices train AI models locally, share ZK-proven gradients, aggregate globally.

**Components:**
- PyTorch Trainer (local)
- Gradient Hasher (deterministic)
- ZK Gradient Proof Circuit
- Aggregator (collects & averages gradients)

**Gradient Submission Flow:**
```
Device trains on local batch
    ↓
Computes gradient hash (deterministic)
    ↓
Generates ZK proof:
  - Public: gradient_hash, batch_hash, batch_size
  - Private: actual data points (hashed)
  - Proves: "gradient was computed from valid data"
    ↓
Signs proof with Dilithium
    ↓
Submits to IOTA under index `gradient:v{n}:{device_id}`
```

**Gradient Aggregation:**
1. Aggregator polls IOTA for new gradients
2. For each gradient:
   - Verify ZK proof
   - Verify signature
   - If valid: add gradient to buffer
3. Once buffer has ≥N gradients (or timeout):
   - Fetch gradient vectors (shared via side channel or in plaintext for MVP)
   - Average them: `global_gradient = mean(g1, g2, ..., gN)`
   - Update model: `weights -= learning_rate * global_gradient`
   - Compute new model hash: `new_hash = sha256(model_weights)`
   - Submit to IOTA under index `model:v{n+1}`
4. Governance: DAO votes to approve new model

---

### Layer 4: Governance (DAO)

**Purpose:** Decentralized decision-making for model updates, disputes, incentives.

**Components:**
- Token Ledger (device → balance)
- Proposal System
- Voting Mechanism
- Treasury

**Governance Flow:**
```
Aggregator produces new model v2
    ↓
Proposer creates governance proposal:
  - Model hash: abc123
  - Reason: "10 devices trained for 100 rounds"
    ↓
Voting period (48-72 hours):
  - Each device votes with token weight
  - vote_power = sqrt(device_token_balance)  # Prevent whale dominance
    ↓
Tally votes:
  - If votes_for > votes_against: APPROVED
  - Else: REJECTED, try next round
    ↓
If approved: Update global model hash on IOTA
If rejected: Discard, continue with previous model
```

**Token Mechanics:**
- Initial distribution: Equal to all participants (1 token each)
- Rewards: +1 token per valid gradient submitted
- Voting power: sqrt(balance) to prevent whale attacks
- Staking: Optional, devices can lock tokens for higher voting power

---

## 2. Component Interaction

### Message Flow Diagram

```
USER
  ↓ (request)
PERSONAL AI AGENT (LLM decides action + ZK proof)
  ↓ (action + proof + signature)
IOTA DAG (index: action:{version}:{actor_id})
  ↓ (poll)
AGGREGATOR (verifies + executes + rewards)
  ↓ (state update)
GOVERNANCE DAO (votes on new models)
  ↓ (approved model hash)
IOTA DAG (index: model:{version})
  ↓ (query)
WEB VERIFIER (anyone can verify)
```

### Request/Response Cycle (State Transition)

```
Device State Update:
  Request: UpdateStateRequest {
    device_id: "dev-1",
    old_state_hash: "abc...",
    new_state: {location: "us-east", owner: "Alice"},
    timestamp: 1712345600
  }
  ↓
Prover (gRPC):
  Generates ZK proof using circuit
  Returns: ProofResponse {
    proof: [1024 bytes],
    proof_hash: "def..."
  }
  ↓
TPM Signer (Rust):
  Signs proof hash with Dilithium
  Returns: SignatureResponse {
    signature: [2560 bytes],
    device_id: "dev-1",
    public_key: "pk..."
  }
  ↓
IOTA Submitter:
  Creates message with proof + signature
  Submits to IOTA under index "state:v1:dev-1"
  Returns: MessageID "iotaledger/..."
  ↓
Verification (from web verifier):
  Request: GET /api/verify/entity/dev-1
  ↓
Verifier fetches from IOTA:
  Message = IOTA.getMessages("state:v?:dev-1")
  ↓
Verifies proof:
  is_valid = verify_zk_proof(message.proof, public_inputs)
  is_signed = verify_signature(message.signature, message.proof, device_pk)
  ↓
Response: VerifyResponse {
    entity_id: "dev-1",
    verified: true,
    current_state: {location: "us-east", owner: "Alice"},
    last_update: 1712345600,
    proof_hash: "def..."
  }
```

---

## 3. Data Structures (Complete Specification)

### IOTA Message Payload

**Index Format:** `{layer}:{version}:{actor_id}`
- layer: state, action, gradient, model
- version: v1, v2, etc.
- actor_id: device_id or aggregator_id

**Payload Structure (JSON):**

```json
{
  "type": "state_transition",
  "version": "1.0",
  "data": {
    "device_id": "device-abc123",
    "state_hash": "sha256-hex",
    "property_deltas": {
      "location": "us-west-2",
      "owner": "Alice"
    },
    "timestamp": 1712345600,
    "nonce": 12345
  },
  "proof": {
    "proof_bytes": "base64-encoded-1024-bytes",
    "proof_hash": "sha256-hex",
    "circuit_type": "state_transition",
    "public_inputs": {
      "old_state_hash": "...",
      "new_state_hash": "..."
    }
  },
  "signature": {
    "algorithm": "dilithium2",
    "signature_bytes": "base64-encoded-2560-bytes",
    "public_key": "base64-encoded-1312-bytes",
    "signer_device_id": "device-abc123"
  }
}
```

### ZK Circuit Public/Private Inputs

**State Transition Circuit:**
```
Public Inputs:
  - old_state_hash: Fr (field element)
  - new_state_hash: Fr
  - timestamp: Fr
  
Private Inputs (secret):
  - old_location: Fr
  - old_owner: Fr
  - new_location: Fr
  - new_owner: Fr
  - transition_timestamp: Fr
  
Constraints:
  - hash(old_location, old_owner) == old_state_hash
  - hash(new_location, new_owner) == new_state_hash
  - old_owner == new_owner (ownership doesn't change)
  - transition_timestamp < timestamp + 1000 (not too old)
```

---

## 4. Cryptographic Primitives

### Post-Quantum Signatures (Dilithium)

**Why Dilithium:**
- NIST FIPS 204 approved (quantum-resistant)
- 2.5KB public key, 4.4KB private key
- Signature: 2560 bytes
- Secure until 2050+ even with quantum computers

**Integration:**
```rust
// In hardware/src/dilithium.rs
pub fn generate_keys() -> (PublicKey, SecretKey) {
    // Key generation (deterministic from TPM seed)
}

pub fn sign(message: &[u8], sk: &SecretKey) -> Signature {
    // Deterministic signature (RFC 8032 style)
}

pub fn verify(sig: &Signature, pk: &PublicKey, msg: &[u8]) -> bool {
    // Constant-time verification
}
```

### Hash Functions

**Primary:** SHA-256 (for compatibility, short-term)
**Circuit:** MiMC hash (for ZK efficiency in circuits)

```python
# MiMC is ~10x cheaper in constraints than SHA-256
# Trade-off: 1024 constraints vs 20,000 constraints

# For on-chain state: use SHA-256 for trust
# For circuit constraints: convert to MiMC field element
```

### Zero-Knowledge Proofs (Groth16)

**Proof System:** Groth16 (Ethereum standard)
- Proof size: 1-2 KB
- Verification cost: ~3 pairing checks
- Setup: Trusted ceremony (performed once)

**Constraint Complexity:**
- State circuit: ~1,000 constraints
- Action circuit: ~500 constraints
- Gradient circuit: ~2,000 constraints

---

## 5. Message Format Specifications

### Canonical Serialization (for hashing)

All structures serialized in deterministic order:

```python
def serialize_state(state: EntityState) -> bytes:
    """Canonical form for hashing"""
    return (
        state.device_id.encode() +
        state.version.to_bytes(8, 'big') +
        json.dumps(state.properties, sort_keys=True).encode() +
        state.timestamp.to_bytes(8, 'big')
    )

def hash_state(state: EntityState) -> str:
    return sha256(serialize_state(state)).hexdigest()
```

### Protocol Buffers (for gRPC)

```protobuf
service Prover {
  rpc GenerateStateProof(StateProofRequest) returns (StateProofResponse);
  rpc GenerateActionProof(ActionProofRequest) returns (ActionProofResponse);
  rpc GenerateGradientProof(GradientProofRequest) returns (GradientProofResponse);
}

message StateProofRequest {
  string old_state_hash = 1;
  string new_state_hash = 2;
  int64 timestamp = 3;
  string old_location = 4;
  string new_location = 5;
  string owner = 6;
}

message StateProofResponse {
  bytes proof = 1;
  string proof_hash = 2;
  bool success = 3;
}
```

---

## 6. Verification Procedures

### Entity State Verification (Public)

```python
def verify_entity_state(entity_id: str) -> bool:
    """Verify that an entity's current state is valid"""
    
    # 1. Fetch latest state message from IOTA
    messages = iota.get_messages(f"state:v?:{entity_id}")
    latest = messages[-1]  # Most recent
    
    # 2. Parse message
    data = parse_iota_message(latest)
    
    # 3. Verify ZK proof
    vk = load_verifying_key("state_vk.bin")
    is_proof_valid = verify_groth16(
        data.proof,
        vk,
        public_inputs={
            "old_state_hash": data.old_state_hash,
            "new_state_hash": data.new_state_hash,
        }
    )
    
    # 4. Verify signature
    is_sig_valid = verify_dilithium(
        data.signature,
        data.public_key,
        data.proof
    )
    
    # 5. Verify timestamp (not too old)
    is_fresh = (time.time() - data.timestamp) < 86400  # 24h
    
    return is_proof_valid and is_sig_valid and is_fresh
```

### Model Version Verification

```python
def verify_model_version(model_version: int) -> bool:
    """Verify that a model version is correctly aggregated"""
    
    # 1. Fetch model announcement from IOTA
    model_msg = iota.get_message(f"model:v{model_version}")
    
    # 2. Fetch all contributor gradients
    gradient_msgs = iota.get_messages(f"gradient:v{model_version}")
    
    # 3. For each gradient, verify proof
    valid_gradients = []
    for gmsg in gradient_msgs:
        if verify_zk_proof(gmsg.proof) and verify_signature(gmsg.signature):
            valid_gradients.append(gmsg)
    
    # 4. Check that aggregated result matches announed model
    aggregated_hash = compute_model_hash(valid_gradients)
    announced_hash = model_msg.model_hash
    
    return aggregated_hash == announced_hash
```

---

## 7. Scalability & Performance

### Throughput Analysis

**Single Device (Local):**
- Train 1 epoch (10 batches): 100s
- Gradient proof generation (per batch): 1-2s
- IOTA submission rate: 10 proofs/min

**Network (10 devices):**
- All submit gradients simultaneously
- Aggregator processes in parallel
- Throughput: ~60-100 proofs/min (limited by proof generation, not IOTA)

**Scaling Solutions:**

1. **Batched Proofs:** Generate one proof for 10 gradients
   - Reduces proof generation time by 5x
   - Still verifiable

2. **Sharded Aggregation:** Multiple aggregators per model version
   - Each shard handles devices [0-100], [100-200], etc.
   - Meta-aggregator combines shards
   - Scales to 1000+ devices

3. **Proof Caching:** Reuse proofs for identical gradients
   - If two devices compute same gradient, one proof suffices
   - Saves 50% proof generation in many cases

---

## Appendix: Circuit Formal Specification

### State Transition Circuit (Formal)

```
Inputs:
  public: H_old, H_new, T
  private: L_old, L_new, O, δT
  
Constraints:
  1. MiMC(L_old || O) = H_old
  2. MiMC(L_new || O) = H_new
  3. T ≥ δT (timestamp is fresh)
  4. T < δT + 86400 (timestamp not too old)
  
Prove: The transition from old state to new state is valid
       without revealing locations or ownership.
```

### Gradient Proof Circuit (Formal)

```
Inputs:
  public: H_grad, H_batch, n
  private: x_1, ..., x_n (data points)
  
Constraints:
  1. count(x_i) = n
  2. MiMC(x_1 || ... || x_n) = H_batch
  3. n ≥ 1 (non-empty batch)
  4. n ≤ 1000 (reasonable batch size)
  
Prove: The gradient was computed from n valid data points
       without revealing the data.
```

---

**Version:** 1.0.0  
**Status:** Complete
**Last Updated:** April 2026
