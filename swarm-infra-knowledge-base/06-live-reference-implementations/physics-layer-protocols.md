# Physics Layer Protocols & Coverage Proofs

The physical layer is the foundation of the network. "Money flows, but the network dies without physics."

## 1. Coverage Proofs (Erasure Codes)
To prevent "Ghost Nodes" (nodes spoofing location), we use a Proof-of-Coverage scheme based on fountain codes.

*   **Mechanism**: A station does not broadcast a single "I am here" message.
*   **Sharding**: The heartbeat message is sharded into **5 pieces** using erasure coding.
*   **Transmission**: These 5 pieces are transmitted in sequence over LoRa.
*   **Reconstruction**: Neighboring nodes listen. If the swarm receives at least **3 out of 5** unique pieces (66% quorum), the original message is reconstructed.
*   **Failure**: If <3 pieces are received, the proof fails.
*   **Retry**: Cycle repeats every **18 minutes** (aligned with regulatory duty cycles).

## 2. Signal Monitoring & Blacklisting
*   **Metrics**: RSSI (Signal Strength) and SNR (Signal-to-Noise Ratio) are monitored every **30 seconds**.
*   **Interference**: If a node causes sustained interference (rising noise floor for neighbors), it is flagged.
*   **Action**:
    *   **Tier 1 (Warning)**: Auto-adjustment request sent (lower power).
    *   **Tier 2 (Blacklist)**: If interference persists or node ignores requests, it is **Blacklisted**.
    *   **Consequence**: The network stops routing through the node. **NO REFUNDS** are issued to users during this outage (Force Majeure / Service Maintenance).

## 3. Adaptive Power Voting
*   **Trigger**: High interference density in a sector.
*   **Process**:
    1.  `RadioPhysicsBee` detects the issue.
    2.  Bee initiates an **On-Chain Vote** to regulate transmit power (e.g., "Sector 7 nodes reduce to 5W").
    3.  Consensus reached via smart contract.
    4.  New power settings applied automatically by compliant nodes.

## 4. Quiet Periods
*   **Regulation**: Federally enforced quiet period every **40 minutes**.
*   **Enforcement**: Agents strictly enforce radio silence during these windows to protect the FCC license.
