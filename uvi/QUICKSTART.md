# UVI Quick Start Guide

## What is UVI?

**Universal Verifiable Intelligence** combines:
- ✅ Hardware-bound identities (GVEN)
- ✅ Verifiable AI actions (VPAIN)  
- ✅ Collaborative federated learning (VDAI)
- ✅ Decentralized governance (DAO)

All secured with **post-quantum cryptography**, **zero-knowledge proofs**, and anchored on a **feeless DAG (IOTA)**.

---

## 5-Minute Setup

### 1. Prerequisites
```bash
python3 --version        # 3.10+
pip --version           # 23+
docker --version        # 24+
```

### 2. Install Dependencies
```bash
cd /home/killer123/Desktop/vpn/uvi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Run Examples
```bash
# Demo 1: Unified Agent with state, actions, gradients
python3 examples/demo_unified_agent.py

# Demo 2: Training & Gradient Submission
python3 examples/demo_trainer.py

# Demo 3: Aggregation
python3 examples/demo_aggregation.py
```

### 4. View Architecture
```bash
cat ARCHITECTURE.md
```

---

## Core Concepts

### Layer 1: Identity & State
- Every device has a TPM-rooted identity
- State changes are ZK-proven and anchored on IOTA
- Example: Device location update from "us-west" → "us-east"

### Layer 2: AI Actions
- Personal AI agents decide actions based on user requests
- Policy engine ensures compliance
- ZK proofs hide action details while proving compliance
- Example: "Send email" → LLM decides → Policy checks → ZK proof → Execute

### Layer 3: Collaborative Training
- Devices train models locally on private data
- Gradient updates are ZK-proven (no data revealed)
- Aggregator collects and verifies proofs
- Example: 100 devices → individual gradients → verified → aggregated model

### Layer 4: Governance
- Token-based voting on model updates
- Device rewards for valid contributions
- DAO decides which models to accept
- Example: Device contributes gradient → earns token → votes on next model

---

## Running the Full Stack

### Option 1: Docker Compose (Recommended)
```bash
cd uvi
docker-compose up -d

# Verify all services running
docker-compose ps
```

### Option 2: Manual (For Development)

Terminal 1 – IOTA Node:
```bash
docker run -d --name iota-node -p 14265:14265 iotaledger/hornet
```

Terminal 2 – ZK Prover:
```bash
cd zk && go run prover/server.go
```

Terminal 3 – Agent:
```bash
python3 agent/uvi_agent.py
```

Terminal 4 – Training:
```bash
python3 agent/trainer.py
```

Terminal 5 – Aggregator:
```bash
python3 aggregator/aggregator.py
```

---

## Example: End-to-End Flow

```python
from agent.uvi_agent import UVIAgent

# Create agent
agent = UVIAgent("device-001")

# 1. Initialize state
agent.initialize_state({
    "location": "us-west-2",
    "owner": "Alice"
})

# 2. Update state (generates ZK proof)
agent.update_state_with_proof({"location": "us-east-1"})

# 3. Execute AI action (generates ZK proof of policy compliance)
agent.execute_action_with_proof("Send email to Bob with the report")

# 4. Contribute to federated learning
agent.contribute_gradient_with_proof(
    gradient_hash="abc123...",
    batch_hash="def456...",
    batch_size=32,
    model_version=1
)
```

---

## Verification (Public API)

You can verify any entity, action, or model from the web:

```bash
# Verify entity state
curl http://localhost:8080/api/verify/entity/device-001

# Verify action
curl http://localhost:8080/api/verify/action/action-uuid

# Verify model
curl http://localhost:8080/api/verify/model/v1
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│       Device (Your Laptop)                  │
│  ┌───────────────────────────────────────┐  │
│  │ TPM (Hardware Identity)                │  │
│  │ ↓                                       │  │
│  │ UVI Agent (State, Actions, Training)  │  │
│  │ ↓                                       │  │
│  │ ZK Prover (Generates proofs)          │  │
│  │ ↓                                       │  │
│  │ IOTA Submitter (Anchors proofs)       │  │
│  └───────────────────────────────────────┘  │
└─────────────────────┬───────────────────────┘
                      │ (ZK proofs + signatures)
                      ▼
        ┌─────────────────────────┐
        │   IOTA DAG (Feeless)    │
        │  (Stores all proofs)    │
        └───────────┬─────────────┘
                    │ (polling)
                    ▼
        ┌─────────────────────────┐
        │   Aggregator            │
        │ (Verifies & aggregates) │
        └───────────┬─────────────┘
                    │ (new model)
                    ▼
        ┌─────────────────────────┐
        │   Governance (DAO)      │
        │ (Voting & rewards)      │
        └──────────────────────────┘
```

---

## Testing

### Unit Tests
```bash
pytest agent/tests/ -v
pytest aggregator/tests/ -v
```

### Integration Test
```bash
bash tests/test_end_to_end.sh
```

### Formal Verification (ZK Circuits)
```bash
cd zk && go test ./circuit -v
```

---

## Deployment

### Local Development
```bash
docker-compose up -d
python3 examples/demo_unified_agent.py
```

### Production (IOTA Mainnet)

1. Update config to point to mainnet:
   ```python
   IOTA_URL = "https://api.iota.org"
   ```

2. Deploy aggregator to cloud:
   ```bash
   # Render.com, Heroku, AWS, etc.
   ```

3. Deploy verifier frontend:
   ```bash
   # Vercel.com
   ```

---

## FAQ

**Q: What's the point of ZK proofs?**
A: Prove validity without revealing data. Device can prove gradient came from training without revealing training data.

**Q: Is this quantum-safe?**
A: Yes. Dilithium signatures are NIST-approved post-quantum crypto. Safe until 2050+.

**Q: How many devices can this handle?**
A: MVP: 10-100 devices. With optimizations (batching, sharding): 1000+ devices.

**Q: How do I earn tokens?**
A: Submit valid gradients. Each valid submission = +1 token. Use tokens to vote on models.

**Q: Can big tech replicate this?**
A: No. They would have to abandon centralized data collection. Federated learning + ZK proofs require decentralization.

---

## Next Steps

1. **Read ARCHITECTURE.md** for technical deep-dive
2. **Read 8WEEK_PLAN.md** for implementation roadmap
3. **Run examples/** to see features in action
4. **Run tests/** to verify everything works
5. **Modify agent/trainer.py** to train your own models
6. **Deploy** to production for real federated learning

---

## Support

- **Issues?** Open GitHub issue
- **Questions?** Check ARCHITECTURE.md
- **Contributing?** See CONTRIBUTING.md

---

🚀 **Start building verifiable, decentralized AI today!**

---

**Version:** 1.0.0  
**Status:** Alpha (Ready for Development)  
**Last Updated:** April 2026
