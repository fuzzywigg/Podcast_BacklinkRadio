"""
Radio Physics Bee - Manages the physical layer of the radio network.

Responsibilities:
- Monitor RSSI/SNR metrics from stations.
- Verify "Coverage Proofs" (Fountain Codes / Erasure Codes).
- Detect interference and initiate "Power Voting".
- Blacklist noisy or compliant nodes.
"""

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import BaseBee


class RadioPhysicsBee(BaseBee):
    """
    Manages the physical layer interactions.

    This bee bridges the gap between the digital swarm and the physical radio hardware.
    It simulates (or interfaces with) the logic for:
    - Coverage Verification (Erasure Codes)
    - Interference Management (Power Voting)
    - Node Reputation (Blacklisting)
    """

    BEE_TYPE = "radio_physics"
    BEE_NAME = "Radio Physics Bee"
    CATEGORY = "technical"

    # Physics Constants
    COVERAGE_QUORUM_PERCENT = 0.66  # 66% of shards needed
    SHARDS_TOTAL = 5
    SHARDS_NEEDED = 3
    RETRY_INTERVAL_MINUTES = 18
    INTERFERENCE_THRESHOLD_DB = -80  # Trigger voting if noise > -80dBm

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute radio physics tasks.

        Task payload can include:
        - action: verify_coverage|monitor_interference|power_vote
        - target_node: node_id to check
        """
        self.log("Scanning physical layer...")

        # 1. Read current network state from intel
        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        # If specific task
        if task:
            action = task.get("payload", {}).get("action")
            target = task.get("payload", {}).get("target_node")

            if action == "verify_coverage":
                return self._verify_coverage(target, known_nodes.get(target, {}))
            elif action == "power_vote":
                return self._initiate_power_vote(task.get("payload", {}))

        # 2. General Monitoring Loop (if no specific task)
        # Scan all nodes for coverage proof expiry or interference
        results = {"verified": 0, "failed": 0, "blacklisted": 0, "votes_triggered": 0}

        for node_id, node_data in known_nodes.items():
            # A. Check Coverage Proof
            last_proof = node_data.get("last_proof_at")
            if self._needs_proof(last_proof):
                proof_result = self._verify_coverage(node_id, node_data)
                if proof_result["success"]:
                    results["verified"] += 1
                else:
                    results["failed"] += 1

            # B. Check Interference (Simulated reading)
            interference_level = self._measure_interference(node_id)
            if interference_level > self.INTERFERENCE_THRESHOLD_DB:
                self.log(f"High interference at {node_id}: {interference_level}dBm")
                # Trigger power vote
                self._trigger_power_vote(node_id, interference_level)
                results["votes_triggered"] += 1

        return {"action": "monitoring_scan", "results": results}

    def _verify_coverage(self, node_id: str, node_data: dict[str, Any]) -> dict[str, Any]:
        """
        Verify coverage using Erasure Codes / Fountain Codes logic.

        Simulates receiving 5 shards. Needs 3 to reconstruct.
        """
        self.log(f"Verifying coverage for {node_id}...")

        # In a real system, this would read actual packets from the air/gateway.
        # Here we simulate the reception probability based on 'reliability' score if present,
        # or random chance.

        reliability = node_data.get("reliability", 0.95)

        # Simulate receiving 5 shards
        received_shards = 0
        for _ in range(self.SHARDS_TOTAL):
            if random.random() < reliability:
                received_shards += 1

        success = received_shards >= self.SHARDS_NEEDED

        timestamp = datetime.now(timezone.utc).isoformat()

        # Update Node Intel
        updates = {
            "last_proof_at": timestamp,
            "last_proof_shards": received_shards,
            "status": "online" if success else "offline_proof_failed",
        }

        if not success:
            self.log(
                f"Node {node_id} FAILED coverage proof ({received_shards}/{self.SHARDS_TOTAL} shards)."
            )
            # If failed, potentially blacklist or mark for penalty?
            # For now, just mark offline.
        else:
            self.log(f"Node {node_id} PASSED coverage proof.")

        self.add_listener_intel(node_id, updates)

        return {"success": success, "shards": received_shards, "node_id": node_id}

    def _measure_interference(self, node_id: str) -> float:
        """
        Simulate measuring RSSI/Noise floor.
        Returns noise level in dBm (e.g., -90 is good, -60 is bad).
        """
        # Random fluctuation around -95dBm (noise floor)
        base_noise = -95.0
        fluctuation = random.uniform(-5, 20)  # Occasional spikes
        return base_noise + fluctuation

    def _trigger_power_vote(self, node_id: str, noise_level: float) -> None:
        """
        Create a task to initiate an on-chain power reduction vote.
        """
        vote_task = {
            "type": "radio_physics",
            "payload": {
                "action": "power_vote",
                "sector_node": node_id,
                "noise_level": noise_level,
                "proposal": "reduce_power_3db",
            },
        }
        self.write_task(vote_task)
        self.post_alert(
            f"Interference detected at {node_id} ({noise_level:.1f}dBm). Initiating Power Vote.",
            priority=True,
        )

    def _initiate_power_vote(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the logic to start a vote.
        In reality, this would write a tx to the blockchain proposing the parameter change.
        """
        sector = payload.get("sector_node")
        proposal = payload.get("proposal")

        self.log(f"Initiating On-Chain Vote: {proposal} for sector {sector}")

        # Simulate smart contract interaction
        tx_hash = f"0x{uuid.uuid4().hex}"

        return {"vote_initiated": True, "tx_hash": tx_hash, "proposal": proposal}

    def _needs_proof(self, last_proof_iso: str | None) -> bool:
        """Check if 18 minutes have passed since last proof."""
        if not last_proof_iso:
            return True

        last = datetime.fromisoformat(last_proof_iso)
        now = datetime.now(timezone.utc)
        diff_minutes = (now - last).total_seconds() / 60

        return diff_minutes >= self.RETRY_INTERVAL_MINUTES

    def blacklist_node(self, node_id: str, reason: str) -> None:
        """Blacklist a noisy or rogue node."""
        self.log(f"BLACKLISTING node {node_id}: {reason}", level="warning")

        self.add_listener_intel(
            node_id,
            {
                "status": "blacklisted",
                "blacklist_reason": reason,
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        self.post_alert(f"Node {node_id} has been BLACKLISTED. Reason: {reason}", priority=True)


if __name__ == "__main__":
    bee = RadioPhysicsBee()
    print(bee.run())
