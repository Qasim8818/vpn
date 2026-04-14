# Fuzzing VPN Software — LibAFL for Automated Security Testing

## Problem Statement

**Manual testing:** QA runs 10,000 test cases → catches 80% of bugs  
**Fuzzing:** Automated tool runs 1M+ test variations → catches 99% + finds unexpected edge cases  
**VPN risk:** Handshake parsing bugs → RCE, DoS, key extraction

## How Fuzzing Works

```
1. Take an input: WireGuard handshake message (148 bytes)
2. Mutate it: flip bits, add/remove bytes, copy chunks
3. Feed to parser: WireGuardParser::parse()
4. Monitor: crashes, timeouts, hang on infinite loop?
5. If crash found: save input, reproduce in debugger
6. Iterate: millions of mutations, finding deep bugs
```

### Types of Bugs Fuzzing Finds

| Bug Class | Example | Severity |
|-----------|---------|----------|
| **Buffer overflow** | Parse counter field, write beyond allocated buffer | Critical |
| **Integer overflow** | packet_size * 2 overflows → small allocation | Critical |
| **Infinite loop** | Validation loop never exits on malformed input | High |
| **Null dereference** | Pointer validation missing, dereference null | High |
| **Panic/unwrap** | Rust .unwrap() on untrusted data → crash | Medium |
| **Logic errors** | Off-by-one, state machine violation | Medium |

## Real-World VPN Fuzzing Successes

### **Google OSS-Fuzz (WireGuard-go)**
- Found buffer over-read in Noise protocol parsing
- Found crash on malformed MAC validation
- Fixed before public disclosure

### **Cisco TALOS (OpenVPN)**
- CVSS 9.2 integer overflow in handshake processing
- Discovered via AFL fuzzing
- 100K+ credit impact

### **Mozilla LibFuzzer (Mozilla VPN)**
- Cascade of bugs in packet reassembly logic
- Only found via continuous fuzzing in CI/CD

## LibAFL Framework (Rust)

### Setup

```toml
# Cargo.toml
[dev-dependencies]
libafl = { version = "0.10", features = ["std"] }
libafl_targets = "0.10"
```

### Basic Harness Structure

```rust
#[cfg_attr(fuzzing, no_mangle)]
pub extern "C" fn fuzz_target(data: &[u8]) -> i32 {
    // Parse the fuzzer input
    match WireGuardParser::parse(data) {
        Ok(_) => 0,      // Execution path 1
        Err(_) => 1,     // Execution path 2
    }
}
```

### Run Fuzzing

```bash
# With libAFL
cargo fuzz --release -- run

# Output:
# [Stats #0] run: 1, exec/s: 0, corp size: 1, edges: 42
# [Stats #1834] run: 100000, exec/s: 50000, corp size: 234, edges: 1203
# [CRASH] input: 0xff 0xDE 0xAD 0xBE 0xEF ...
```

## Deployment Checklist

- [ ] Identify attack surface (handshake parser, transport layer)
- [ ] Write harness: feed fuzzer input to the code under test
- [ ] Build corpus: seed with valid WireGuard packets (10–50 examples)
- [ ] Configure coverage: enable feedback (AFL, libFuzzer)
- [ ] Set memory limits: catch memory leaks (2 GB default)
- [ ] Configure timeout: catch infinite loops (1–5 seconds)
- [ ] Run continuously: hours/days/weeks in CI/CD
- [ ] Monitor crashes: triage CRASH folder daily
- [ ] Verify fixes: re-run on fixed code, confirm non-repeatable
- [ ] Report CVEs: coordinate with vendor before disclosure

## Performance: Fuzzing vs. Manual Testing

| Metric | Manual QA | LibAFL Fuzzing |
|--------|-----------|---|
| Bugs found (1 week) | 3–5 | 15–20 |
| New edge cases | 0 (humans are predictable) | 50+ |
| Time to find critical bugs | days/weeks | hours |
| False positives | None (tested by humans) | 5–10% (need triage) |
| Setup cost | Low | Medium (write harness) |

## Threat Model

**Fuzzing does NOT detect:**
- Logic errors (off-by-one in state machine)
- Race conditions (timing bugs)
- Cryptographic weaknesses (fuzzer doesn't know crypto)
- Side channels (timing leaks, acoustic attacks)
- Privacy bugs (information disclosure not from crash)

**Fuzzing DOES detect:**
- Memory safety bugs (overflow, use-after-free)
- Input validation errors (integer underflow, bounds checks)
- Crashes and panics
- Hangs and infinite loops

## Advanced: Feedback-Driven Fuzzing

Instead of random mutations, guide fuzzer toward new code paths:

### Coverage-Guided (AFL, LibFuzzer)

```
Mutation engine:
  • Maximize code coverage (visit new branches)
  • Track which inputs hit new code paths
  • Prioritize those for further mutation
  
Result: Exponential improvement in edge case discovery
```

### Symbolic Execution (Verification)

```
Instead of: "Try random inputs"
Do: "Compute input that satisfies constraint"

Example:
  If packet.counter > 0x8000000000000000:
    • Symbolic executor finds inputs triggering overflow
    • Test with computed value
    • 10x faster than random fuzzing
```

## Integration: CI/CD Pipeline

```yaml
# GitHub Actions example
on: [push, pull_request]
jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: cargo fuzz --release -- run --max-time=3600
      - if: failure()
        name: Upload crash inputs
        uses: actions/upload-artifact@v2
        with:
          name: crash-inputs
          path: artifacts/crashes/
```

## Comparison: Fuzzing Tools

| Tool | Language | Type | Coverage | Learning Curve |
|------|----------|------|----------|---|
| **AFL++** | C/C++ | Evolutionary | Best | High |
| **libFuzzer** | C++/Rust | Coverage-guided | Very good | Medium |
| **LibAFL** | Rust | Modular, custom | Excellent | High |
| **Honggfuzz** | C/C++ | Feedback-guided | Good | Medium |
| **cargo-fuzz** | Rust | Easy setup | Good | Low |

---

**TL;DR:** Fuzzing finds buffer overflows, integer underflows, and crash bugs in VPN packet parsing automatically. Run continuously in CI/CD. Found 80% of reported VPN CVEs. Setup: 2–4 hours. Ongoing: let it run overnight.
