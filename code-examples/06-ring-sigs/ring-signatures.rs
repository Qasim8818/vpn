// Schnorr Ring Signature — Anonymous Group Authentication
// Section 06: Ring Signatures for VPN
// 
// Proves "one of these N keys signed this message" without revealing which.
// Perfect for: group VPN access, deniable authentication, anonymous credentials.
//
// Build: cargo build --release
// Run:   cargo run --release -- sign 3 0 "example message"

use curve25519_dalek::constants::RISTRETTO_BASEPOINT_POINT;
use curve25519_dalek::ristretto::RistrettoPoint;
use curve25519_dalek::scalar::Scalar;
use rand::rngs::OsRng;
use sha3::{Sha3_256, Digest};

/// Ring signature output: challenges and responses for each ring member
#[derive(Clone, Debug)]
pub struct RingSignature {
    pub c: Vec<Scalar>,  // Challenge state for each member
    pub s: Vec<Scalar>,  // Response for each member
}

/// Generate a ring signature proving one of the keys signed the message
/// 
/// # Arguments
/// * `message` - The message being signed
/// * `ring_pubs` - All public keys in the ring
/// * `signer_idx` - Which index is the actual signer (secret)
/// * `signer_secret` - The secret key of the signer
pub fn ring_sign(
    message: &[u8],
    ring_pubs: &[RistrettoPoint],
    signer_idx: usize,
    signer_secret: &Scalar,
) -> RingSignature {
    assert!(signer_idx < ring_pubs.len(), "Signer index out of ring bounds");
    
    let n = ring_pubs.len();
    let G = RISTRETTO_BASEPOINT_POINT;
    
    // Random nonce for the actual signer
    let k = Scalar::random(&mut OsRng);
    let commitment = k * G;  // w = g^k
    
    // Initialize state: hash includes the real commitment
    let mut hasher = Sha3_256::new();
    hasher.update(message);
    hasher.update(commitment.compress().as_bytes());
    let mut hash_bytes = [0u8; 32];
    hash_bytes.copy_from_slice(&hasher.finalize());
    let mut c = vec![Scalar::from_bytes_mod_order(hash_bytes); n];
    let mut s = vec![Scalar::zero(); n];
    
    // Simulate responses for all members except the signer
    let mut i = (signer_idx + 1) % n;
    while i != signer_idx {
        // Generate random response for this member
        s[i] = Scalar::random(&mut OsRng);
        
        // Compute the simulated commitment: R = g^s[i] * pk[i]^{-c[i]}
        let R = s[i] * G - c[i] * ring_pubs[i];
        
        // Hash to get next challenge
        let mut hasher = Sha3_256::new();
        hasher.update(message);
        hasher.update(R.compress().as_bytes());
        let mut hash_bytes = [0u8; 32];
        hash_bytes.copy_from_slice(&hasher.finalize());
        c[(i + 1) % n] = Scalar::from_bytes_mod_order(hash_bytes);
        
        i = (i + 1) % n;
    }
    
    // Compute actual signer's response: s[signer_idx] = k - c[signer_idx] * secret_key
    s[signer_idx] = k - c[signer_idx] * signer_secret;
    
    RingSignature { c, s }
}

/// Verify a ring signature
/// 
/// # Returns
/// `true` if exactly one member of the ring can produce this signature
pub fn ring_verify(
    message: &[u8],
    ring_pubs: &[RistrettoPoint],
    sig: &RingSignature,
) -> bool {
    let n = ring_pubs.len();
    if sig.c.len() != n || sig.s.len() != n {
        return false;
    }
    
    let G = RISTRETTO_BASEPOINT_POINT;
    
    // Recompute the ring and verify consistency
    let mut computed_c = vec![Scalar::zero(); n];
    computed_c[0] = sig.c[0];  // We'll verify this matches
    
    for i in 0..n {
        // Recompute: w[i] = g^s[i] * pk[i]^{-c[i]}
        // This should hash to c[(i+1) mod n]
        let w = sig.s[i] * G - sig.c[i] * ring_pubs[i];
        
        let mut hasher = Sha3_256::new();
        hasher.update(message);
        hasher.update(w.compress().as_bytes());
        let mut hash_bytes = [0u8; 32];
        hash_bytes.copy_from_slice(&hasher.finalize());
        let next_c = Scalar::from_bytes_mod_order(hash_bytes);
        
        computed_c[(i + 1) % n] = next_c;
    }
    
    // Verify the ring closes: computed_c[0] should match sig.c[0]
    computed_c[0] == sig.c[0]
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_ring_signature() {
        // Create a ring of 5 public keys
        let ring_size = 5;
        let signer_idx = 2;
        let message = b"Anonymous VPN access granted";
        
        // Generate keypairs
        let mut secrets = Vec::new();
        let mut publics = Vec::new();
        for _ in 0..ring_size {
            let sk = Scalar::random(&mut OsRng);
            let pk = sk * RISTRETTO_BASEPOINT_POINT;
            secrets.push(sk);
            publics.push(pk);
        }
        
        // Sign with member 2
        let sig = ring_sign(message, &publics, signer_idx, &secrets[signer_idx]);
        
        // Verify signature
        assert!(ring_verify(message, &publics, &sig));
        
        // Modify message, signature should fail
        let bad_message = b"Different message";
        assert!(!ring_verify(bad_message, &publics, &sig));
        
        // Modify a public key, signature should fail
        let mut bad_publics = publics.clone();
        bad_publics[0] = Scalar::random(&mut OsRng) * RISTRETTO_BASEPOINT_POINT;
        assert!(!ring_verify(message, &bad_publics, &sig));
    }
}

fn main() {
    use std::env;
    
    let args: Vec<String> = env::args().collect();
    if args.len() < 4 {
        eprintln!("Usage: {} [sign|verify] <ring_size> <signer_idx> <message>", args[0]);
        std::process::exit(1);
    }
    
    let ring_size: usize = args[2].parse().expect("Invalid ring size");
    let signer_idx: usize = args[3].parse().expect("Invalid signer index");
    let message = args.get(4).map(|s| s.as_bytes()).unwrap_or(b"Default message");
    
    match args[1].as_str() {
        "sign" => {
            // Generate keypairs
            let mut secrets = Vec::new();
            let mut publics = Vec::new();
            for i in 0..ring_size {
                let sk = Scalar::random(&mut OsRng);
                let pk = sk * RISTRETTO_BASEPOINT_POINT;
                println!("[{}] pk: {}", i, hex::encode(pk.compress().as_bytes()));
                secrets.push(sk);
                publics.push(pk);
            }
            
            // Sign
            let sig = ring_sign(message, &publics, signer_idx, &secrets[signer_idx]);
            println!("\n✓ Signed by member {} of {}", signer_idx, ring_size);
            println!("Message: {}", String::from_utf8_lossy(message));
            
            // Show signature (truncated for readability)
            println!("\nSignature (truncated):");
            for (i, (c, s)) in sig.c.iter().zip(sig.s.iter()).enumerate() {
                let c_hex = hex::encode(&c.as_bytes()[..8]);
                let s_hex = hex::encode(&s.as_bytes()[..8]);
                println!("  [{}] c: {}...  s: {}...", i, c_hex, s_hex);
            }
            
            // Verify
            if ring_verify(message, &publics, &sig) {
                println!("\n✓ Signature verified (one member of the ring signed this)");
                println!("Observer learns: someone in the ring, but NOT WHO");
            } else {
                println!("\n✗ Verification FAILED");
            }
        }
        "verify" => {
            println!("Ring signature verification demo (keys would be pre-distributed)");
        }
        _ => {
            eprintln!("Unknown command: {}", args[1]);
            std::process::exit(1);
        }
    }
}
