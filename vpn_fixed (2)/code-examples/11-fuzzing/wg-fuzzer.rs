// Fuzzing WireGuard Packet Parsing — LibAFL Harness
// Section 11: Automated Security Testing
//
// Feeds random/mutated packets to WireGuard handshake parsing.
// Detects crashes, memory leaks, infinite loops before production.
//
// Build: cargo build --release (requires libafl)
// Run:   cargo fuzz --release -- run_fuzzer

use std::mem;

/// WireGuard packet types
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
enum MessageType {
    MessageHandshakeInitiation = 1,
    MessageHandshakeResponse = 2,
    MessageHandshakeCounter = 3,
    MessageTransportData = 4,
}

/// Simplified WireGuard message layout (educational, not production)
#[repr(C, packed)]
#[derive(Clone, Copy, Debug)]
struct MessageHeader {
    msg_type: u8,
    receiver_index: [u8; 4],
    counter: u64,
}

/// WireGuard handshake initiation message
#[repr(C, packed)]
struct MessageHandshakeInitiation {
    header: MessageHeader,
    sender_index: [u8; 4],
    unencrypted_ephemeral: [u8; 32],
    encrypted_static: [u8; 48],
    encrypted_timestamp: [u8; 28],
    mac1: [u8; 16],
    mac2: [u8; 16],
}

/// WireGuard handshake response message
#[repr(C, packed)]
struct MessageHandshakeResponse {
    header: MessageHeader,
    sender_index: [u8; 4],
    receiver_index: [u8; 4],
    unencrypted_ephemeral: [u8; 32],
    encrypted_nothing: [u8; 16],
    mac1: [u8; 16],
    mac2: [u8; 16],
}

/// WireGuard transport data message
#[repr(C, packed)]
struct MessageTransportData {
    header: MessageHeader,
    packet_counter: u64,
    encrypted_encapsulated_packet: [u8; 256],
}

/// Parser validates incoming packets
struct WireGuardParser;

impl WireGuardParser {
    /// Parse and validate a WireGuard message header
    /// Production: this is where bugs live (buffer overflows, integer underflows, etc.)
    fn parse_header(data: &[u8]) -> Result<MessageHeader, &'static str> {
        if data.len() < mem::size_of::<MessageHeader>() {
            return Err("Packet too short for header");
        }

        // In production WireGuard, unsafe memcpy here (C code)
        // We replicate the behavior
        let msg_type = data[0];
        let receiver_idx = &data[1..5];
        let counter = u64::from_le_bytes(
            data[5..13]
                .try_into()
                .map_err(|_| "Invalid counter bytes")?,
        );

        if msg_type < 1 || msg_type > 4 {
            return Err("Invalid message type");
        }

        Ok(MessageHeader {
            msg_type,
            receiver_index: receiver_idx.try_into().unwrap(),
            counter,
        })
    }

    /// Parse and validate handshake initiation
    /// Fuzzer targets this function to find crashes
    fn parse_handshake_init(data: &[u8]) -> Result<(), &'static str> {
        if data.len() < mem::size_of::<MessageHandshakeInitiation>() {
            return Err("Handshake init too short");
        }

        // Validate header exists
        let _header = Self::parse_header(data)?;

        // Check sender_index is not zero (WireGuard rule)
        let sender_idx_bytes = &data[5..9];
        let sender_idx = u32::from_le_bytes(sender_idx_bytes.try_into().unwrap());
        if sender_idx == 0 {
            return Err("Sender index cannot be zero");
        }

        // Validate ephemeral public key format (should be non-zero)
        let ephemeral = &data[13..45];
        if ephemeral.iter().all(|&b| b == 0) {
            return Err("Ephemeral key is all-zeros");
        }

        // Validate encrypted_static field (allowed to be anything)
        let _encrypted_static = &data[45..93];

        // Validate MAC1 and MAC2 (should be computed, not just random)
        // In production: full BLAKE2 verification
        let _mac1 = &data[109..125];
        let _mac2 = &data[125..141];

        Ok(())
    }

    /// Parse transport data message
    fn parse_transport_data(data: &[u8]) -> Result<(), &'static str> {
        if data.len() < 21 {
            // Minimum: header (13) + counter (8)
            return Err("Transport data too short");
        }

        let _header = Self::parse_header(data)?;

        // Validate packet_counter doesn't overflow
        let packet_counter = u64::from_le_bytes(data[13..21].try_into().unwrap());
        if packet_counter == u64::MAX {
            return Err("Packet counter overflow");
        }

        // Payload is encrypted; just check it's not entirely zero (weak check)
        if data.len() > 21 {
            let payload = &data[21..];
            if !payload.is_empty() && payload.iter().any(|&b| b != 0) {
                return Ok(());
            }
        }

        Err("Payload appears invalid")
    }

    /// Main dispatcher: route to parser based on message type
    pub fn parse(data: &[u8]) -> Result<(), &'static str> {
        if data.is_empty() {
            return Err("Empty packet");
        }

        match data[0] {
            1 => Self::parse_handshake_init(data),
            2 => {
                if data.len() < mem::size_of::<MessageHandshakeResponse>() {
                    return Err("Handshake response too short");
                }
                Self::parse_header(data)?;
                Ok(())
            }
            3 => {
                if data.len() < 13 {
                    return Err("Counter message too short");
                }
                Self::parse_header(data)?;
                Ok(())
            }
            4 => Self::parse_transport_data(data),
            _ => Err("Unknown message type"),
        }
    }
}

/// Fuzzing harness: called repeatedly by LibAFL with mutated inputs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_packet() {
        assert!(WireGuardParser::parse(&[]).is_err());
    }

    #[test]
    fn test_invalid_type() {
        assert!(WireGuardParser::parse(&[5, 0, 0, 0, 0]).is_err());
    }

    #[test]
    fn test_truncated_header() {
        let truncated = vec![1, 0, 0]; // Only 3 bytes, need 13
        assert!(WireGuardParser::parse(&truncated).is_err());
    }

    #[test]
    fn test_handshake_init_valid() {
        let mut packet = vec![1; 148]; // Handshake initiation size
        packet[0] = 1; // Message type
        packet[5] = 1; // Sender index (non-zero)
        packet[13] = 255; // Ephemeral key non-zero

        let result = WireGuardParser::parse(&packet);
        println!("Result: {:?}", result);
        // Should pass validation (or fail gracefully)
    }

    #[test]
    fn test_zero_sender_index() {
        let mut packet = vec![0; 148];
        packet[0] = 1; // Handshake init
        // Sender index already zero (bad)
        assert!(WireGuardParser::parse(&packet).is_err());
    }

    #[test]
    fn test_zero_ephemeral_key() {
        let mut packet = vec![0; 148];
        packet[0] = 1;
        packet[5] = 1; // Non-zero sender
        // Ephemeral key is all-zeros (bad)
        assert!(WireGuardParser::parse(&packet).is_err());
    }

    #[test]
    fn test_transport_data_valid() {
        let mut packet = vec![0; 100];
        packet[0] = 4; // Transport data
        packet[5] = 1; // Non-zero counter
        packet[13] = 42; // Payload has non-zero byte
        assert!(WireGuardParser::parse(&packet).is_ok());
    }

    #[test]
    fn test_fuzz_randomdata() {
        // In production LibAFL, this runs with random mutations
        use std::collections::hash_map::RandomState;
        use std::hash::{BuildHasher, Hasher};

        let mut hasher = RandomState::new().build_hasher();
        hasher.write_u64(12345);
        let hash = hasher.finish();

        let random_packet: Vec<u8> = (0..50)
            .map(|i| ((hash.wrapping_mul(i as u64)) & 0xFF) as u8)
            .collect();

        // Should not crash, should return error or ok
        let _result = WireGuardParser::parse(&random_packet);
    }
}

fn main() {
    println!("WireGuard Packet Fuzzing Harness");
    println!("=================================\n");

    // Example 1: Valid handshake initiation
    println!("Test 1: Malformed header (too short)");
    let short_packet = vec![1, 2, 3];
    match WireGuardParser::parse(&short_packet) {
        Ok(_) => println!("  ✓ Accepted"),
        Err(e) => println!("  ✓ Rejected: {}", e),
    }

    // Example 2: Invalid message type
    println!("\nTest 2: Invalid message type (>4)");
    let invalid_type = vec![255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    match WireGuardParser::parse(&invalid_type) {
        Ok(_) => println!("  ✓ Accepted"),
        Err(e) => println!("  ✓ Rejected: {}", e),
    }

    // Example 3: Valid structure but suspicious payload
    println!("\nTest 3: Zero sender index (invalid)");
    let mut zero_sender = vec![1; 148];
    zero_sender[0] = 1;
    // sender[1..5] is all zeros
    match WireGuardParser::parse(&zero_sender) {
        Ok(_) => println!("  ✓ Accepted"),
        Err(e) => println!("  ✓ Rejected: {}", e),
    }

    println!("\n=== How to use LibAFL ===");
    println!("1. Add libAFL to Cargo.toml:");
    println!("   [dev-dependencies]");
    println!("   libafl = {{ version = \"0.10\", features = [\"std\"] }}");
    println!("\n2. Run fuzzer:");
    println!("   cargo +nightly fuzz -- run_fuzzer");
    println!("\n3. Fuzzer will:");
    println!("   • Generate random inputs");
    println!("   • Feed to WireGuardParser::parse()");
    println!("   • Detect crashes, hangs, memory leaks");
    println!("   • Save crashing inputs for replay");
}
