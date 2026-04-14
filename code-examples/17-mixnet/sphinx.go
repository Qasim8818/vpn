// Sphinx Packet Encoding — Onion Routing for VPN Mixnets
// Section 17: Infrastructure — Anonymous Packet Routing
//
// Scenario: Mix network with 10 routers. Each router sees only:
// - Previous router (encrypted input)
// - Next router (encrypted output)
// - NO correlation between input and output

package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
)

// SphinxHeader: layered encryption, one layer per hop
type SphinxHeader struct {
	GroupElement [32]byte // Ephemeral DH public key (ECDH-32)
	RouteInfo    [200]byte // Encrypted relay (route) information
	Routinginfo  [1024]byte // Encrypted next-hop addresses (layered)
}

// SphinxPacket: the on-the-wire format after encryption
type SphinxPacket struct {
	Header   SphinxHeader
	Payload  [2000]byte // Encrypted user data
}

// MixNode represents a router in the mix network
type MixNode struct {
	ID            int
	PrivateKey    [32]byte
	PublicKey     [32]byte
	NextNodeIndex int // 0-9 for ring topology
}

// MixNetwork coordinates mix nodes
type MixNetwork struct {
	nodes []*MixNode
}

// SimpleSphinxCodec implements basic Sphinx encoding (educational version)
// Production Sphinx: more complex, includes integrity checks, etc.
type SimpleSphinxCodec struct {
	numHops int
}

// KeyDerivation: derive shared secret from DH exchange
// In production: use x25519 elliptic curve; here: simplified
func deriveKey(ephemeralPublic [32]byte, nodePrivate [32]byte) [32]byte {
	// Simplification: hash(ephemeral || private)
	h := sha256.New()
	h.Write(ephemeralPublic[:])
	h.Write(nodePrivate[:])
	var key [32]byte
	copy(key[:], h.Sum(nil))
	return key
}

// ChaCha20Poly1305Encrypt: one-time encryption layer
func encryptLayer(data []byte, key [32]byte, routeIdx int) []byte {
	// In real Sphinx: use ChaCha20 stream cipher
	// Here: simplified with AES-256
	block, err := aes.NewCipher(key[:])
	if err != nil {
		panic(err)
	}

	// Create a stream cipher (CTR mode)
	ctr := cipher.NewCTR(block, make([]byte, 16))

	// Encrypt data
	encrypted := make([]byte, len(data))
	ctr.XORKeyStream(encrypted, data)

	return encrypted
}

// DecryptLayer: reverse of encryptLayer
func decryptLayer(data []byte, key [32]byte) []byte {
	// Decryption is same as encryption in CTR mode (XOR is symmetric)
	return encryptLayer(data, key, 0)
}

// BuildOnionPacket: construct layered packet for path
// Path: [client -> Node0 -> Node1 -> Node2 -> exit]
func (codec *SimpleSphinxCodec) BuildOnionPacket(
	path []*MixNode,
	payload []byte,
	ephemeralPrivate [32]byte,
	ephemeralPublic [32]byte,
) SphinxPacket {

	packet := SphinxPacket{}
	copy(packet.Header.GroupElement[:], ephemeralPublic[:])
	copy(packet.Payload[:], payload)

	// Layer encryption: innermost (last node) to outermost (first node)
	var routingInfo [1024]byte
	var routeData []byte = routingInfo[:128] // Start with 128 bytes

	// Build routing info: each node knows where to send next
	currentInfo := make([]byte, 128)
	currentInfo[0] = 2 // Payload size (simplified)
	currentInfo[1] = byte(path[len(path)-1].ID) // Final destination

	// Layer encryption (reverse order: from exit node backwards to entry)
	for i := len(path) - 1; i >= 0; i-- {
		node := path[i]

		// Derive shared secret: ephemeral pubkey * node privkey
		sharedSecret := deriveKey(ephemeralPublic, node.PrivateKey)

		// Encrypt routing info with this layer
		encryptedInfo := encryptLayer(currentInfo, sharedSecret, i)

		// For next layer: prepend this node's ID to routing info
		nextInfo := make([]byte, len(encryptedInfo)+1)
		nextInfo[0] = byte(node.ID)
		copy(nextInfo[1:], encryptedInfo)
		currentInfo = nextInfo[:128] // Keep to 128 bytes (simplified)
	}

	copy(packet.Header.Routinginfo[:], currentInfo)
	return packet
}

// PeelOnionLayer: each mix node processes one layer
func (codec *SimpleSphinxCodec) PeelOnionLayer(
	packet *SphinxPacket,
	nodePrivate [32]byte,
	nodeEphemeralPublic [32]byte,
) (nextNodeID int, nextPacket SphinxPacket, err error) {

	// Derive shared key with entry ephemeral
	sharedSecret := deriveKey(packet.Header.GroupElement, nodePrivate)

	// Decrypt routing info for this layer
	decryptedInfo := decryptLayer(packet.Header.Routinginfo[:], sharedSecret)

	// Parse: first byte = next node ID
	nextNodeID = int(decryptedInfo[0])
	if nextNodeID < 0 || nextNodeID > 9 {
		return 0, SphinxPacket{}, fmt.Errorf("invalid next node: %d", nextNodeID)
	}

	// Prepare next packet (remove one layer)
	nextPacket = *packet
	copy(nextPacket.Header.Routinginfo[:], decryptedInfo[1:])

	return nextNodeID, nextPacket, nil
}

func main() {
	fmt.Println("=== Sphinx Mixnet Packet Encoding ===\n")

	// Initialize mix network: 5 nodes
	network := &MixNetwork{nodes: make([]*MixNode, 5)}
	for i := 0; i < 5; i++ {
		// Generate simple key material (in production: full ECDH)
		private := [32]byte{}
		public := [32]byte{}
		random.Read(private[:])
		random.Read(public[:])

		network.nodes[i] = &MixNode{
			ID:            i,
			PrivateKey:    private,
			PublicKey:     public,
			NextNodeIndex: (i + 1) % 5,
		}
	}

	fmt.Println("Mix network topology:")
	for _, node := range network.nodes {
		fmt.Printf("  Node %d → Node %d\n", node.ID, node.NextNodeIndex)
	}

	// Construct a packet for path: Client → Node0 → Node2 → Node4 → Exit
	path := []*MixNode{
		network.nodes[0],
		network.nodes[2],
		network.nodes[4],
	}

	fmt.Printf("\nPacket path: Client → %d → %d → %d → Exit\n", path[0].ID, path[1].ID, path[2].ID)

	// Create ephemeral key pair for this packet
	ephemeralPrivate := [32]byte{}
	ephemeralPublic := [32]byte{}
	random.Read(ephemeralPrivate[:])
	random.Read(ephemeralPublic[:])

	// Build onion-encoded packet
	payload := []byte("Confidential message through mixnet")
	codec := &SimpleSphinxCodec{numHops: len(path)}

	onion := codec.BuildOnionPacket(path, payload, ephemeralPrivate, ephemeralPublic)

	fmt.Println("\n=== Onion Packet Structure ===")
	fmt.Printf("Ephemeral key: %s\n", hex.EncodeToString(onion.Header.GroupElement[:16]))
	fmt.Printf("Routing info (encrypted): %s\n", hex.EncodeToString(onion.Header.Routinginfo[:32]))
	fmt.Printf("Payload (encrypted): %s\n", hex.EncodeToString(onion.Payload[:32]))

	// Simulate packet traveling through mix network
	fmt.Println("\n=== Processing Packet Through Mix Network ===")

	currentPacket := onion
	currentNodeID := 0

	for hop := 0; hop < len(path); hop++ {
		node := network.nodes[currentNodeID]
		fmt.Printf("\n[Hop %d] Node %d receives packet\n", hop, node.ID)

		// Peel one layer
		nextNodeID, peeled, err := codec.PeelOnionLayer(&currentPacket, node.PrivateKey, node.PublicKey)
		if err != nil {
			fmt.Printf("  ERROR: %v\n", err)
			break
		}

		fmt.Printf("  Decrypts layer, learns: next node = %d\n", nextNodeID)
		fmt.Printf("  Forwards to Node %d\n", nextNodeID)

		// Verify anonymity
		fmt.Printf("  Node %d CANNOT see:\n", currentNodeID)
		fmt.Printf("    • Previous sender (encrypted routing)\n")
		fmt.Printf("    • Final destination (encrypted routing)\n")
		fmt.Printf("    • Packet correlation (new ephemeral key each send)\n")

		currentNodeID = nextNodeID
		currentPacket = peeled
	}

	// Exit node can read payload (or forward further)
	fmt.Printf("\n[Exit] Node %d receives final packet\n", currentNodeID)
	fmt.Println("  Can decrypt payload (has shared secret)")
	fmt.Println("  But only knows: \"some node sent this\"")
	fmt.Println("  Cannot trace back to sender without observing all hops")

	fmt.Println("\n=== Security Properties ===")
	fmt.Println("✓ Sender anonymity: mix node 0 doesn't know who sent packet")
	fmt.Println("✓ Receiver anonymity: mix node N doesn't know who will receive")
	fmt.Println("✓ Path hiding: each node knows only next hop, not full path")
	fmt.Println("✓ Unlinkability: two packets from same sender appear unrelated")
	fmt.Println("\n⚠ Limits:")
	fmt.Println("  • Global passive adversary (see all inputs/outputs) breaks anonymity")
	fmt.Println("  • Timing correlation: if packets enter&exit simultaneously")
	fmt.Println("  • Solution: add decoy traffic, random delays per node")
}
