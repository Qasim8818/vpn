// Circom circuit: ZK-SNARK for VPN membership (Merkle tree)
// Proves: "I am in the valid users set" without revealing which user
// 
// Trust model:
// - Authority publishes Merkle root of valid users
// - Each user gets: (secret, merkle_path) — kept private
// - User creates proof showing: I know secret+path that hash to root
// - Server verifies proof without learning: who the user is

pragma circom 2.0.0;

include "poseidon.circom";
include "merkle_proof.circom";

template VPNAuthCircuit(depth) {
    // PRIVATE INPUTS (known only to user, never revealed)
    signal input secret;                         // User's secret, e.g. hash of password
    signal input pathElements[depth];             // Merkle path: sibling hashes
    signal input pathIndices[depth];              // Left/right indicator at each level

    // PUBLIC INPUTS (sent in proof, known to everyone)
    signal input root;                           // Merkle root (published by authority)
    signal input nullifier;                      // H(secret || nonce) for anti-replay
    signal input nonce;                          // Fresh nonce from server

    // CONSTRAINTS

    // Constraint 1: Compute nullifier
    // Proves user knows the secret without revealing it
    // nullifier = Poseidon(secret, nonce)
    component nullifierHasher = Poseidon(2);
    nullifierHasher.inputs[0] <== secret;
    nullifierHasher.inputs[1] <== nonce;
    
    nullifierHasher.out === nullifier;  // CONSTRAINT: must be equal

    // Constraint 2: Verify Merkle proof
    // Proves user is in the valid-users set
    // Computes leaf from secret, then verifies path to root
    
    component leaf = Poseidon(1);
    leaf.inputs[0] <== secret;

    component tree = MerkleProof(depth);
    tree.leaf <== leaf.out;
    tree.root <== root;
    
    for (var i = 0; i < depth; i++) {
        tree.pathElements[i] <== pathElements[i];
        tree.pathIndices[i] <== pathIndices[i];
    }
    
    tree.valid === 1;  // CONSTRAINT: this leg must be valid

    // Result:
    // - Prover (user) knows: secret, pathElements, pathIndices
    // - Verifier (server) checks: proof is valid, nullifier not seen before
    // - Server learns: NOTHING about user identity
    //   (any user from the tree could have generated this proof)
}

component main(depth) = VPNAuthCircuit(20);  // 20-level tree = 2^20 = 1M users
