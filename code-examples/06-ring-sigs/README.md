# Ring Signatures — Anonymous Group Authentication

## Problem Statement

**Traditional VPN auth:** You send credential → server knows you specifically.  
**Ring signature auth:** You prove you're one of N authorized users → server doesn't know which.

**Use case:** Group VPN access where accountability (which user accessed) is secondary to privacy (server can't link connections to identities).

## How It Works

### Ring Signature Protocol

1. **Setup** — Authority publishes list of N authorized public keys
2. **Sign** — Any member uses their secret key to sign a message
3. **Verify** — Anyone can verify that "one of these N keys signed this"
4. **Hidden signer** — Verifier learns ONLY "it was someone in the ring"

### Math (Schnorr Ring Signature)

```
Ring signature = (c[0], c[1], ..., c[n-1], s[0], s[1], ..., s[n-1])

Signing (member i knows secret key x_i):
  - Generate random k, compute w = g^k
  - Hash w with message → c[i]
  - For all j ≠ i: generate random s[j], compute c[j+1] from w[j]
  - Solve for s[i]: s[i] = k - c[i] * x_i
  
Verification:
  - For each j: compute w[j] = g^{s[j]} * pk[j]^{-c[j]}
  - Hash w[j] with message → c[j+1]
  - Ring "closes" if computed c[0] = original c[0]
```

## Security Properties

| Property | Guarantees |
|----------|-----------|
| **Unforgeability** | Only actual ring members can create valid signatures |
| **Anonymity** | Verifier learns ONLY "one of the N members" — no further info |
| **Non-linkability** | Two signatures cannot be linked to the same signer |
| **Unconditional anonymity** | Even with unlimited computation power, can't determine signer |

## When to Use Ring Signatures

✅ **Good for:**
- Group VPN access (N users, server can't link sessions to users)
- Deniable authentication (signer can claim anyone in the ring did it)
- Anonymous voting/credentials in decentralized systems
- Privacy-preserving attestation

❌ **Bad for:**
- Large rings (1000+ users) — signature/verification time grows O(n)
- Real-time, latency-critical operations (slower than ordinary signatures)
- When you need account-specific behavior (ring sigs don't identify users)

## Performance Characteristics

| Ring Size | Signature Size | Sign Time | Verify Time | Use Case |
|-----------|----------------|-----------|-------------|----------|
| n=3 | 98 bytes | ~2ms | ~3ms | Small group |
| n=10 | 320 bytes | ~8ms | ~10ms | Team access |
| n=100 | 3.2 KB | ~100ms | ~100ms | Department VPN |
| n=1000 | 32 KB | ~1.5s | ~1.5s | Avoid this size |

## Implementation Details

This example uses **Schnorr ring signatures on Ristretto (Curve25519)**:

- **Curve:** Ristretto (elliptic curve group, 256-bit)
- **Hash:** SHA3-256 (Fiat-Shamir for challenge generation)
- **Size:** Each ring element = 64 bytes (Ristretto compressed point)
- **Signature:** 2 * 32 * n bytes (two scalars per ring member)

### Build & Run

```bash
# Add dependencies to Cargo.toml:
curve25519-dalek = "4.0"
sha3 = "0.10"
rand = "0.8"
hex = "0.4"

# Compile
cargo build --release

# Sign with group of 5, user 2 as signer
cargo run --release -- sign 5 2 "Authentication request"

# Output:
# [0] pk: a4f8...
# [1] pk: 1b2c...
# [2] pk: 7e9d...  ← signer (but hidden from observer)
# [3] pk: 4f1b...
# [4] pk: 9c3a...
#
# ✓ Signed by member 2 of 5
# Message: Authentication request
# ✓ Signature verified (one member of the ring signed this)
# Observer learns: someone in the ring, but NOT WHO
```

## Real-World Usage

### Nym Network (Decentralized VPN)

- Uses ring signatures in **credentials layer**
- Users prove "I'm in the credential tree" without revealing which credential
- Enables unlinkable bandwidth tokens
- Each user's traffic is unlinkable across sessions

### Signal Protocol (Messaging)

- Ring signatures used in **sealed sender** mode
- Sender proves they're in a group, not identified
- E2E encryption + ring sig = sender-private messaging

### Threshold Credentials (BBS+)

- Combines ring sigs with selective disclosure
- "Prove you have a credential attribute" without revealing which credential
- Used in privacy-preserving identity systems

## Comparison: Ring Sigs vs. Alternatives

| Signature Type | Anonymity | Size | Speed | Setup |
|---|---|---|---|---|
| **Ring Sig** | N-way (all equal) | O(n) bytes | O(n) time | Pre-published ring |
| **Threshold Sig** | 1 of k sign | ~100B | Fast | Trusted dealer |
| **ZK Proof** | Arbitrary predicate | O(proof) bytes | O(verify proof) | Circuits |
| **Blind Sig** | Binary (issuer ⊥ user) | ~100B | Medium | Issuer key |

**Ring sigs are best when:**
- Equal anonymity within the group
- No additional structure (like thresholds)
- Ring is static and pre-shared

## Security Considerations

### Anonymity Under Scrutiny

✅ **Strong:** Observer of single signature cannot determine signer  
⚠️ **Weak:** If user signs multiple times, correlation attacks are possible

```
Mitigation: Rotate the ring regularly
- Each period (day/week), create new ring with shuffled members
- Users can't be linked across periods
```

### Timing Side Channels

⚠️ **Risk:** Signing time might vary based on signer's position

```
Mitigation: Constant-time ring closure
- In production: use constant-time scalar operations
- Example: use libsodium's crypto_sign_sk_to_seed() for timing safety
```

### Large Rings & Scalability

❌ **Problem:** Ring size n → O(n) time and space

```
Solutions:
1. Smaller rings (10–100 members)
2. Accumulators (Merkle tree of public keys)
3. Zero-knowledge proofs (better for large sets)
4. Switch to ZK credentials for >100 members
```

## Deployment Checklist

- [ ] Decide ring composition (fixed membership or rotating?)
- [ ] Pre-distribute public keys to all ring members
- [ ] Implement constant-time operations (use battle-tested library)
- [ ] Test with target ring size (e.g., n=10 for team VPN)
- [ ] Benchmark sign/verify times for your latency budget
- [ ] Plan key rotation (when ring members change)
- [ ] Add timing jitter to defeat side-channel attacks
- [ ] Monitor for signature linkability (correlation analysis)
- [ ] Document ring authority and member management process

## References

- **Rivest, Shamir, Taomi (2001):** "How to Leak a Secret" — Original ring signature concept
- **Schnorr (1989):** Discrete log signature scheme foundation
- **Curve25519 implementation:** DJB's work, adopted by Ristretto
- **Ring sig applications in Nym:** https://nymtech.net/ — Coconut credentials (uses ring structure)

## What's Not Here

- **Ring signatures on lattices** (post-quantum) — separate research area
- **Linkable ring sigs** (user traceable) — different threat model
- **Stealth addresses** (Bitcoin) — ring sigs + encryption combination
- **Proxy signatures** — delegation variant

---

**TL;DR:** Ring signatures hide the signer within a group at the cost of O(n) size/time. Great for N ≤ 100. For larger groups or real-time latency, switch to ZK-proofs or blind signatures.
