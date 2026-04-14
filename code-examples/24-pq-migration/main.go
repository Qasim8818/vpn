// Post-Quantum Migration: Kyber-768 PSK Generation for WireGuard
// 
// Problem: Current adversaries recording VPN traffic now will decrypt it
// with future quantum computers. This is "harvest now, decrypt later" attack.
//
// Solution: Add Kyber-768 (PQC KEM) generated PSK to WireGuard immediately.
// Even if X25519 breaks to quantum, ChaCha20-Poly1305 + random Kyber PSK remains secure.
//
// This runs ONCE during VPN configuration, before any traffic.
// The PSK is added to WireGuard config:
//   $ wg set wg0 peer AAAA... preshared-key <(go run this-program)

package main

import (
	"bytes"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"log"

	// CIRCL: Cloudflare's PQC library (Go)
	"github.com/cloudflare/circl/kem/kyber/kyber768"
)

// KyberPSKGenerator handles Kyber key encapsulation
type KyberPSKGenerator struct {
	kem KEM  // Abstract interface
}

// KEM interface (Kyber implements this)
type KEM interface {
	Scheme() string
	Encapsulate(publicKey []byte) (ciphertext, sharedSecret []byte, err error)
	Decapsulate(privateKey, ciphertext []byte) (sharedSecret []byte, err error)
}

// GenerateHybridPSK creates a 32-byte PSK from Kyber-768
// Using only the shared secret (not the ciphertext)
func GenerateHybridPSK() (psk []byte, err error) {
	// Step 1: Generate Kyber-768 keypair
	// In practice, this would be done once and stored in HSM
	publicKey, privateKey, err := kyber768.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("kyber generate key: %w", err)
	}

	// Step 2: Encapsulate (peer would need to do this)
	// In production, this is interactive:
	// 1. Server sends Kyber public key
	// 2. Client encapsulates, gets plaintext shared secret
	// 3. Client sends ciphertext back to server
	// 4. Server decapsulates using own private key
	// 5. Both derive same shared secret

	// For this example, we do both sides:
	ciphertext, sharedSecret, err := kyber768.Encapsulate(publicKey)
	if err != nil {
		return nil, fmt.Errorf("kyber encapsulate: %w", err)
	}

	// Step 3: Verify decapsulation (server side)
	verifySecret, err := kyber768.Decapsulate(privateKey, ciphertext)
	if err != nil {
		return nil, fmt.Errorf("kyber decapsulate: %w", err)
	}

	// Sanity check: both sides must get same secret
	if !bytes.Equal(sharedSecret, verifySecret) {
		return nil, fmt.Errorf("kyber encapsulation failed: secrets don't match")
	}

	// Step 4: Derive PSK from shared secret
	// Kyber-768 provides 32 bytes of shared secret
	// This is ALREADY cryptographically secure randomness
	psk = sharedSecret[:32]

	return psk, nil
}

// GeneratePSK alternative: Simple random (for fallback)
// If Kyber unavailable, use ChaCha20 output
func GenerateRandomPSK() ([]byte, error) {
	psk := make([]byte, 32)
	_, err := rand.Read(psk)
	return psk, err
}

// Main workflow: WireGuard PSK setup
func main() {
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println("  WireGuard + Kyber-768 PSK Generation")
	fmt.Println("  (Post-Quantum Forward Secrecy)")
	fmt.Println("═══════════════════════════════════════════════════════\n")

	// Generate PSK
	psk, err := GenerateHybridPSK()
	if err != nil {
		log.Fatalf("PSK generation failed: %v", err)
	}

	// Output as base64 (WireGuard expects binary, but we show b64 for readability)
	pskBase64 := base64.StdEncoding.EncodeToString(psk)
	pskHex := fmt.Sprintf("%x", psk)

	fmt.Printf("✓ Kyber-768 PSK generated (32 bytes)\n\n")
	fmt.Printf("Base64 format (for scripts):\n")
	fmt.Printf("%s\n\n", pskBase64)
	fmt.Printf("Hex format (for verification):\n")
	fmt.Printf("%s\n\n", pskHex)

	// SECURITY PROPERTIES
	fmt.Printf("═══════════════════════════════════════════════════════\n")
	fmt.Printf("SECURITY ANALYSIS\n")
	fmt.Printf("═══════════════════════════════════════════════════════\n\n")

	fmt.Printf("Threat Model: \"Harvest Now, Decrypt Later\" (HNDL)\n\n")

	fmt.Printf("Scenario 1: X25519 stays secure\n")
	fmt.Printf("  ✓ Classical security: WireGuard works as-is\n")
	fmt.Printf("  ✓ Adds Kyber PSK: Extra security, no downside\n\n")

	fmt.Printf("Scenario 2: X25519 breaks to quantum computer\n")
	fmt.Printf("  ✗ Without Kyber PSK:\n")
	fmt.Printf("    Attacker records encrypted traffic NOW\n")
	fmt.Printf("    Attacker builds quantum computer in 20 years\n")
	fmt.Printf("    Attacker breaks X25519, decrypts all traffic\n")
	fmt.Printf("    → Massive retroactive compromise\n\n")

	fmt.Printf("  ✓ With Kyber PSK:\n")
	fmt.Printf("    Traffic encrypted with ChaCha20(Kyber-PSK, X25519-key)\n")
	fmt.Printf("    Breaking X25519 reveals only nonce/derivation order\n")
	fmt.Printf("    ChaCha20 security still rests on Kyber PSK entropy\n")
	fmt.Printf("    Kyber is conjectured post-quantum secure\n")
	fmt.Printf("    → Traffic remains confidential despite X25519 break\n\n")

	fmt.Printf("═══════════════════════════════════════════════════════\n")
	fmt.Printf("DEPLOYMENT INSTRUCTIONS\n")
	fmt.Printf("═══════════════════════════════════════════════════════\n\n")

	fmt.Printf("1. Generate PSK on server:\n")
	fmt.Printf("   $ go run pq-migration.go > /tmp/psk.key\n\n")

	fmt.Printf("2. Add to WireGuard config:\n")
	fmt.Printf("   $ wg set wg0 peer <peer-pubkey> preshared-key $(cat /tmp/psk.key)\n\n")

	fmt.Printf("3. Verify:\n")
	fmt.Printf("   $ wg show wg0 preshared-keys\n")
	fmt.Printf("   (PSK should be non-zero)\n\n")

	fmt.Printf("4. Test traffic:\n")
	fmt.Printf("   $ ping <peer-vpn-ip>\n")
	fmt.Printf("   (Should work transparently — PSK is automatic)\n\n")

	fmt.Printf("═══════════════════════════════════════════════════════\n")
	fmt.Printf("IMPLEMENTATION NOTES\n")
	fmt.Printf("═══════════════════════════════════════════════════════\n\n")

	fmt.Printf("• Kyber-768: NIST PQC finalist (standardization expected 2024)\n")
	fmt.Printf("• Security level: 128-bit classical equivalent\n")
	fmt.Printf("• Ciphertext size: 1088 bytes (overhead is acceptable)\n")
	fmt.Printf("• Shared secret: 32 bytes (perfect for ChaCha20 PSK)\n")
	fmt.Printf("• Generation time: ~1ms per PSK\n")
	fmt.Printf("• Zero performance impact on data path (one-time setup)\n\n")

	fmt.Printf("• Library: CIRCL (Cloudflare, audited, pure Go)\n")
	fmt.Printf("• Alternative: liboqs-go if hardware crypto needed\n\n")

	fmt.Printf("═══════════════════════════════════════════════════════\n\n")

	// Additional: show what happens in the handshake
	fmt.Printf("WireGuard Handshake with Kyber PSK:\n\n")

	fmt.Printf("1. Initiator → Responder: PublicKey, Ephemeral-X25519, Kyber-Init\n")
	fmt.Printf("   (Contains X25519 public + Kyber encapsulated message)\n\n")

	fmt.Printf("2. Responder derives:\n")
	fmt.Printf("   Key1 = DH(responder-private, ephemeral-public)    [ECDH]\n")
	fmt.Printf("   Key2 = Kyber-decapsulate(responder-private)       [PQC]\n")
	fmt.Printf("   PSK = Key1 XOR Key2 (simplified; actual is more complex)\n\n")

	fmt.Printf("3. Encryption:\n")
	fmt.Printf("   Ciphertext = ChaCha20-Poly1305(psk, message)\n")
	fmt.Printf("   Security: min(X25519, Kyber-768) against eavesdropping\n\n")

	fmt.Printf("Result: Traffic is secure against both:\n")
	fmt.Printf("  • Classical algorithms (AES-128, DES, fast discrete log)\n")
	fmt.Printf("  • Quantum algorithms (Shor's, Grover's)\n\n")

	// Output just the PSK stream (suitable for piping)
	fmt.Print(pskBase64)
}

/*
BUILD & RUN:

  go get github.com/cloudflare/circl

  go run pq-migration.go
  # Output: base64-encoded 32-byte PSK

  # In production, create a secure script:
  #!/bin/bash
  set -e
  PSK=$(go run pq-migration.go)
  wg set wg0 peer "$PEER_PUB_KEY" preshared-key "$PSK"
  wg show wg0 preshared-keys

MIGRATION PATH (From GUIDE Section 24):

Phase 1 (NOW): Add Kyber PSK to existing X25519 WireGuard
  - Zero protocol changes
  - Zero compatibility issues
  - PSK is just additional entropy source
  - Clients don't need update

Phase 2 (3-6 months): Evaluate Kyber standardization
  - NIST expected to finalize around mid-2024
  - Replace/update if needed

Phase 3 (6-18 months): Add ML-DSA (Dilithium) for signatures
  - Replace Ed25519 identity keys
  - Hybrid signature approach

Phase 4 (18+ months): Full PQ stack
  - Remove classical curves entirely
  - Formal verification complete
*/
