"""
Payout Processor Bee - Manages financial transactions, refunds, and treasury.

Responsibilities:
- Process refunds (100% back on content failure).
- Enforce stake slashing (1% penalty on node crash).
- Manage "Prompt Air Gap" for payment messages (sanitization).
- Route payments via optimal path (Onramp vs Web3).
"""

from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import BaseBee


class PayoutProcessorBee(BaseBee):
    """
    Manages the flow of value (Real Crypto & DAO Credits).

    Enforces the "Customer is Always Right" refund policy:
    - Content failed? 100% Refund.
    - Node crashed? 100% Refund + 1% Node Stake Slash.
    """

    BEE_TYPE = "payout_processor"
    BEE_NAME = "Payout Processor Bee"
    CATEGORY = "monetization"

    # Constants
    REFUND_WINDOW_SECONDS = 5
    SLASH_PENALTY_PERCENT = 0.01  # 1%

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute payout tasks.

        Task payload can include:
        - action: process_refund|slash_stake|route_payment
        - transaction_data: details of the tx
        """
        self.log("Processing financial operations...")

        if not task:
            return {"status": "idle"}

        action = task.get("payload", {}).get("action")

        if action == "process_refund":
            return self._process_refund(task.get("payload", {}))
        elif action == "slash_stake":
            return self._slash_stake(task.get("payload", {}))
        elif action == "route_payment":
            return self._route_payment(task.get("payload", {}))

        return {"error": "Unknown action"}

    def _process_refund(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Execute an immediate 100% refund.
        """
        user_wallet = payload.get("user_wallet")
        amount = payload.get("amount")
        reason = payload.get("reason", "content_delivery_failure")
        tx_id = payload.get("original_tx_id")

        self.log(f"Initiating REFUND: {amount} to {user_wallet}. Reason: {reason}")

        # 1. Select Payment Path (Fastest)
        path = self._select_payment_path()

        # 2. Construct Transaction (MCP Flow Simulation)
        refund_tx = {
            "to": user_wallet,
            "value": amount,
            "data": "0x",  # Simple transfer
            "path": path,
            "nonce": self._get_nonce(),
        }

        # 3. Broadcast (Simulated)
        success = True  # Assume success for simulation

        # 4. Log & Alert
        self.post_alert(f"REFUND ISSUED: {amount} to {user_wallet} ({reason})", priority=True)

        # 5. Discord Webhook (Simulated via log)
        self.log(f"DISCORD_WEBHOOK_SENT: Refund processed for {user_wallet}")

        return {
            "status": "refunded",
            "amount": amount,
            "wallet": user_wallet,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _slash_stake(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Slash a node's stake for failure.
        """
        node_id = payload.get("node_id")
        stake_amount = payload.get("current_stake", 1000)  # Default mock stake

        penalty = stake_amount * self.SLASH_PENALTY_PERCENT

        self.log(f"SLASHING STAKE: Node {node_id} penalized {penalty} (1%)")

        # Update Node Intel
        self.add_listener_intel(
            node_id,
            {
                "stake_slashed": penalty,  # Accumulate
                "last_slash_at": datetime.now(timezone.utc).isoformat(),
                "notes": [f"Slashed {penalty} due to crash/failure"],
            },
        )

        return {"status": "slashed", "node_id": node_id, "penalty_amount": penalty}

    def _route_payment(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Determine the best way to route a user's payment.
        """
        user_preference = payload.get("preference", "crypto")

        path = self._select_payment_path(user_preference)

        return {"selected_path": path, "instructions": f"Use {path} provider"}

    def _select_payment_path(self, preference: str = "crypto") -> str:
        """
        Dynamic selection of payment provider based on latency/uptime.
        """
        # Logic: Check availability (simulated)
        # Priority: Onramp -> Web3 -> Stripe

        # Simulate checking endpoints...
        coinbase_onramp_ok = True

        if preference == "fiat":
            return "stripe"

        if coinbase_onramp_ok:
            return "coinbase_onramp"
        else:
            return "wallet_connect"

    def _get_nonce(self) -> int:
        return int(datetime.now().timestamp())


if __name__ == "__main__":
    bee = PayoutProcessorBee()
    print(bee.run())
