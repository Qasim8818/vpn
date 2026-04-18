# Post-Quantum Cryptography Deep-Dive for VPN

**Audience:** Cryptographers, security engineers, compliance officers  
**Purpose:** Understand quantum threats and practical PQC deployment  
**Scope:** Kyber, Dilithium, FIPS 203/204, migration strategy  
**Status:** FIPS 203/204 officially published (August 2024)  
**Last Updated:** April 2026

---

## Executive Summary

**Timeline (Conservative):**
- **2024–2026:** Deploy Kyber-768 hybrid NOW (no downside)
- **2030:** Assume quantum computer feasible (RSA-2048 breakable)
- **2035:** All recorded pre-2030 traffic compromised (harvest now, decrypt later)
- **2040:** Post-quantum migration mandatory (regulations coming)

**Practical Action:**
- [ ] Replace X25519 with Kyber-768 (available now, FIPS 203)
- [ ] Hybrid mode: Both Kyber + X25519 (safe, future-proof)
- [ ] Rotate all keys annually (assume past compromised)
- [ ] Deploy Dilithium for firmware signing (FIPS 204)

---

## Part 1: Quantum Computing Fundamentals

### Classical vs. Quantum Computers

**Classical bit:** 0 or 1 (definite state)  
**Quantum bit (qubit):** 0, 1, or **superposition** (both simultaneously)

**Key quantum phenomena:**

| Phenomenon | Effect on Crypto | Problem/Benefit |
|---|---|---|
| **Superposition** | Test 2^n states in parallel | Exponential speedup (Shor's algorithm) |
| **Entanglement** | Correlated qubit pairs | Enables quantum error correction |
| **Interference** | Amplify correct answer, cancel wrong | Makes some problems tractable |

### Shor's Algorithm: Breaking RSA

**Classical factoring RSA-2048:**
```
Task: Find p, q such that p*q = N (2048-bit number)
Classical time: 2^256 bit operations (10^77, age of universe not enough)
```

**Quantum (Shor's algorithm):**
```
Task: Same (find factors)
Quantum time: 1.5 billion quantum gates (2^30, achievable in hours)

Requirements:
  • 4,000–6,000 logical qubits (error-corrected)
  • ~1 billion quantum gate operations
  • Quantum error rate < 10^-4 (currently 10^-2, improving)
  
Timeline: 2030–2035 assuming exponential improvements
```

### Current State of Quantum Hardware

**Device Status (2024):**

| Organization | Qubits | Error Rate | Status |
|---|---|---|---|
| **IBM** | 433 | 10^-2 | Noisy, experimental |
| **Google** | 99 | 10^-3 (claimed) | "Quantum advantage" on toy problem |
| **China** | 253 (unverified) | Unknown | Secretive |
| **IonQ** | 24 (trapped ion) | 10^-3 | Different architecture, more stable |

**Bottom line:** All current quantum computers are **not** a threat to RSA-2048 (yet).

### Harvest Now, Decrypt Later (Real Threat)

**Timeline:**

```
2024 (today):
  ├─ Attacker (state-funded) taps fiber → records VPN traffic
  ├─ Stores encrypted VPN handshakes in secure vault
  ├─ Cost: Minimal (already done by NSA/GCHQ)
  └─ Risk: Acceptable (can't decrypt yet)

2025–2034:
  ├─ Quantum research accelerates
  ├─ Storage cost decreases
  ├─ Attacker monitors progress
  └─ No risk to current operations

2030 (first major milestone):
  ├─ Quantum computer breaks RSA-2048 (privately announced)
  ├─ US intelligence community likely has access first
  ├─ Classified: "RSA dead, all historical traffic compromised"
  └─ Public discovery: 5–10 years later (Snowden-style)

2035 (compromise timeline):
  ├─ RSA-2048 factoring becomes routine
  ├─ Attacker decrypts all stored VPN traffic from 2024–2034
  ├─ All user IPs, server IPs, timing metadata revealed
  ├─ Session keys derivable (if used directly, no PFS)
  └─ Impact: 10+ years of user privacy compromised
```

**Key assumption:** Unbreakable encryption (Kyber-768) was NOT recording-resistant.

---

## Part 2: Kyber-768 (NIST FIPS 203)

### What Is Kyber?

**Kyber:** Key Encapsulation Mechanism (KEM) based on **Learning With Errors (LWE)** problem.

**Mathematical basis:**
```
Hard problem: Find secret s given:
  A (random matrix, public)
  b = A*s + e (mod q)  ← includes noise (error) vector

Noise makes it hard (adds exponential difficulty for attacker)
Even quantum computers can't solve (exponential speedup factor unknown)
```

**Kyber advantages:**
1. **Post-quantum secure** (believed to be)
2. **Fast** (microseconds, not milliseconds)
3. **Small keys** (768 bits, vs. RSA 2048)
4. **Industry standard** (NIST FIPS 203, ratified Aug 2024)

### Kyber Variants

| Variant | Security Level | Public Key | Ciphertext | Cost | Recommended |
|---|---|---|---|---|---|
| **Kyber-512** | ~128 bits | 800 B | 768 B | Low | Development only |
| **Kyber-768** | ~192 bits | 1,184 B | 1,088 B | Medium | **Recommended** |
| **Kyber-1024** | ~256 bits | 1,568 B | 1,568 B | High | Paranoid/future-proof |

**For VPN:** Kyber-768 is sweet spot (balance of security + performance).

### Kyber Implementation Example

**Go library (crypto/kyber):**

```go
package main

import (
	"crypto/kyber/kyber768"
)

func main() {
	// Generate ephemeral keypair
	epk, esk, _ := kyber768.GenerateKeyPair()
	
	// Initiator encapsulates (creates shared secret)
	ciphertext, sharedSecret, _ := kyber768.Encapsulate(epk)
	
	// Responder decapsulates (recovers same shared secret)
	recovered, _ := kyber768.Decapsulate(esk, ciphertext)
	
	// Verify secrets match
	assert(sharedSecret == recovered)  // → true
}
```

### Kyber in VPN Handshake (WireGuard-like)

**Current protocol (X25519):**
```
Initiator → Responder:
  msg1: ephemeral_pubkey_X25519, encrypted_static_key
  
Responder → Initiator:
  msg2: ephemeral_pubkey_X25519, encrypted_nothing
  
Shared secret: DH(init_ephemeral, resp_ephemeral)
Session key: KDF(shared_secret)
```

**New protocol (Kyber hybrid):**
```
Initiator → Responder:
  msg1: kyber_ct (ciphertext), x25519_pubkey, encrypted_static
  
Responder → Initiator:
  msg2: kyber_ct (ciphertext), x25519_pubkey, encrypted_nothing
  
Shared secret: KDF(kyber_result || x25519_result)
Session key: KDF(combined_secret)

Security property:
  • If Kyber breaks: X25519 still provides confidentiality
  • If X25519 breaks: Kyber still provides confidentiality
  • Both must break for compromise (contradicts cryptography principles)
```

---

## Part 3: Dilithium (NIST FIPS 204)

### What Is Dilithium?

**Dilithium:** Digital signature algorithm (PQC variant).

**Use cases:**
1. Firmware signing (prove binary came from official vendor)
2. Certificate signing (CA issues certificates)
3. Message authentication (prove sender)

### Dilithium Variants

| Variant | Security | Signature | Public Key | Speed | Recommended |
|---|---|---|---|---|---|
| **Dilithium-2** | 128 bits | 2,420 B | 1,312 B | Fast | Test/dev |
| **Dilithium-3** | 192 bits | 3,293 B | 1,952 B | Medium | **Recommended** |
| **Dilithium-5** | 256 bits | 4,595 B | 2,592 B | Slow | Paranoid |

**For VPN:** Dilithium-3 for firmware/certs, Dilithium-2 for session signing.

### Dilithium in Certificate Signing

**Current (RSA-4096):**
```
CA private key: RSA-4096 (512 bytes)
CA public key: RSA-4096 (512 bytes)
Signature on cert: RSA-4096 (512 bytes)
Total overhead per cert: 1.5 KB
```

**New (Dilithium-3):**
```
CA private key: Dilithium-3 (2.5 KB)
CA public key: Dilithium-3 (1.95 KB)
Signature on cert: Dilithium-3 (3.3 KB)
Total overhead per cert: 7.75 KB
Increase: 5x larger, but still manageable
```

---

## Part 4: Migration Strategy (4-Phase Approach)

### Phase 1: Pilot (Months 1–3)

**Goal:** Deploy hybrid Kyber + X25519 in staging environment.

```
Actions:
  ├─ Update crypto library (quic-go, libsodium → Kyber support)
  ├─ Generate Kyber test keypairs
  ├─ Implement hybrid KEM (concatenate shared secrets)
  ├─ Deploy to staging VPN servers (1% of traffic)
  ├─ Monitor: latency, packet loss, key derivation failures
  └─ Success criteria: 0 bugs, < 1ms latency overhead

Timeline:
  Week 1-2: Library updates, testing
  Week 3-4: Staging deployment, monitoring
  Week 5-8: Bug fixes, tuning
  Week 9-12: Decision to proceed (or iterate)
```

### Phase 2: Canary (Months 4–6)

**Goal:** Roll out to production in canary fashion.

```
Actions:
  ├─ Enable Kyber hybrid on 5% of prod servers
  ├─ Monitor real user traffic (latency, errors, battery drain mobile)
  ├─ Graduate to 25% if metrics healthy
  ├─ Graduate to 100% over 1 month
  └─ Success criteria: No user complaints, latency < 2ms overhead

Rollback plan:
  If critical bug found:
    ├─ Disable Kyber on affected servers (5 min propagation)
    ├─ Users auto-reconnect (use X25519 fallback)
    ├─ No data loss (session resumed)
    └─ Time to mitigation: < 30 minutes
```

### Phase 3: Mandatory (Months 7–12)

**Goal:** All connections use Kyber hybrid.

```
Actions:
  ├─ Retire X25519-only connections (client-side enforcement)
  ├─ Notify users (3 months warning): "Update VPN app to v2.5"
  ├─ v2.5 supports both Kyber + X25519
  ├─ v3.0 (12 months later) requires Kyber hybrid
  └─ Old clients (< v2.5) disconnected (< 5% user impact usually)

Success criteria:
  • 99%+ of active users on Kyber-capable client
  • Zero Kyber-specific crashes or attacks
```

### Phase 4: Historic Key Rotation (Months 13+)

**Goal:** Rotate all pre-migration keys (assume potentially compromised).

```
Actions:
  ├─ For each user's stored key material:
  │  ├─ Generate new Kyber keypair
  │  ├─ Re-derive all session keys (new ephemerals)
  │  └─ Securely erase old key material
  ├─ Broadcast new keys (signed with Dilithium-3)
  ├─ Users update keys atomically (no split-brain)
  └─ Log: "2026-01 key rotation complete"

Reason:
  If quantum computer breaksRSA in 2035:
    ├─ Attacker decrypts all pre-January-2026 traffic
    ├─ But: Session keys derived from post-Kyber generation are safe
    ├─ Result: Historical compromise doesn't affect ongoing security
```

---

## Part 5: Hybrid Crypto (Best Practice)

### Why Hybrid?

**Single algorithm risk:**
```
Scenario A: Deploy only Kyber
  If unknown quantum algorithm breaks LWE:
    → All VPN compromised (single point of failure)

Scenario B: Deploy Kyber + X25519 (hybrid)
  If unknown algorithm breaks Kyber:
    → LWE assumption might be wrong
    → But: X25519 (ECDH) still secure (classically hard)
    → VPN remains protected
    
  If unknown algorithm breaks X25519:
    → ECC assumption breached
    → But: Kyber still secure (LWE assumed quantum-resistant)
    → VPN remains protected
```

**Formula:**
```
Hybrid security = min(Kyber_security, X25519_security)
                = Conservative choice (safer)
```

### Hybrid Implementation

**Key agreement:**
```go
func HybridKeyAgreement(kyber_ciphertext, x25519_pubkey) {
    // Decrypt Kyber
    kyber_shared := kyber768.Decapsulate(kyber_secret, kyber_ciphertext)
    
    // Perform X25519 ECDH
    x25519_shared := ecdh(x25519_secret, x25519_pubkey)
    
    // Combine (XOR safer than concatenation, but both work)
    combined := kyber_shared XOR x25519_shared
    
    // Derive session key
    session_key := HKDF_SHA256(info="VPN_KEY", combined)
}
```

---

## Part 6: Transition Checklist

- [ ] **Understand PQC basics** (this document)
- [ ] **Choose library** (liboqs-c, liboqs-go, libcrux-Rust)
- [ ] **Prototype hybrid KEM** in test environment
- [ ] **Benchmark** latency, throughput, CPU usage
- [ ] **Update API** to support Kyber in handshake
- [ ] **Deploy staging** (1% traffic, 1 month)
- [ ] **Deploy canary** (5% → 25% → 100%, 3 months)
- [ ] **Mandatory adoption** (old clients unsupported after 12 months)
- [ ] **Key rotation** (January 2026 migration baseline)
- [ ] **Staff training** (document PQC migration for ops team)
- [ ] **Audit & certify** (third-party security review)

---

## Part 7: References & Standards

**NIST Standards (2024):**
- FIPS 203: Kyber KEM standard (use this)
- FIPS 204: Dilithium signature standard (use this)
- FIPS 202: SHA-3 (unchanged, post-quantum secure)

**Implementations:**
- **liboqs-c:** https://github.com/open-quantum-safe/liboqs
- **liboqs-go:** Kyber bindings for Go
- **libcrux:** Rust implementation (Mozilla sponsored)

**Timeline documents:**
- "How to Migrate to Post-Quantum Cryptography" (NIST SP 800-208)
- "PQC Migration Timeline" (Google, 2024)

---

*PQC Deep-Dive v1.0*  
*Last Updated: April 2026*
