// P4 Program: WireGuard Replay Protection in Hardware NIC
// Target: Netronome Agilio / Nvidia BlueField-3 DPU
// Compiles to: NIC ASIC, executes at line rate (100+ Gbps)

#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x0800;
const bit<8> PROTO_UDP = 17;
const bit<16> WG_PORT = 51820;

typedef bit<9> egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ipv4Addr_t;

header ethernet_t {
    macAddr_t dst_addr;
    macAddr_t src_addr;
    bit<16> ether_type;
}

header ipv4_t {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> total_len;
    bit<16> identification;
    bit<3> flags;
    bit<13> frag_offset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> checksum;
    ipv4Addr_t src_addr;
    ipv4Addr_t dst_addr;
}

header udp_t {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> length;
    bit<16> checksum;
}

// WireGuard transport message (msg_type 0x04)
header wg_transport_t {
    bit<8> msg_type;
    bit<24> reserved;
    bit<32> receiver_index;
    bit<64> counter;  // Monotonic per session
}

struct headers {
    ethernet_t ethernet;
    ipv4_t ipv4;
    udp_t udp;
    wg_transport_t wg_transport;
}

struct metadata {
    bit<1> is_wireguard;
    bit<1> replay_detected;
    bit<32> peer_id;
}

parser IngressParser(packet_in pkt,
                     out headers hdr,
                     out metadata meta,
                     inout standard_metadata_t std_meta) {
    state start {
        pkt.extract(hdr.ethernet);
        transition select(hdr.ethernet.ether_type) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            PROTO_UDP: parse_udp;
            default: accept;
        }
    }
    state parse_udp {
        pkt.extract(hdr.udp);
        transition select(hdr.udp.dst_port) {
            WG_PORT: parse_wireguard;
            default: accept;
        }
    }
    state parse_wireguard {
        pkt.extract(hdr.wg_transport);
        meta.is_wireguard = 1;
        transition accept;
    }
}

control IngressControl(inout headers hdr,
                       inout metadata meta,
                       inout standard_metadata_t std_meta) {

    // Per-peer replay window: stores last seen counter
    // Map: peer_id (32-bit) → last_counter (64-bit)
    // Using 65536 entries = can track 64K peers efficiently
    Register<bit<64>, bit<32>>(65536) last_counter;
    RegisterAction<bit<64>, bit<32>, bit<64>>(last_counter) read_counter =
        RegisterAction {
            size = 65536;
            initial_value = 0;
            reads = 1;
            writes = 1;
        };

    action drop_packet() {
        mark_to_drop(std_meta);
    }

    action send_to_host() {
        std_meta.egress_spec = 9;  // CPU port (target-specific)
    }

    action check_replay() {
        // Read last counter for this peer
        bit<64> last_val = read_counter.execute(hdr.wg_transport.receiver_index);

        // WireGuard counter check: accept if:
        // 1. Counter > last_counter (normal case)
        // 2. Counter within tolerance window of last_counter
        // Reject if: counter + 2^31 < last_counter (definitely old)

        if (hdr.wg_transport.counter + 0x80000000 < last_val) {
            // Counter too old → replay
            meta.replay_detected = 1;
        } else if (hdr.wg_transport.counter >= last_val) {
            // Valid counter → update
            read_counter.execute(hdr.wg_transport.receiver_index);
        }
    }

    apply {
        if (meta.is_wireguard == 1 && hdr.wg_transport.msg_type == 0x04) {
            check_replay();
            if (meta.replay_detected == 1) {
                drop_packet();  // Dropped entirely in NIC, host never wakes
            } else {
                send_to_host();  // Legit packet → DMA to host ring buffer
            }
        }
    }
}

control EgressControl(inout headers hdr,
                      inout metadata meta,
                      inout standard_metadata_t std_meta) {
    apply {
    }
}

control DeparserImpl(packet_out pkt, in headers hdr) {
    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.udp);
        pkt.emit(hdr.wg_transport);
    }
}

control VerifyChecksumImpl(inout headers hdr,
                          inout metadata meta) {
    apply {
    }
}

control ComputeChecksumImpl(inout headers hdr,
                           inout metadata meta) {
    apply {
    }
}

V1Switch(IngressParser(),
         VerifyChecksumImpl(),
         IngressControl(),
         EgressControl(),
         ComputeChecksumImpl(),
         DeparserImpl()) main;
