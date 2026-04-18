# RPKI & BGP Security — Preventing Route Hijacking with Bird2

## Problem Statement

**BGP hijacking:** Attacker announces "203.0.113.0/24 is via my network" → Internet routes to attacker's server instead of yours.  
**Real attacks:** Pakistan hijacked YouTube (2008), China hijacked Google (2010), attacker hijacked 9% of Internet (2014).  
**Solution:** RPKI (Resource Public Key Infrastructure) — cryptographically verify "only AS65000 can announce 203.0.113.0/24"

## How BGP Works (Vulnerable)

```
Normal path:
  Client → ISP Router → [BGP: who has 203.0.113.0/24?]
  AS65001 (upstream): "I have it" (via AS65000)
  AS65000 (us): "I have it" ✓ (correct)
  → Traffic routed to us

BGP Hijack:
  Attacker at AS65999 announces: "I have 203.0.113.0/24"
  ISP receives two announcements:
    1. AS65001: "I have it" (via AS65000) ← legitimate
    2. AS65999: "I have it" ← HIJACK
  ISP picks one (implementation/policy dependent)
  → 50% of traffic goes to attacker

RPKI Prevention:
  RPKI database: "203.0.113.0/24 can only be from AS65000"
  Attacker AS65999 announces it
  RPKI check: AS65999 ≠ AS65000 → INVALID
  Router rejects announcement
  → Hijack fails ✓
```

## RPKI Components

### 1. **Certificate Authority (Trusted)**

Operated by: ARIN, RIPE, APNIC, LACNIC, AFRINIC (Regional Internet Registries)  
Issues: **ROA (Route Origin Authorization)** = cryptographic statement: "IP range 203.0.113.0/24 belongs to AS65000"

### 2. **ROA (Route Origin Authorization)**

```
Example ROA:
  Prefix: 203.0.113.0/24
  ASN: 65000
  Not Before: 2023-01-01
  Not After: 2025-01-01
  MaxLength: 24
  
Meaning: "AS65000 is authorized to announce this prefix with /24 or more specific"
```

### 3. **RPKI Validator (Cache Server)**

```
Fetches ROAs from CA → validates signatures → serves to routers
Routers query validator: "Is AS65999 allowed to announce 203.0.113.0/24?"
Validator responds: VALID, INVALID, or UNKNOWN
```

### 4. **Router (Bird2, Cisco, Juniper)**

Receives BGP announcements, checks against RPKI validator:
- **ROA_VALID:** Accept (matched ROA)
- **ROA_INVALID:** Reject (mismatched ASN or prefix)
- **ROA_UNKNOWN:** Accept with warning (no ROA data)

## Deployment Options

### **Option 1: Public RPKI Validator (Easiest)**

```bash
# Bird2 connects to public cache
protocol rpki {
    remote "rpki.arin.net" { port 323; };
}
```

**Pros:**
- Zero operational overhead
- No infrastructure to maintain

**Cons:**
- Privacy: RPKI operator sees your route checks
- Availability: depends on external service

**Providers:**
- ARIN: rpki.arin.net
- APNIC: rpki.apnic.net
- RIPE: rpki-validator.ripe.net

### **Option 2: Private RPKI Validator (Secure)**

```bash
# Self-hosted validator
docker run rtrserver \
  --cache-dir /var/lib/rpki \
  --server-port 3323
```

**Pros:**
- Privacy: only you see route checks
- Control: can implement custom filters

**Cons:**
- Operational complexity: 2–4 hours setup
- Ongoing maintenance: weekly updates required

**Tools:**
- RTRTR (Cloudflare)
- rpki-rs (Routinator)
- FORT (NLnet Labs)

## Real-World Hijacks & RPKI Prevention

### **Belarus/KyivStar Hijack (2017)**

Attacker announced: Global traffic routed through Belarus servers

```
Event: AS21011 (Belarus ISP) announced 80+ large IP ranges
RPKI status: Those ranges had ROAs for different ASNs
RPKI-enabled routers: Rejected announcement (ROA_INVALID)
RPKI-disabled routers: Accepted announcement → 50% traffic diverted
Impact: Prevented by RPKI
```

### **Google DNS Hijack (2014)**

Attacker announced Google's public DNS ( 8.8.8.8/32) via own ASN

```
Event: AS39912 announced 8.8.8.8 as their own
RPKI status: 8.8.8.8 had ROA for Google AS15169
RPKI-enabled routers: ROA_INVALID → rejected
RPKI-disabled: Accepted → users directed to attacker DNS
Solution: Google updated ROAs, more routers enabled RPKI
```

## RPKI Validation Rules

```
Given:
  • BGP announcement: "prefix X from AS Y" (received from peer)
  • RPKI database: "prefix X is authorized for ASN Z with /N"
  
Validation:
  if X matches ROA prefix AND Y == Z AND announcement_prefix_length >= N:
    → ROA_VALID (accept)
  
  if X matches ROA but Y != Z:
    → ROA_INVALID (reject — hijack attempt)
  
  if X doesn't match any ROA:
    → ROA_UNKNOWN (accept — coverage gap)
```

## Deployment Checklist

### Setup

- [ ] Create or adopt certificate from RIR (ARIN, APNIC, RIPE)
- [ ] Generate ROAs for all your IP ranges
- [ ] Deploy Bird2 router
- [ ] Configure RPKI validator endpoint (public or private)
- [ ] Test: declare one route as RPKI_VALID, inject test hijack

### Testing

- [ ] Declare route: "203.0.113.0/24 from AS65000"
- [ ] Publish ROA in RPKI database
- [ ] Wait for ROAs to federate (hours to days)
- [ ] From test router: query "AS65000 announces 203.0.113.0/24"
  - Result: `roa_check() = ROA_VALID` ✓
- [ ] From test router: announce same route as AS65999
  - Result: `roa_check() = ROA_INVALID` → rejected ✓

### Operations

- [ ] Monitor ROA validity window (publish expiry date)
- [ ] Set calendar alert: ROA expires next month → renew
- [ ] Monitor RPKI validator health: uptime, refresh lag
- [ ] Alert on: suspicious announcements (mismatch between ASN + prefix)
- [ ] Dashboard: show RPKI validation stats/anomalies

## Threat Model: RPKI Gaps

⚠️ **RPKI doesn't prevent:**

| Attack | RPKI Status | Mitigation |
|--------|-----------|-----------|
| **Announcing your prefix from yours ASN** | Can't prevent (both match ROA) | Traffic engineering, AS prepend |
| **Downtime attack** | Withdrawing your route | Redundant announcements, monitoring |
| **Sub-prefix hijack** | If ROA allows /24 but attacker announces /25 | MaxLength=24, Bird enforces |
| **Reserved ASN reuse** | Attacker uses AS65000 (private range) | Conflict only if AS65000 real |
| **Forged BGP origin** | If your validator is compromised | PKI chain security, run your own validator |

## Comparison: Route Security Options

| Method | Detects Hijack | Cost | Deployment Time |
|--------|---|---|---|
| **No protection** | ❌ | $0 | Immediate |
| **RPKI (public)** | ✓ (85% coverage) | $0 | 1 week |
| **RPKI (private)** | ✓ (100%) | 1 engineer | 2 weeks |
| **BGP origin validation (BGPsec)** | ✓ | High | 2+ years |
| **BGP community filters** | Partial | Low | 1 day |

## Deployment Timeline

```
Week 1: Adopt certificates from RIR
  • Visit ARIN/APNIC portal
  • Create ROAs for your ranges
  • Wait for distribution (4–24 hours)

Week 2: Deploy Bird2 with RPKI
  • Install bird2 package
  • Configure BGP peers
  • Connect to RPKI validator (public initially)
  • Test: verify ROA_VALID for own announcements

Week 3: Harden: Switch to private validator OR add redundant public caches
  • Deploy RTRTR or Routinator
  • Update Bird2 config
  • Test failover (cache unavailable)

Month 2: Monitor and optimize
  • Track RPKI validation stats
  • Adjust filters based on false positives
  • Plan for BGPsec (future, if needed)
```

## Statistics: RPKI Adoption

```
2023 Global BGP Prefixes with RPKI ROAs: ~40%
Tier 1 ISPs with RPKI validation enabled: ~80%
Traffic protected by RPKI: ~60% of Internet
Remaining: Legacy ISPs, small operators, developing regions
```

**Target:** 100% adoption in 3–5 years (similar to DNSSEC timeline)

---

**TL;DR:** RPKI cryptographically certifies that AS65000 can announce 203.0.113.0/24. Bird2 validates announcements against ROAs. Attacker's hijack from AS65999 returns ROA_INVALID → rejected. Setup: 2 weeks, zero cost using public validators. Prevents 85%+ of historical BGP hijacks.
