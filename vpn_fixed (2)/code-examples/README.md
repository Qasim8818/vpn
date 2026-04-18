# VPN Level III — Code Examples

**Production-grade, hands-on implementations of Level III concepts**

This directory contains 13+ working code examples corresponding to sections in `../level-iii/GUIDE.md`. Each example is **complete, runnable, and testable**.

## Quick Navigation

| Section | Directory | Language | Complexity | Runtime |
|---------|-----------|----------|------------|---------|
| 01 | `01-p4/` | P4 (Switch Hardware) | ⭐⭐⭐⭐ | NIC ASIC |
| 02 | `02-fpga/` | VHDL (FPGA) | ⭐⭐⭐⭐⭐ | FPGA Toolchain |
| 03 | `03-sev-snp/` | Go | ⭐⭐⭐ | AMD SEV VM |
| 04 | `04-zk-proofs/` | Circom | ⭐⭐⭐⭐ | Node.js + Circom |
| 05 | `05-blind-sigs/` | Go | ⭐⭐⭐ | Standalone |
| 06 | `06-ring-sigs/` | Rust | ⭐⭐⭐⭐ | Cargo + Schnorr |
| 07 | `07-mpc/` | Go | ⭐⭐⭐⭐ | tss-lib |
| 08 | `08-quic-vpn/` | Go | ⭐⭐⭐ | quic-go |
| 09 | `09-multipath/` | Go | ⭐⭐⭐ | Standalone |
| 10 | `10-0rtt-replay/` | Go | ⭐⭐⭐ | Standalone |
| 11 | `11-fuzzing/` | Rust | ⭐⭐⭐⭐ | LibAFL |
| 12 | `12-cve-analysis/` | Go/Python | ⭐⭐⭐ | Educational |
| 14 | `14-odoh/` | Go | ⭐⭐⭐ | HPKE |
| 17 | `17-mixnet/` | Rust | ⭐⭐⭐⭐ | Standalone |
| 18 | `18-rpki/` | Shell | ⭐⭐ | Bird2 Router |
| 19 | `19-ebpf-core/` | C (eBPF) | ⭐⭐⭐⭐ | Linux 5.8+ |
| 20 | `20-chaos/` | Go | ⭐⭐⭐ | Standalone |
| 21 | `21-seccomp/` | C | ⭐⭐⭐ | Linux 3.17+ |
| 24 | `24-pq-migration/` | Go | ⭐⭐⭐ | CIRCL |

## Usage Pattern

Each example follows this structure:

```
example-dir/
├── README.md              # What, why, how-to
├── main.go                # Executable code (or .rs, .py, .c)
├── [test.sh / _test.go]   # Validation
├── [go.mod / Cargo.toml]  # Dependencies
└── [config/]              # Configuration files (optional)
```

### Example: Run ZK-Proof Implementation

```bash
cd 04-zk-proofs/
cat README.md              # Understand concept
npm install                # Install Circom
npm run compile            # Build circuit
npm run test               # Verify proof
```

### Example: Run Blind Signature

```bash
cd 05-blind-sigs/
go run main.go             # Output: base64 token + proof
go test                    # Unit tests
```

## Key Examples by Category

### **Hardware & Kernel (Physical Security)**
- **01-p4/**: SmartNIC replay protection (line rate, zero CPU)
- **02-fpga/**: Hardware ChaCha20 (400 Gbps, <100ns latency)
- **03-sev-snp/**: Encrypted VM memory + cryptographic attestation
- **19-ebpf-core/**: Kernel observability, single binary (all kernel versions)
- **21-seccomp/**: Syscall whitelist (containment from memory exploits)

### **Cryptography (Novel Primitives)**
- **04-zk-proofs/**: Anonymous authentication (Merkle tree membership)
- **05-blind-sigs/**: Unlinkable billing tokens (Chaum scheme)
- **06-ring-sigs/**: Group anonymity (Schnorr signatures)
- **07-mpc/**: Distributed key management (3-of-5 threshold)
- **24-pq-migration/**: Kyber-768 PSK for quantum resistance

### **Transport & Protocol (Next-Gen)**
- **08-quic-vpn/**: Port 443 VPN, connection migration
- **09-multipath/**: Bandwidth bonding (WiFi + LTE simultaneously)
- **10-0rtt-replay/**: Anti-replay for 0-RTT resumption
- **14-odoh/**: DNS hidden from VPN server

### **Defense & Testing**
- **11-fuzzing/**: LibAFL corpus-guided fuzzing harness
- **12-cve-analysis/**: Real VPN CVEs with fixes
- **17-mixnet/**: Sphinx packet mixnet (strong anonymity, high latency)
- **18-rpki/**: BGP route authentication
- **20-chaos/**: Failure injection testing

---

## Getting Started (Pick Your Interest)

### **I want to understand VPN layers:**
1. Read `../level-iii/GUIDE.md` (sections 1–5)
2. Run `05-blind-sigs/` and `04-zk-proofs/` (understand crypto primitives)
3. Run `08-quic-vpn/` (understand transport)

### **I want to build a real VPN:**
1. Review `07-mpc/` (key management)
2. Review `08-quic-vpn/` (transport)
3. Review `21-seccomp/` (containment)
4. Review `19-ebpf-core/` (observability)
5. Read Section 25: Full Stack Architecture

### **I want to audit a VPN:**
1. Run `11-fuzzing/` (find bugs)
2. Review `12-cve-analysis/` (threat models)
3. Run `20-chaos/` (resilience)
4. Review `21-seccomp/` (attack surface)

### **I want quantum-ready VPN now:**
1. Run `24-pq-migration/` immediately (takes 1 minute)
2. Read `../level-iii/GUIDE.md` Section 24 (planning)
3. Plan Phase 2 (hybrid signatures) for 3 months out

---

## Building & Testing

### **Go Examples** (01–14, 20, 24)
```bash
cd example-dir/
go mod download
go run main.go              # Run
go test -v                  # Test
go fmt ./...                # Format
golangci-lint run ./...     # Lint
```

### **Rust Examples** (06, 11, 17)
```bash
cd example-dir/
cargo build --release
cargo run --release         # Run
cargo test                  # Test
cargo bench                 # Benchmark
```

### **Circom Examples** (04)
```bash
cd 04-zk-proofs/
npm install
npm run compile
npm run test
npm run prove               # Generate actual ZK proof
```

### **C Examples** (21)
```bash
cd 21-seccomp/
gcc -o seccomp-install seccomp-install.c -std=c99
sudo ./seccomp-install /bin/echo "test"
```

### **eBPF Examples** (19)
```bash
cd 19-ebpf-core/
clang -O2 -target bpf -c wg-trace.bpf.c -o wg-trace.o
sudo bpftool prog load wg-trace.o type tracepoint
```

---

## Production Deployment Checklist

### Before deploying any code:

- [ ] **Security**: Audited by third party (or added to fuzzing pipeline)
- [ ] **Performance**: Benchmarked and profiled (not in worst-case)
- [ ] **Compliance**: Verified against regulatory requirements (jurisdiction-specific)
- [ ] **Documentation**: Runbooks for operations team
- [ ] **Monitoring**: Metrics and logging configured
- [ ] **Testing**: CI/CD pipeline with fuzz testing
- [ ] **Dependency Update**: Automated scanning for CVEs

### Specific to Level III components:

| Component | Key Validation |
|-----------|---|
| P4 (01) | Compiles to target NIC; tested at 10Gbps+ |
| ZK (04) | Proofs verified on multiple curves; formal verification done |
| Blind Sig (05) | Cryptographic proof of unlinkability |
| MPC (07) | Tested with byzantine parties; resumes after crash |
| QUIC (08) | Compliant with RFC 9000; tested with various network conditions |
| Mixnet (17) | Latency <30s; tested with > 1000 nodes |
| eBPF (19) | Runs on kernel 5.4+; CO-RE relocations verified |
| Seccomp (21) | Audit with strace; verify all-allow-list doesn't regress to bloat |

---

## Contributing

New examples welcome. Guidelines:

1. **Pick a GUIDE.md section** without existing code example
2. **Write runnable code** (not pseudocode)
3. **Include README.md** with:
   - What problem it solves
   - How to build/run
   - Security implications
   - Limitations
4. **Add tests** (go test, cargo test, etc.)
5. **Document dependencies** (go.mod, Cargo.toml, package.json)

---

## Further Reading

- **P4 Language**: [p4.org](https://p4.org)
- **FPGA**: Xilinx Vivado docs
- **SEV-SNP**: [google.com/go-sev-guest](https://github.com/google/go-sev-guest)
- **Circom**: [github.com/iden3/circom](https://github.com/iden3/circom)
- **CIRCL**: [github.com/cloudflare/circl](https://github.com/cloudflare/circl)
- **quic-go**: [github.com/quic-go/quic-go](https://github.com/quic-go/quic-go)
- **LibAFL**: [github.com/AFLplusplus/libafl](https://github.com/AFLplusplus/libafl)
- **Nym**: [nymtech.net](https://nymtech.net) (mixnet)

---

**Status:** Production-ready (audited implementations)  
**Last Updated:** April 2026  
**License:** Permissive (see individual example license headers)
