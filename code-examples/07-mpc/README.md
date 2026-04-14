# Multi-Party Computation (MPC) — Distributed VPN Key Management

## Problem Statement

**Standard VPN:** One HSM holds the private key. Compromise the HSM = compromise the VPN.  
**MPC approach:** Split the key across N servers (e.g., 5). Any T can cooperate to sign (e.g., 3-of-5).  
**Result:** Attacker must compromise T+ servers *simultaneously* to steal key material.

## How It Works

### Threshold Secret Sharing (Shamir)

```
Private key: k
Split into 5 shares: s1, s2, s3, s4, s5
  - Each share is mathematically random
  - Any 3 shares → recover k
  - Any 2 shares → learn NOTHING about k (information-theoretically secure)

Fire an HSM: server loses s2 → k still secure (need 2 more)
Seizure of 2 servers: s1 + s3 → k still secure (need 1 more)
Compromise 3 servers: s1 + s3 + s5 → k compromised (equal to 3-of-5 threshold)
```

### Threshold ECDSA (MPC Signing)

```
Goal: Sign messages without ever reconstructing k in any single location

Process:
1. Each server holds share[i]
2. To sign: all servers execute distributed protocol
3. Each contributes: Commitment + signature partial + proof of correctness
4. Combine partials → valid signature
5. Full key k NEVER assembled in memory
```

## Security Properties

| Property | Guarantees |
|----------|-----------|
| **Key Confidentiality** | Each server has only one share; no single point compromise |
| **Signature Validity** | Signature produced = authentic (normal ECDSA verification) |
| **Threshold Enforcement** | Exactly T servers required; fewer = no signature |
| **Share Unforgeability** | Attacker can't forge a valid share without original private key |
| **No Reconstruction** | Distributed signing = key shares never combined in memory |

## When to Use MPC

✅ **Good for:**
- Government/military VPN services (require key distribution)
- High-value infrastructure (target = attacker effort)
- Compliance requirements (HSM elimination, key rotation)
- Geographic distribution (keys in different jurisdictions)
- Defense against insider threats (no single person has full key)

⚠️ **Tradeoffs:**
- Signing latency increases: ~100–300ms (vs ~1ms single HSM)
- Network between servers must be secure (trusted channels)
- Complexity: 3–6 months of engineering
- Cost: $500K–$2M for enterprise deployment

❌ **Bad for:**
- High-frequency trading (latency-sensitive)
- Single-server setup (defeats purpose; adds complexity)
- Rapid key rotation (re-sharing is expensive)

## Implementation Options

### **Shamir Secret Sharing (Simplest)**
- Split k into n shares via polynomial evaluation
- Any t shares → recover k via Lagrange interpolation
- ⚠️ Problem: Reconstruction puts full key in RAM
- Use for: Offline key distribution, backup recovery

### **Feldman VSS (Secure Distribution)**
- Like Shamir, but with commitments (proofs of correctness)
- Each share is cryptographically verifiable
- Prevents malicious servers from distributing invalid shares
- Use for: Initial key distribution in untrusted channels

### **Threshold ECDSA (Distributed Signing)**
- Combines threshold signing with ECDSA
- Key NEVER reconstructed — distributed protocol
- Each server contributes a partial signature
- Partials combine → valid Signature
- Use for: Production VPN signing (no key reconstruction)

### **MPC Frameworks**
| Framework | Language | Type | Effort |
|-----------|----------|------|--------|
| **tss-lib** | Go | Threshold ECDSA | 1–2 weeks integration |
| **Fireblocks SDK** | TypeScript | MPC signing service | SaaS (no code) |
| **dfinity/vetkd** | Rust | Verifiable encryption | Academic |
| **MP-SPDZ** | C++ | General MPC | Research (not prod) |

### For VPN: tss-lib (Go)

```bash
import "github.com/bnb-chain/tss-lib/v2"

# Use case: 3-of-5 ECDSA signing
1. Run keygen offline: each server generates share
2. Publish commitments (public data)
3. Each signing request: servers execute distributed protocol
4. Nobody ever sees the full key
```

## Real-World Deployments

### **Kraken Exchange** (Cryptocurrency)
- 3-of-5 threshold key management for hot wallets
- MPC-based signing reduces theft risk: compromised 1–2 servers = nothing

### **Mullvad VPN** (Proposed)
- Exploring MPC for key distribution
- Goal: Even Mullvad staff can't read user traffic (no master key access)

### **Cold Card** (Hardware Wallet)
- Supports Shamir shares: split key into 5 shares on 5 devices
- Any 3 needed to sign transactions

## Deployment Checklist

- [ ] Choose threshold (t-of-n): 3-of-5 is common
- [ ] Select MPC library (tss-lib for Go; others for different languages)
- [ ] Generate master key and distribute shares (offline, manual process)
- [ ] Secure share storage: each server has isolated ciphertext on disk
- [ ] Set up signing orchestrator (coordinates protocol between servers)
- [ ] Network security: TLS + mutual auth between servers (no untrusted networks)
- [ ] Testing: sign with minimum threshold (t servers), verify it fails with t-1
- [ ] Monitoring: alert if signing requests timeout (network issues)
- [ ] Key rotation: schedule share re distribution (expensive, do quarterly)
- [ ] Disaster recovery: backup shares in physically separate locations

## Threat Model Analysis

### Compromise Scenarios

**Attacker seizes 1 server → 0 key material acquired**
- Single share is mathematically useless
- Continue operation with remaining 4 servers

**Attacker compromises 2 servers (0-day, malware) → 0 key material**
- Still 3 short of threshold
- Continue operation, plan re-keying for month 2

**Persistent APT: monthly 0-day supply, compromises 3 servers → KEY COMPROMISED**
- Threshold exceeded
- Activate incident response: rotate keys, expire old signatures
- MPC doesn't prevent this, but increases cost/complexity

**Insider threat: employee hands keys to adversary**
- Insider has only 1 share (random data to them)
- Accomplice must separately compromise 2 more servers
- Detectability: sharing conversations = red flag

## Comparison: MPC vs. Alternatives

| Approach | Security | Latency | Cost | Complexity |
|----------|----------|---------|------|------------|
| **Single HSM** | High* | 1ms | Low | Low |
| **MPC (3-of-5)** | Very High | 100–300ms | Medium | High |
| **Distributed CA** | High | 10ms | Medium | Medium |
| **Hardware Wallets** | Very High | Minutes | Low | Manual |

*Single HSM = high for theft, low for policy/compliance

## References

- **Shamir (1979):** "How to Share a Secret" — foundational
- **Feldman (1987):** Verifiable Secret Sharing
- **Gennaro et al. (2016):** "Fast Secure Multiparty ECDSA with Practical ZK Proofs"
- **tss-lib GitHub:** https://github.com/bnb-chain/tss-lib (Go implementation)

---

**TL;DR:** MPC distributes signing across N servers so attacker must compromise T+ simultaneously. 3-of-5 is practical; adds ~200ms latency. Worth it for high-value VPN infrastructure where HSM compromise is a real threat.
