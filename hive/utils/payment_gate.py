"""
Payment Gate - Manages refunds, slashing, and incident logging.

Ensures users are made whole if services fail, and penalizes
underperforming nodes to maintain network integrity.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    # Try importing from relative path if inside package
    from .plausible_andon import analytics
except ImportError:
    # Fallback for when running as script/different context
    import sys
    sys.path.append(str(Path(__file__).parent))
    from plausible_andon import analytics


class PaymentGate:
    """
    Manages the 'Customer Service' logic:
    - Auto-refunds on failure
    - Node slashing for instability
    - Incident logging (Discord/File)
    """

    def __init__(self, hive_path: Optional[Path] = None):
        if hive_path is None:
            # Assume we are in hive/utils, so go up one level to hive
            self.hive_path = Path(__file__).parent.parent
        else:
            self.hive_path = hive_path

        self.honeycomb_path = self.hive_path / "honeycomb"
        self.nodes_path = self.honeycomb_path / "nodes.json"
        # intel.json for user "wallets"
        self.intel_path = self.honeycomb_path / "intel.json"

        # State for verbose mode
        self.state_path = self.honeycomb_path / "state.json"

    def process_refund(self,
                       user_handle: str,
                       amount: float,
                       reason: str,
                       node_id: Optional[str] = None) -> Dict[str,
                                                              Any]:
        """
        Process a full refund to the user.

        Args:
            user_handle: The user to refund.
            amount: The amount to refund.
            reason: Why the refund is happening (e.g., "song_not_found", "timeout").
            node_id: The node responsible (if applicable).

        Returns:
            Dict with refund details.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Update User Balance (in intel.json)
        self._credit_user_balance(user_handle, amount)

        # 2. Log Incident
        log_entry = {
            "timestamp": timestamp,
            "type": "refund",
            "user": user_handle,
            "amount": amount,
            "reason": reason,
            "node_id": node_id
        }
        self._log_incident(log_entry)

        # 3. Track in Plausible (RLVR Penalty)
        analytics.track_event(
            event_name="Refund Issued",
            props={
                "user": user_handle,
                "amount": str(amount),
                "reason": reason
            }
        )

        return {
            "status": "refunded",
            "amount": amount,
            "recipient": user_handle,
            "timestamp": timestamp,
            "message": "Refund processed successfully"
        }

    def slash_node(self, node_id: str,
                   percentage: float = 0.01) -> Dict[str, Any]:
        """
        Slash a node's stake for failure.

        Args:
            node_id: The ID of the node to slash.
            percentage: Percentage of stake to slash (default 1%).

        Returns:
            Dict with slashing details.
        """
        if not self.nodes_path.exists():
            return {"error": "Nodes registry not found"}

        try:
            with open(self.nodes_path, 'r') as f:
                data = json.load(f)

            nodes = data.get("nodes", {})
            if node_id not in nodes:
                return {"error": f"Node {node_id} not found"}

            node = nodes[node_id]
            current_stake = node.get("stake", 0.0)
            slash_amount = current_stake * percentage
            new_stake = current_stake - slash_amount

            # Apply slash
            nodes[node_id]["stake"] = new_stake
            nodes[node_id]["last_slashed"] = datetime.now(
                timezone.utc).isoformat()

            # Save
            with open(self.nodes_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Log
            self._log_incident({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "slashing",
                "node_id": node_id,
                "slash_amount": slash_amount,
                "new_stake": new_stake
            })

            # Track in Plausible (System Health)
            analytics.track_event(
                event_name="Node Slashed",
                props={
                    "node_id": node_id,
                    "amount": str(slash_amount)
                }
            )

            return {
                "status": "slashed",
                "node_id": node_id,
                "amount_slashed": slash_amount,
                "remaining_stake": new_stake
            }

        except Exception as e:
            return {"error": f"Slashing failed: {str(e)}"}

    def _credit_user_balance(self, user_handle: str, amount: float) -> None:
        """Credit the user's balance in intel.json."""
        # Note: This is a simplified "wallet" using the listener intel file
        # In a real system, this would be a secure ledger.

        try:
            # We need to read/modify/write intel.json carefully
            # Ideally, we'd use the Queen or a Bee's method, but we are a util.
            # We'll do a direct file op for now, assuming single-threaded
            # access or low contention.

            if not self.intel_path.exists():
                return

            with open(self.intel_path, 'r') as f:
                intel = json.load(f)

            listeners = intel.get("listeners", {}).get("known_nodes", {})

            # Find listener by handle (inefficient but works for small scale)
            target_node_id = None
            if user_handle in listeners:
                target_node_id = user_handle
            else:
                # Try to search by handle field
                for nid, data in listeners.items():
                    if data.get("handle") == user_handle:
                        target_node_id = nid
                        break

            if not target_node_id:
                # Create a temporary entry if not exists (unlikely if they just
                # paid)
                target_node_id = user_handle
                listeners[target_node_id] = {"handle": user_handle}

            # Update balance
            current_balance = listeners[target_node_id].get(
                "wallet_balance", 0.0)
            listeners[target_node_id]["wallet_balance"] = current_balance + amount

            # Add note
            notes = listeners[target_node_id].get("notes", [])
            notes.append(
                f"Refunded ${amount} at {
                    datetime.now(
                        timezone.utc).isoformat()}")
            listeners[target_node_id]["notes"] = notes

            # Save
            intel["listeners"]["known_nodes"] = listeners
            with open(self.intel_path, 'w') as f:
                json.dump(intel, f, indent=2)

        except Exception as e:
            print(f"Error crediting user: {e}")

    def _log_incident(self, data: Dict[str, Any]) -> None:
        """Log incident to file and optionally Discord."""

        # 1. File Log
        log_line = json.dumps(data)
        log_path = self.honeycomb_path / "incident_log.jsonl"
        with open(log_path, 'a') as f:
            f.write(log_line + "\n")

        # 2. Discord Log
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return

        # Check verbose mode
        is_verbose = self._is_verbose_logging()

        # Logic:
        # - Always log to file (done)
        # - Send to Discord only if Critical OR Verbose mode is ON
        # Refunds are "routine" (quiet) unless verbose.
        # Node slashing is arguably critical, but let's follow the prompt:
        # "default mode is quiet – routine refunds happen silently... Discord channel only gets a summary if explicitly toggled to verbose"

        if not is_verbose and data.get("type") == "refund":
            return

        # Construct message
        message = ""
        if data.get("type") == "refund":
            message = f"💸 **Refund Issued**\nUser: `{
                data.get('user')}`\nAmount: `${
                data.get('amount')}`\nReason: {
                data.get('reason')}"
        elif data.get("type") == "slashing":
            message = f"⚔️ **Node Slashed**\nNode: `{
                data.get('node_id')}`\nAmount: `{
                data.get('slash_amount')}` tokens"

        try:
            requests.post(webhook_url, json={"content": message}, timeout=2)
        except Exception:
            pass  # Fail silently for logging

    def _is_verbose_logging(self) -> bool:
        """Check if verbose logging is enabled."""
        if not self.state_path.exists():
            return False

        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            return state.get("settings", {}).get("verbose_logging", False)
        except Exception:
            return False
