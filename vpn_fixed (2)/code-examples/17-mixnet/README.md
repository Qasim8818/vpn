# Mixnets — Sphinx Packet Encoding for Anonymous Routing

## Problem Statement

**Traditional VPN:** VPN server sees your traffic, your ISP sees VPN server connection.  
**Mixnet:** Packets routed through 3+ relay nodes. Each sees only partial path.  
**Sphinx protocol:** Encryption layering ensures anonymity at each hop.

## Architecture

```
Sender (192.168.1.100)
  ↓ creates onion packet
  [Layer1[Layer2[Layer3[Payload]]]]
  ↓ send to Node 0
  
Node 0 (exit sees: "foo.com")
  ↓ decrypts outer layer, learns: "send to Node 2"
  [Layer2[Layer3[Payload]]]
  ↓ forward
  
Node 2
  ↓ decrypts, learns: "send to Node 4"
  [Layer3[Payload]]
  ↓ forward
  
Node 4 (exit node)
  ↓ decrypts final layer
  Payload (now readable)
  ↓ deliver to recipient
  
Result: No single node sees sender→recipient path
```

## Security Properties

| Property | Guarantee | Threat |
|----------|-----------|--------|
| **Sender anonymity** | Node 0 doesn't know who sent | ISP sees connection to Node 0 |
| **Receiver anonymity** | Exit node doesn't know where packet goes next | Recipient sees connection from Node 4 |
| **Path hiding** | Each node knows only next hop | Global passive adversary (sees all) breaks anonymity |
| **Unlinkability** | Two requests from me are unrelated | Timing correlation: enter→exit same time = linked |

## How Sphinx Works

### 1. Onion Construction

```
Sender chooses path: [Node0, Node2, Node4]

For each hop (REVERSE order: Node4 → Node2 → Node0):
  1. Derive shared key: our ephemeral_secret_key * node_public_key
  2. Encrypt routing info: "next node is Node X"
  3. Decrypt and re-encrypt entire packet (nested)
  
Result: Packet with N encrypted layers
```

### 2. Onion Peeling

```
Each node:
  1. Derive shared key (same as sender did)
  2. Peel one layer: AES-CTR decrypt
  3. Extract "next node" from decryption output
  4. Forward to next node
  5. Cannot see previous sender or final recipient
```

## Real-World Deployments

### **Nym Network** — Privacy-First VPN

- Uses Sphinx packet encoding
- Mix network across 1000+ geographic nodes
- Built for resistance against traffic analysis
- Bandwidth incentives: nodes earn cryptocurrency for relaying

### **Loopix** (Research) — Defenses Against Timing Attacks

- Combines Sphinx with decoy traffic
- Each node adds random delays
- Timing correlation becomes probabilistic

### **Tor Hidden Services** (Partial)

- Tor uses similar 3-hop circuits
- Sphinx-like onion encryption
- Differs in key agreement, cover traffic strategy

## Comparison: Anonymity Approaches

| Approach | Sender Anon | Receiver Anon | Timing Resistant | Complexity |
|----------|---|---|---|---|
| **Single VPN** | Good | Poor | No | Low |
| **Sphinx (3 hops)** | Very Good | Good | No* | Medium |
| **Loopix (Sphinx + jitter)** | Excellent | Good | Yes | High |
| **Tor (3-hop circuit)** | Excellent | Excellent | No | Very High |
| **I2P mix network** | Very Good | Very Good | Partial | High |

*Adds decoy traffic to resist timing attacks

## Deployment Checklist

### Implementation

- [ ] Choose DH curve (x25519 recommended)
- [ ] Implement ephemeral key generation per packet
- [ ] Implement AES-256-CTR per-hop encryption
- [ ] Build routing info format (next node ID, padding strategy)
- [ ] Test packet peeling: ensure only intended recipient reads payload
- [ ] Add MAC (message authentication): prevent tampering

### Operational

- [ ] Recruit mix node operators (at least 5–10 initial)
- [ ] Node discovery: publish node list, key material
- [ ] Path selection: random among all nodes (prevents correlation)
- [ ] Decoy traffic: background packets reduce timing attacks
- [ ] Monitoring: detect node failures, rebalance traffic
- [ ] Key rotation: monthly/quarterly update node keys

### Security

- [ ] Prevent sybil attack: vetted node list (or reputation system)
- [ ] Timing analysis: add jitter (20–50ms per node)
- [ ] Loop prevention: no repeating nodes in path
- [ ] Cover traffic: send dummy packets when idle (costly)
- [ ] Latency budgeting: total path < 5 seconds (user tolerance)

## Threat Model

### Strong Adversary (Global Passive)

**Can:** See all network traffic everywhere  
**Breaks:** Sender anonymity (timing: message enters Node0, exits Node4 at same time)  
**Mitigation:** Nym's decoy traffic, cover traffic (expensive, but works)

### Local Adversary (ISP, Government)

**Can:** See your connection to entry node  
**Breaks:** Sender anonymity (via entry node)  
**Does NOT break:** Receiver anonymity (you can't tell who I'm visiting)  
**Mitigation:** Multihop entry (connect through multiple nodes before payload)

### Node-Compromising Adversary

**Can:** Operate malicious mix node(s)  
**Breaks:** Sender anonymity (if operator controls entry node)  
**Breaks:** Receiver anonymity (if operator controls exit node)  
**Does NOT break:** Anonymity from one node alone (path spans multiple operators)  
**Mitigation:** More nodes, regular audits, incentivize honest operation

## Performance Impact

| Metric | VPN | Mixnet (Nym) | Change |
|--------|-----|---|---|
| Latency | 20–50ms | 500–2000ms | 10–40x slower |
| Bandwidth (client) | 100 Mbps | 10–50 Mbps | 2–10x slower |
| CPU (per packet) | < 1 μs | 50–200 μs | Much slower |
| Cover traffic | None | 20–50% | Significant cost |

**Tradeoff:** Anonymity vs. speed and bandwidth

## Advanced Topics

### 1. **Sphinx Extensions**

- **Blended messages:** variable-length payload (prevent size-based correlation)
- **Reliability:** add path redundancy (send duplicate via different route)
- **Compressible routing:** smaller header format

### 2. **Cover Traffic Strategies**

- **Poisson mixing:** random time between sends (adds latency)
- **Link padding:** always send fixed-size packets (high overhead)
- **Decoy traffic:** background noise when idle

### 3. **Scalability**

- Large mix network (1000+ nodes) creates path selection problem
- Solutions: hierarchical routing, geographic regions

---

**TL;DR:** Sphinx encrypts packets in layers: each node peels one layer, learns only "next node" address. No single node sees sender→recipient. Global passive adversary (watching all traffic) breaks anonymity via timing correlation. Mitigation: add decoy traffic, timing jitter. Latency cost: 10–40x vs. VPN.
