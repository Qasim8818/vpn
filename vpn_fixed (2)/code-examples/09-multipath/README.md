# Multipath VPN — Simultaneous Network Paths for Throughput & Resilience

## Problem Statement

**Single-path VPN:** One network interface → bottleneck is device's slowest link.  
**Mobile reality:** WiFi + LTE both available → why not use both?  
**Multipath VPN:** Stripe traffic across WiFi, LTE, Ethernet → aggregate 120+ Mbps, automatic failover.

## Architecture

```
Device
  ├─ WiFi (100 Mbps, 50ms RTT)
  ├─ LTE (20 Mbps, 100ms RTT)
  └─ Ethernet (1 Gbps, 1ms RTT)
       ↓ (Multipath Scheduler)
       ↓ Route traffic to minimize latency or maximize throughput
       ↓
       VPN Gateway (reassembles packets)
       ↓
       Internet
```

## Key Concepts

### 1. **Path Selection**

Different strategies for different traffic types:

| Strategy | Best For | Usage |
|----------|----------|-------|
| **Lowest RTT** | Gaming, VoIP, real-time | All packets on fastest path |
| **Highest BW** | Downloads, streaming | Highest-capacity path |
| **Weighted** | Mixed workload | Bandwidth/RTT² ratio splitting |
| **Striping** | Parallel transfers | Round-robin across all paths |

### 2. **Traffic Allocation**

Given paths with different BW/RTT, allocate fractions:

```
Path weights = (BW_i / RTT_i²) / Σ(BW_j / RTT_j²)

Example:
  WiFi: 100 Mbps / (0.05s)² = 40,000 "units"
  LTE: 20 Mbps / (0.1s)² = 2,000 "units"
  Total: 42,000 units
  
  WiFi allocation = 40,000 / 42,000 = 95%
  LTE allocation = 2,000 / 42,000 = 5%
```

### 3. **Packet Reassembly**

VPN gateway must reorder packets that arrive out-of-order:

```
Sender
  Packet 1 → WiFi (arrives t=10ms)
  Packet 2 → LTE (arrives t=40ms)
  Packet 3 → WiFi (arrives t=20ms)
  
Receiver
  Packet 1 received at t=10ms ✓
  Packet 3 received at t=20ms (buffer: waits for packet 2)
  Packet 2 received at t=40ms ✓
  Deliver to app: [1, 2, 3] in order
```

## Real-World Deployments

### **MPTCP (Multipath TCP)** — Kernel-Level (Linux 4.9+)

Use multiple TCP sub-flows, Linux kernel reassembles:

```bash
# Enable MPTCP on Android/Linux
sysctl -w net.mptcp.enabled=1

# Applications automatically use multiple paths
```

**Pros:** Kernel handles everything, transparent to apps  
**Cons:** Requires server support, not all ISPs allow MPTCP

### **WireGuard + Custom Multipath Layer**

Implement multipath above WireGuard (Section 09 approach):

```bash
# Device has eth0 (WiFi) + wwan0 (LTE)
# Create two WireGuard interfaces
wg-quick up wg0-wifi   # Over WiFi
wg-quick up wg0-lte    # Over LTE

# Application multiplexer decides which to use per packet
```

**Pros:** Full control, explicit per-packet routing  
**Cons:** Manual implementation, app changes needed

### **Google Quic Usage** (YouTube, Google Maps)

- QUIC supports connection migration
- Packets flow through available paths
- Automatic failover when path degrades
- Used in YouTube for seamless WiFi↔LTE switches

## Deployment Checklist

- [ ] Identify all available network paths (WiFi, LTE, Ethernet, etc.)
- [ ] Measure path characteristics: bandwidth, RTT, packet loss
- [ ] Choose allocation strategy (throughput vs. latency)
- [ ] Implement packet sequencing (to handle out-of-order delivery)
- [ ] Add reassembly buffer at VPN gateway (configurable window)
- [ ] Implement failover (what happens when WiFi drops?)
- [ ] Add metrics: per-path throughput, packet loss, latency
- [ ] Test: mobile phone switching WiFi while downloading file
- [ ] Monitor: device battery impact (LTE uses more power than WiFi)
- [ ] Optimize: don't use all paths if one is much better (save battery)

## Performance Numbers

### Aggregation Gains

| Scenario | Single Best | Multipath | Improvement |
|----------|------------|-----------|-------------|
| WiFi + LTE | 100 Mbps | 95% of 100 = 95 Mbps | Neutral (picks WiFi) |
| WiFi + LTE degraded | 20 Mbps | 95% of 100 + 5% of 20 = 96 Mbps | 4.8x |
| WiFi + LTE + Ethernet | 1 Gbps | 99% of 1000 = 990 Mbps | Same (Ethernet sole bottleneck) |

### Failover Speed

| Scenario | Single-Path | Multipath |
|----------|-----------|-----------|
| WiFi drops during download | 2–5 sec (TCP timeout + retry) | 50ms (LTE already active) |
| LTE glitch | 100ms–2s retransmission timeout | < 50ms (WiFi + Ethernet compensate) |

## Comparison: Multipath Options

| Option | Layer | Control | Complexity | Deploy Time |
|--------|-------|---------|-----------|-----------|
| **MPTCP** | TCP | Kernel | Medium | 1 week |
| **QUIC migrate** | UDP (QUIC) | App | Medium | 2 weeks |
| **Custom multipath** | App/VPN | Full | High | 4 weeks |
| **Bonding (Linux)** | Link layer | Kernel | High | 2 weeks |

## Threat Model

**Attacker has no direct multipath attacks** (it's architectural, not cryptographic).

However:

⚠️ **Path correlation:** If attacker can see packets on both WiFi and LTE, they can link them (timestamp-based attack).
- Mitigation: Add random jitter to packet timing per path

⚠️ **Path flooding:** Attacker floods one path → system over-allocates to other paths → congestion
- Mitigation: Rate limiting per path, capacity tracking

⚠️ **Asymmetric paths:** Packets go out WiFi, return on LTE → correlatable
- Mitigation: Natural on cellular (different providers), add decoy traffic

## Advanced Topics (Not Covered Here)

- **Congestion control algorithm** (how to measure available bandwidth per path?)
- **Packet scheduling** (how often switch between paths?)
- **Rate limiting** (fairness when paths have different capacities)
- **TCP subflow priority** (which subflow gets retransmitted traffic?)
- **Energy efficiency** (WiFi is cheap, LTE is expensive — avoid LTE if not needed)

---

**TL;DR:** Multipath VPN aggregates network capacity across WiFi/LTE/Ethernet for 120+ Mbps on mobile devices. Failover is automatic (no 2–5s timeout). Implementation: custom scheduler if full control needed, MPTCP if kernel support available, QUIC if latency matters.
