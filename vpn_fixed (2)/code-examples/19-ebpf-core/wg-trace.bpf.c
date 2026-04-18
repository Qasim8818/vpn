// eBPF CO-RE: WireGuard Packet Tracer (Kernel 5.4+)
//
// This program traces WireGuard packet processing without kernel headers
// Uses CO-RE (Compile Once, Run Everywhere) and BTF (BPF Type Format)
// to automatically adapt to any kernel version's struct layout
//
// Build: clang -O2 -target bpf -c wg-trace.bpf.c -o wg-trace.bpf.o
// Load: sudo bpftool prog load wg-trace.bpf.o type tracepoint
// Run: sudo cat /sys/kernel/debug/tracing/trace_pipe

#include "vmlinux.h"  // Generated from kernel BTF: bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

// Event to userspace ring buffer
typedef struct {
    u32 peer_id;
    u64 bytes_in;
    u64 bytes_out;
    u32 handshakes;
} wg_stats;

// Ring buffer maps event to userspace
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} wg_events SEC(".maps");

// Per-peer statistics
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 100000);
    __type(key, u32);
    __type(value, wg_stats);
} peer_stats SEC(".maps");

// CO-RE macro: Read struct field at any kernel version
// Kernel might have different layout, but BPF loader fixes offsets at load time
#define BPF_CORE_READ_INTO(ptr, sz, src, field) \
    bpf_probe_read_kernel(ptr, sz, &((typeof(src))src)->field)

// Kprobe: Hook WireGuard send function
// void wg_packet_send_staged_packets(struct wg_peer *peer)
SEC("kprobe/wg_packet_send_staged_packets")
int BPF_KPROBE(trace_wg_send, struct wg_peer *peer) {
    // Parse: struct wg_peer {
    //   struct wg_device *device;
    //   u64 internal_id;
    //   u32 serial;
    //   ... (many fields)
    // }

    // Using CO-RE: automatically read field at current kernel's offset
    u64 internal_id = BPF_CORE_READ(peer, internal_id);
    u32 serial = BPF_CORE_READ(peer, serial);

    bpf_printk("WG: Send to peer %llu (serial %u)", internal_id, serial);

    // Update per-peer statistics
    wg_stats *stats = bpf_map_lookup_elem(&peer_stats, (u32 *)&internal_id);
    if (stats) {
        __sync_fetch_and_add(&stats->bytes_out, 1500);  // Assume standard packet size
    }

    return 0;
}

// Kprobe: Hook WireGuard receive function
// void wg_packet_receive(struct wg_device *wg, struct sk_buff *skb)
SEC("kprobe/wg_packet_receive")
int BPF_KPROBE(trace_wg_receive, struct wg_device *wg, struct sk_buff *skb) {
    // struct sk_buff {
    //   unsigned int len;
    //   unsigned int data_len;
    //   ...
    // }

    u32 len = BPF_CORE_READ(skb, len);
    bpf_printk("WG: Receive %u bytes", len);

    return 0;
}

// Tracepoint: Hook kernel crypto operations used by WireGuard
// trace_event:crypto_skcipher_encrypt_done (CHACHA20_POLY1305)
SEC("tracepoint/crypto/skcipher_encrypt_done")
int BPF_TRACEPOINT(trace_chacha20, struct trace_event_raw_skcipher_encrypt_done *ctx) {
    // This event fires every time WireGuard encrypts a packet
    // Can be used to calculate throughput, detect anomalies

    u64 nbytes = ctx->databytes;  // From trace event
    bpf_printk("ChaCha20: encrypted %llu bytes", nbytes);

    return 0;
}

// Ring buffer event: send stats to userspace
SEC("timer")
int periodic_stats(void) {
    // This runs periodically (from userspace)
    // Iterate all peers and send statistics

    wg_stats *s, zero = {};

    // (Iteration would be done in userspace due to BPF map iteration limits)
    // Just demonstrate the ring buffer push:

    s = bpf_ringbuf_reserve(&wg_events, sizeof(*s), 0);
    if (!s)
        return 0;

    s->peer_id = 1;
    s->bytes_in = 1000000;
    s->bytes_out = 2000000;
    s->handshakes = 5;

    bpf_ringbuf_submit(s, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
__u32 _version SEC("version") = 1;

/*
KERNEL COMPATIBILITY:

This program compiles ONCE:
  $ clang -O2 -target bpf -c wg-trace.bpf.c -o wg-trace.bpf.o

Then loads on ANY kernel with:
  $ bpftool prog load wg-trace.bpf.o type kprobe

The BPF loader (libbpf) automatically:
  1. Reads kernel BTF from /sys/kernel/btf/vmlinux
  2. Reads compiled program's BTF
  3. Relocates struct field accesses to match current kernel
  4. Adjusts offsets for wg_peer->internal_id, sk_buff->len, etc.

Result: Same .o file works on:
  - Linux 5.4 (field offset X)
  - Linux 5.15 (field offset Y, different layout)
  - Linux 6.1 (field offset Z)

Without CO-RE:
  - Would need to recompile for each kernel version
  - Or manually write offset tables for each version
  - Major maintenance burden

KEY ADVANTAGE FOR VPN:
- Trace WireGuard on any system without kernel headers
- Get observability even on systems you don't control
- Single artifact, zero maintenance
*/
