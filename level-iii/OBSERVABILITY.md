# VPN Observability Framework — Monitoring, Logging, Alerting

**Audience:** SRE, DevOps, security monitoring  
**Purpose:** Production-grade observability for VPN infrastructure  
**Scope:** Metrics, traces, logs, dashboards, alerts  
**Last Updated:** April 2026

---

## Executive Summary

**Three Pillars of Observability:**
1. **Metrics:** Gauges (CPU %), counters (connections), histograms (latency)
2. **Logs:** Structured events (handshake, auth failure, DDoS)
3. **Traces:** Request journey (client → LB → VPN server → exit)

**Goal:** Debug any issue within 15 minutes using these signals.

---

## Part 1: Metrics & Dashboarding

### Core VPN Metrics

| Metric | Type | Purpose | Alert Threshold |
|--------|------|---------|---|
| **Connections/sec** | Counter | User signup rate | > 10K/sec = DDoS |
| **Active connections** | Gauge | Current load | > 10M = capacity |
| **CPU utilization** | Gauge | Hardware headroom | > 80% = scale |
| **Memory utilization** | Gauge | OOM risk | > 90% = restart |
| **Packet loss** | Gauge | Network issues | > 0.1% = investigate |
| **Latency P50/P99** | Histogram | User experience | P99 > 50ms = slow |
| **Encryption errors** | Counter | Auth failures | > 1%/min = attack |
| **Key rotation time** | Histogram | Cryptographic perf | > 1s = slow |
| **DPA attacks detected** | Counter | Security events | > 10/day = alert sec |

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  
scrape_configs:
  - job_name: 'vpn-servers'
    static_configs:
      - targets: ['vpn1.example.com:9090', 'vpn2.example.com:9090']
    
  - job_name: 'gateways'
    static_configs:
      - targets: ['gateway1.example.com:9090']

  - job_name: 'kubernetes'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: vpn.*

recording_rules:
  - name: vpn_rules
    rules:
      - record: vpn:connections:rate5m
        expr: rate(vpn_active_connections[5m])
      
      - record: vpn:latency:p99
        expr: histogram_quantile(0.99, vpn_latency_seconds_bucket)
```

### Grafana Dashboards

**Dashboard: VPN Overview**
```
Row 1 (Status):
  ├─ Active users (large gauge: 523,000)
  ├─ Uptime (large: 99.97%)
  ├─ Global throughput (large: 450 Gbps)
  └─ Geography (map: traffic heatmap)

Row 2 (Performance):
  ├─ Latency P50/P99 (time series graph)
  ├─ Packet loss (line graph)
  ├─ CPU per region (bar chart)
  └─ Memory (stacked area)

Row 3 (Security):
  ├─ Encryption failures (time series)
  ├─ Failed auth attempts (counter)
  ├─ DDoS attacks detected (heat map)
  └─ Anomaly score (gauge: 0–100)

Row 4 (Debugging):
  ├─ Error logs (tail, colorized)
  ├─ Slow handshakes (top 10)
  └─ Geographic anomalies (list)
```

---

## Part 2: Structured Logging

### Log Events (Structured JSON)

```json
{
  "timestamp": "2026-04-12T15:32:45.123Z",
  "level": "INFO",
  "event": "VPN_HANDSHAKE_INITIATION",
  "user_id": "user_abc123",
  "session_id": "sess_xyz789",
  "client_ip": "203.0.113.10",
  "peer_public_key": "Iveqar+BvxlmQDBrcnqqLFEi2D/At8DYwJVuc6j+Uks=",
  "version": "1.0.0",
  "duration_ms": 42,
  "status": "SUCCESS"
}
```

**Benefits of structured logs:**
1. Parseable (JSON → grep, jq, tools)
2. Correlatable (session_id ties user journeys together)
3. Queryable (ElasticSearch → Kibana dashboards)
4. Secure (sensitive fields stripped before storage)

### Critical Events to Log

```
VPN_HANDSHAKE_INITIATION
  └─ Includes: timestamp, user_id, client_ip, duration, status

VPN_HANDSHAKE_FAILURE
  └─ Includes: reason (invalid_mac, replay_check, crypto_fail), user_id, attempt_count

KEY_ROTATION
  └─ Includes: old_key_id, new_key_id, rotation_type (scheduled, emergency), duration

SECURITY_EVENT_DPA
  └─ Includes: event_type (timing_anomaly, side_channel), severity, remediation

RATE_LIMIT_EXCEEDED
  └─ Includes: user_id, limit_type (bandwidth, connections), actual_vs_limit

ANOMALY_DETECTED
  └─ Includes: anomaly_type (geo_jump, size_anomaly, timing), score (0-100), action_taken
```

### Logging Best Practices

**DO:**
- ✅ Log structured events (JSON)
- ✅ Include correlation IDs (trace every request)
- ✅ Redact PII (IP → hash, user_id not password)
- ✅ Use appropriate levels (ERROR for real problems, not noisy)
- ✅ Timestamp in UTC (never local time)

**DON'T:**
- ❌ Log plaintext keys (even in DEBUG)
- ❌ Log full session state (too much data)
- ❌ Log at INFO level for every packet (volume explosion)
- ❌ Disable logging in production (for "performance"; measure first)

---

## Part 3: Distributed Tracing

### Trace Flow Example

```
POST /api/login (web)
  ├─ trace_id: uuid-123
  └─ span_id: span-001
    │
    ├─→ Auth service (300ms)
    │    ├─ span_id: span-002
    │    └─ DB query (50ms)
    │         └─ span_id: span-003
    │
    ├─→ Key management (500ms)
    │    ├─ span_id: span-004
    │    ├─ Get key (10ms)
    │    ├─ Derive ephemeral (200ms)
    │    └─ Sign certificate (290ms)
    │
    └─→ VPN server assignment (100ms)
         └─ span_id: span-005

Total request latency: 1.2 seconds
Critical path: Key derivation (500ms) + signing (290ms)
Optimization: Parallelize if possible
```

### OpenTelemetry SDK (Go Example)

```go
import "go.opentelemetry.io/otel"

func LoginHandler(ctx context.Context, username, password string) {
    tracer := otel.Tracer("vpn-auth")
    
    // Start span for entire request
    ctx, span := tracer.Start(ctx, "login_handler")
    defer span.End()
    
    // Span for authentication
    ctx, authSpan := tracer.Start(ctx, "authenticate_user")
    err := authenticateUser(ctx, username, password)
    authSpan.End()
    
    if err != nil {
        span.AddEvent("authentication_failed", trace.WithAttributes(
            attribute.String("error", err.Error()),
        ))
        return
    }
    
    // Span for key generation
    ctx, keySpan := tracer.Start(ctx, "generate_keys")
    keys := generateEphemeralKeys(ctx)
    keySpan.End()
    
    // Export trace to collector
    otel.GetTracerProvider().ForceFlush(context.Background())
}
```

---

## Part 4: Alerting Rules

### Severity Levels

| Level | Response Time | Example |
|-------|---|---|
| **INFO** | No action | User connected |
| **WARNING** | Investigate within hours | Latency P99 > 40ms |
| **CRITICAL** | Respond within 15 min | Packet loss > 1% |
| **EMERGENCY** | Respond immediately | > 50% servers down |

### Prometheus Alert Examples

```yaml
alert: HighPacketLoss
  expr: increase(net_rx_dropped_total[5m]) > 1000000
  for: 1m
  annotations:
    severity: warning
    summary: "{{ $labels.instance }} losing {{ $value | humanize }} packets"

alert: HandshakeFailureRate
  expr: rate(vpn_handshake_failures_total[5m]) > 0.01
  for: 5m
  annotations:
    severity: critical
    summary: "Handshake failure rate > 1%"
    action: "Check: DDoS? Certificate expired? Protocol change?"

alert: ServerDown
  expr: up{job="vpn-servers"} == 0
  for: 2m
  annotations:
    severity: emergency
    summary: "VPN server {{ $labels.instance }} is DOWN"
    action: "Page on-call, start investigation"
```

### Escalation Policy

```
CRITICAL alert:
  1. Page on-call engineer (Slack, PagerDuty)
  2. Notify Slack channel #vpn-incidents
  3. Open incident in Jira (auto-create)
  4. Start incident bridge (Zoom conference)
  5. If unresolved after 15 min: Page manager
  6. If unresolved after 30 min: Page VP
```

---

## Part 5: Anomaly Detection (ML)

### Unsupervised Learning

**Goal:** Detect unusual traffic without a labeled training set.

**Algorithm: Isolation Forest**

```
Normal user: 100 MB/day, 8 AM–6 PM, NYC ISP
Anomaly user: 50 GB/day, 24/7, rotating ISP

Isolation Forest score:
  • Normal user: 0.15 (easy to isolate, not anomalous)
  • Anomaly user: 0.92 (hard to isolate, very different)

Threshold: Score > 0.7 → Alert
```

### Metrics to Analyze

```
Per-user metrics:
  ├─ Bytes/day (distribution)
  ├─ Concurrent sessions (unusual jumps)
  ├─ Unique IPs (change detection)
  ├─ Connection durations (outliers)
  ├─ Packet size distribution (DPI evasion?)
  └─ Time-of-day pattern (5 AM usage = suspicious?)

ML model: Isolation Forest + DBSCAN clustering
Training: 30 days of normal traffic
Output: Anomaly score per user per hour (0–1)
Threshold: 0.8 → investigation
```

---

## Part 6: Cost of Observability

| Component | Scale | Cost |
|---|---|---|
| **Prometheus** | 100K metrics | $500/mo (self-hosted) or $2K/mo (managed) |
| **Grafana** | 50 dashboards | $300/mo (open-source) or $1K/mo (Cloud) |
| **ELK Stack** | 100 GB/day logs | $3K/mo self-hosted, $5K+/mo (Elastic Cloud) |
| **Datadog** | Simpler integration | $20K+/mo (all-in-one) |
| **Custom (open source)** | Self-managed | Staff time (1 FTE) = $120K/yr |

**Rule of thumb:** Observability costs 10–15% of total VPN operations budget.

---

*Observability Framework v1.0*  
*Last Updated: April 2026*
