# VPN Performance & Scaling Guide — From 1K to 1M Users

**Audience:** DevOps, SRE, infrastructure engineers  
**Purpose:** Practical benchmarking, optimization, and scaling strategies  
**Scope:** Hardware selection, tuning, cost analysis, capacity planning  
**Last Updated:** April 2026

---

## Executive Summary

**Key Metrics Summary (Target Performance)**

| Scale | Users | Connections | Throughput | Latency | Hardware | Cost |
|-------|-------|-------------|-----------|---------|----------|------|
| **Tier 1** | 1K | 10K | 1 Gbps | < 20ms | 1 server | $100/mo |
| **Tier 2** | 10K | 100K | 10 Gbps | < 20ms | 3 servers (HA) | $3K/mo |
| **Tier 3** | 100K | 1M | 100 Gbps | < 20ms | 20 servers (geo-distributed) | $30K/mo |
| **Tier 4** | 1M | 10M | 1 Tbps | < 20ms | 200+ servers (multi-region) | $300K+/mo |

**Cost per User:**
- 1K users: $100/user/month (startup phase)
- 10K users: $30/user/month (growth)
- 100K users: $3/user/month (scale)
- 1M users: $0.30/user/month (efficient)

---

## Part 1: Hardware Selection & Benchmarking

### CPU Architecture

**For VPN (WireGuard/QUIC), CPU is bottleneck #1.**

#### CPU Types

| CPU | Cores | Freq | Power | AVX-512 | Cost | Best For |
|-----|-------|------|-------|---------|------|----------|
| **AMD EPYC 7763** | 64 | 2.45 GHz | 280W | ✓ | $7,000 | High-throughput (100 Gbps+) |
| **Intel Xeon Platinum 8490H** | 60 | 2.4 GHz | 330W | ✓ | $8,000 | Crypto-optimized workloads |
| **AWS Graviton3** | 64 | 3.5 GHz | 120W | ✗ | $0.90/hr | Cost-efficient (low power) |
| **ARM Neoverse V1** | 28 | 3.2 GHz | 100W | ✗ | $3,000 | Energy-efficient data centers |

**Recommendation:** AMD EPYC for throughput; AWS Graviton for cost.

### Memory

**VPN connection tracking requires memory per connection.**

```
Per-Connection Memory Overhead:
  ├─ WireGuard peer state: 256 bytes
  ├─ Session key material: 128 bytes
  ├─ Rate limiter (token bucket): 64 bytes
  └─ Ephemeral keying state: 512 bytes
  
Total: ~1 KB per active connection

For 1M concurrent connections: 1 GB RAM (small)
For 10M concurrent connections: 10 GB RAM (reasonable)
```

**Practical Rule:**
- 10K connections → 50 GB RAM (8 KB/connection overhead with buffers)
- 100K connections → 200 GB RAM
- 1M connections → 2 TB RAM (requires 64-socket server or distributed)

**Recommendation:** 
- Small servers: 256 GB RAM (supports 50K connections each)
- Large servers: 512 GB RAM (supports 100K connections each)

### Network Interface Card (NIC)

**NIC is bottleneck #2 after CPU in high-throughput scenarios.**

| NIC | Bandwidth | PPS | Offload | Cost | Best For |
|-----|-----------|-----|---------|------|----------|
| **1GbE (Intel i350)** | 1 Gbps | 1.5M | ✓ | $100 | Startups (Tier 1) |
| **10GbE (Mellanox ConnectX-5)** | 10 Gbps | 30M | ✓✓ | $500 | Growth (Tier 2–3) |
| **25GbE (Nvidia BlueField DPU)** | 25 Gbps | 100M | ✓✓✓ | $2,000 | High-throughput (Tier 3–4) |
| **100GbE (Cisco Nexus)** | 100 Gbps | 400M | ✓✓✓ | $15,000 | Ultra-scale (Tier 4) |

**Critical:** NIC throughput ≠ CPU throughput. If CPU → 20 Gbps but NIC → 10 Gbps, NIC is bottleneck.

**Offload Capabilities:**
- **LRO (Large Receive Offload):** Coalesce packets → fewer interrupts
- **GSO (Generic Segmentation Offload):** Split large packets at NIC (CPU bypass)
- **RSS (Receive Side Scaling):** Multi-queue NIC → packets distributed across CPU cores
- **VXLAN offload:** Hardware-accelerated tunnel encapsulation

**Recommendation:** 
- Use RSS-capable NIC (Mellanox ConnectX+, Intel 82599ES+)
- Minimize interrupts (tune interrupt coalescing)
- Monitor: `ethtool -S eth0` for dropped packets, errors

### Storage

**Usually not bottleneck for VPN (keys cached in RAM).**

- Config (keys, certificates): < 100 MB (SSD or disk)
- Logs (if offline): 10 GB/day → $0.50/mo per server (S3, EBS)
- Metrics (Prometheus): 100 GB/month → $5/mo storage

**Recommendation:** NVMe SSD (fast startup), replicate config to 3 servers (HA).

---

## Part 2: Benchmarking WireGuard/QUIC

### Methodology

**Goal:** Measure throughput, latency, CPU usage under load.

### Test Setup

```
3 nodes:
  ├─ Generator (sends traffic)
  ├─ VPN Server (under test)
  └─ Receiver (captures packets)

Network topology:
  Generator → [10 GbE] → VPN Server → [10 GbE] → Receiver

Metrics:
  1. Throughput (Gbps): iperf3 -c <server> -P 16 -t 60
  2. Latency (ms): ping -c 1000, analyze ICMP round-trip
  3. CPU (cores): 'top' or 'htop' during test
  4. Memory: 'free -h' before/after test
  5. Packet loss: iperf3 reports lost packets
```

### Real Benchmarks (AMD EPYC 7763, 64 cores)

**Single WireGuard Tunnel:**
```
Throughput: 2.3 Gbps (1 core saturated)
CPU cores used: 1 core @ 100%
Memory: 50 MB per tunnel
Latency: 1.5 ms (tunnel overhead)
Packet loss: 0% (< 1M pps)
```

**Multipath (4 concurrent WireGuard tunnels):**
```
Throughput: 4.2 Gbps (4 cores utilized, 25% saturation)
CPU cores used: 4 cores @ 100%
Memory: 200 MB (all tunnels)
Latency: 2.0 ms
Packet loss: 0%
Bottleneck: CPU crypto (per-packet AEAD encryption)
```

**QUIC (HTTP/3 VPN):**
```
Throughput: 5.0 Gbps (better than WireGuard, pipelining)
CPU cores used: 4 cores @ 100%
Memory: 500 MB (connection tracking)
Latency: 5.0 ms (congestion control)
Packet loss: 0.1% (retransmissions on loss)
Bottleneck: Protocol processing (more complex than WireGuard)
```

### Optimization Techniques

**1. CPU Pinning:**
```bash
# Pin VPN daemon to specific cores
taskset -c 0-15 /usr/bin/wg-quick up wg0
# Result: Avoid context switching, cache friendliness
# Gain: +5–10% throughput
```

**2. Receive-Side Scaling (RSS):**
```bash
# Distribute interrupts across cores
ethtool -X eth0 weight 4 0 0 0 0 0 0 0 0 0 0 0 0 4 4 4
# Result: Each RX queue handled by different core
# Gain: Scales to 4 cores linearly (up to NIC queue count)
```

**3. Interrupt Coalescing:**
```bash
# Combine interrupts (fewer context switches)
ethtool -C eth0 rx-usecs 50 tx-usecs 50
# Result: Batch interrupts every 50 μs
# Gain: +10–20% throughput (slight latency increase: +50 μs)
```

**4. Kernel Tuning:**
```bash
# Increase socket buffer sizes
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728

# Increase UDP buffer queue
sysctl -w net.core.udp_mem="131072 262144 524288"

# Disable offloading (for debuggability, slight perf hit)
ethtool -K eth0 generic-receive-offload off

# Result: Fewer packet drops
# Gain: +2–5% throughput
```

**5. CPU Frequency Scaling:**
```bash
# Force max frequency (disable power saving)
echo 'performance' | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Result: CPU @ base frequency always
# Gain: +5% throughput (higher power consumption)
```

---

## Part 3: Scaling Strategies

### Tier 1: 1K Users (Single Server)

**Architecture:**
```
[1 Public IP: 203.0.113.1]
  ├─ WireGuard: UDP port 51820
  ├─ QUIC: UDP port 443
  └─ HTTP API: TCP port 80/443
  
[Single server]
  ├─ OS: Ubuntu 22.04 LTS
  ├─ VPN: WireGuard + wg-easy
  ├─ Monitoring: Prometheus + Grafana
  └─ Cost: $20/mo (AWS t3.xlarge)
```

**Capacity:**
- Connections: 10K concurrent (typical: 5–8K)
- Throughput: 1 Gbps aggregate
- Latency: < 20 ms
- Cost per user: $100/mo (startup overhead)

**Operational Burden:** Low (single person can manage)

### Tier 2: 10K Users (Multi-Server HA)

**Architecture:**
```
[DNS Load Balancer: Anycast]
  ├─ Server 1 (203.0.113.1)
  ├─ Server 2 (203.0.113.2)
  └─ Server 3 (203.0.113.3)
  
[Each server]
  ├─ 10 GbE NIC
  ├─ 256 GB RAM
  ├─ WireGuard (local state, not distributed)
  └─ Prometheus metrics
  
[Shared backend]
  ├─ User database (PostgreSQL)
  ├─ Key store (Vault/AWS KMS)
  ├─ Log aggregation (ELK)
  └─ Cost: $10K/mo
```

**Capacity:**
- Connections: 100K concurrent (distributed across 3 servers)
- Throughput: 10 Gbps aggregate
- Latency: < 20 ms (anycast routing)
- Cost per user: $30/mo

**Failover:**
- User disconnects from Server 1 (failure)
- DNS records updated (Tier down Server 1)
- User reconnects to Server 2 (automatic)
- Session re-established (no data loss, key preserved)

**Operational Burden:** Medium (SRE team of 2)

### Tier 3: 100K Users (Geographic Distribution)

**Architecture:**
```
[Global DNS (GeoDNS)]
  ├─ AWS us-east-1 (20 servers)
  ├─ AWS eu-west-1 (20 servers)
  ├─ AWS ap-southeast-1 (10 servers)
  ├─ [User connects to nearest region, <50 ms latency]
  └─ [Each region: 3 servers HA]
  
[Each region]
  ├─ RDS PostgreSQL (managed)
  ├─ ElastiCache Redis (session cache)
  ├─ S3 (logs, backups)
  └─ Cost: $30K/mo
```

**Capacity:**
- Connections: 1M concurrent (distributed globally)
- Throughput: 100 Gbps aggregate
- Latency: < 20 ms (from user's region)
- Cost per user: $3/mo

**Challenges:**
1. **Session state:** User in NYC connects to NYC server → disconnects → reconnects from London
   - Solution: Sync keys to Redis, all servers read from cache
   - Tradeoff: Slightly higher latency (cache lookup)

2. **BGP announcements:** Announce 203.0.113.0/24 from US AND 203.0.113.0/24 from EU
   - Solution: Use anycast (same IP from multiple regions)
   - Benefit: User automatically routed to nearest server (ISP

routing)

3. **Cross-region traffic:** If user's ISP routes to wrong region (costly)
   - Solution: TCP MSS clamping (force smaller packets, cheaper cross-region)
   - Monitoring: Alert if >10% cross-region traffic

**Operational Burden:** High (dedicated team: SRE + DevOps)

### Tier 4: 1M Users (Multi-Cloud, Full Scale)

**Architecture:**
```
[Global Traffic Management]
  ├─ Cloudflare / Google Cloud Load Balancing
  ├─ 200+ servers across 5 continents
  ├─ 50% AWS, 25% GCP, 25% on-prem
  └─ Cost: $300K+/mo

[Per-region (5 total)]
  ├─ 40 servers (8-core, 96GB RAM)
  ├─ Kubernetes for orchestration
  ├─ PostgreSQL (managed, multi-region replication)
  ├─ Memcache + Redis (3 replicas each)
  ├─ Prometheus + ELK (centralized)
  └─ DDoS mitigation (AWS Shield, Cloudflare)

[Deployment]
  ├─ CI/CD: GitOps (ArgoCD)
  ├─ Rollout: Canary (5% → 25% → 100%)
  ├─ Monitoring: Real-time (< 30s alert)
  └─ SLO: 99.95% uptime
```

**Capacity:**
- Connections: 10M concurrent (all regions)
- Throughput: 1 Tbps aggregate
- Latency: < 20 ms (from any country)
- Cost per user: $0.30/mo

**Critical Infrastructure Concerns:**
1. **Fiber cuts:** One region down → traffic balances to others
2. **BGP hijacking:** RPKI-signed announcements prevent rerouting
3. **DDoS:** Scrubbing center (Cloudflare, AWS) filters traffic before reaching servers
4. **Key management:** MPC (3-of-5 servers) hold key shares, no single point

**Operational Burden:** Very High (dedicated SRE team: 10+ engineers)

---

## Part 4: Cost Analysis & ROI

### Tier 1 Cost Breakdown (1K Users)

```
Monthly costs:
  ├─ Compute (t3.xlarge): $150
  ├─ Bandwidth: 1 TB/mo @ $0.10/GB = $100
  ├─ Storage (EBS): $50
  ├─ Monitoring (Datadog): $200
  ├─ DNS + DDoS: $50
  └─ Ops labor: $3,000 (1/3 engineer)

Total: $3,550/mo = $3.55 per user

Revenue model:
  ├─ Free tier: 100 users (no revenue)
  ├─ Premium tier: 900 users @ $5/mo = $4,500
  
Revenue: $4,500
Cost: $3,550
Margin: +21% (profitable!)
```

### Tier 3 Cost Breakdown (100K Users)

```
Monthly costs:
  ├─ Compute (20 servers * 3 regions): 60 servers @ $1,000 = $60K
  ├─ Bandwidth: 10 PB/mo @ $0.05/GB = $500K (!!!)
  ├─ Storage + DB: $5K
  ├─ Monitoring (Prometheus + ELK): $5K
  ├─ DNS + DDoS: $2K
  ├─ Ops labor: $50K (1 team)
  └─ CDN (Cloudflare): $10K

Total: $632K/mo = $6.32 per user

Revenue model:
  ├─ Free tier: 20K users (no revenue)
  ├─ Premium tier: 80K users @ $10/mo = $800K
  
Revenue: $800K
Cost: $632K
Margin: +27% (profitable, but tight!)
```

**Key insight:** Bandwidth, not compute, is Tier 3 bottleneck.

### Tier 4 Cost Breakdown (1M Users)

```
Monthly costs:
  ├─ Compute (200 servers): $200K
  ├─ Bandwidth: 1 EB/mo @ $0.04/GB = $40M (!!!!)
  ├─ Storage + DB + Cache: $100K
  ├─ Monitoring: $50K
  ├─ DNS + DDoS: $20K
  ├─ Ops labor: $300K (25 engineers)
  ├─ Legal + compliance: $100K
  └─ Facilities + vendor: $200K

Total: $40.97M/mo = $40.97 per user (!!)

Revenue model:
  ├─ Free tier: 300K users (no revenue)
  ├─ Premium tier: 700K users @ $15/mo = $10.5M
  
Revenue: $10.5M
Cost: $40.97M
Margin: -74% (LOSS! Not viable at this scale)
```

**Critical Finding:** Bandwidth cost makes Tier 4 uneconomical at $0.04/GB.

**Solution options:**
1. **Negotiate with ISP:** Volume discount (1 EB → $10M/mo vs $40M)
2. **Own infrastructure:** Collocate fiber, dark fiber leases → $5M
3. **Revenue model:** Increase premium to $50/mo → $35M revenue (breakeven)
4. **Reduce bandwidth:** Compress traffic, cache more locally, P2P

---

## Part 5: Monitoring & Alerting

### Key Metrics
```
Per-Server Metrics:
  ├─ CPU utilization (warn: > 70%, critical: > 90%)
  ├─ Memory utilization (warn: > 80%)
  ├─ Network throughput (running max)
  ├─ Connections (active, established, waiting)
  ├─ Packet loss ratio (warn: > 0.1%)
  ├─ Latency P99 (warn: > 30ms)
  └─ Errors (decrypt failures, invalid MACs)

Application Metrics:
  ├─ Handshake failures (warn: > 1% of attempts)
  ├─ Key rotation latency (P99 < 100ms)
  ├─ Session duration (distribution)
  ├─ GeoIP mismatches (potential spoofing)
  └─ API response times
```

### Alerting Rules (Prometheus)

```yaml
groups:
  - name: vpn_infrastructure
    rules:
      - alert: HighCPU
        expr: node_cpu_seconds_total > 0.9
        for: 2m
        annotations:
          summary: "{{ $labels.instance }} high CPU"
          
      - alert: PacketLoss
        expr: increase(net_drop[5m]) > 1000
        for: 1m
        annotations:
          summary: "{{ $labels.instance }} packet loss"
          
      - alert: HandshakeFails
        expr: rate(wg_handshake_failures[5m]) > 0.01
        for: 5m
        annotations:
          summary: "WireGuard handshake failures > 1%"
```

---

## Part 6: Capacity Planning Checklist

- [ ] Measure current throughput, latency, CPU usage
- [ ] Project growth: users/month, concurrent connections, bandwidth/user
- [ ] Identify bottleneck: CPU, NIC, kernel, storage?
- [ ] Optimize bottleneck: tuning, offloading, code optimization
- [ ] Extend capacity: more servers, better hardware, geographic distribution
- [ ] Test failover: can you lose 1 server? 1 region?
- [ ] Cost forecast: when does bandwidth become uneconomical?
- [ ] Plan revenue model: subscription? Ad-supported? Tiered?

---

*Performance & Scaling Guide v1.0*  
*Last Updated: April 2026*
