"""
Donation Processor Bee - Handles incoming donations and payments.

CRITICAL PRIORITY BEE - Immediate response required.

Responsibilities:
- Process incoming donation events
- Verify payment authenticity
- Trigger thank-you workflows
- Update treasury and economy state
- Queue shoutouts for donors
- Track donation metrics
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import sys
import json
import hashlib

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_bee import EmployedBee
from utils.safety import validate_interaction, sanitize_payment_message, AUTHORITIES
from utils.economy import calculate_dao_rewards, validate_wallet_request


class DonationProcessorBee(EmployedBee):
    """
    Processes donations and payments in real-time.
    
    CRITICAL: This bee handles money. All inputs are untrusted
    and must be validated against known treasury wallets.
    """

    BEE_TYPE = "donation_processor"
    BEE_NAME = "Donation Processor Bee"
    CATEGORY = "monetization"

    # Donation tiers for recognition
    DONATION_TIERS = {
        "mega": {"min": 100, "color": "gold", "shoutout": "mega"},
        "super": {"min": 25, "color": "purple", "shoutout": "special"},
        "supporter": {"min": 5, "color": "blue", "shoutout": "standard"},
        "tip": {"min": 0.01, "color": "green", "shoutout": "quick"}
    }

    # Supported payment methods
    SUPPORTED_METHODS = ["stripe", "paypal", "crypto", "manual"]

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process donation-related tasks.

        Task payload actions:
        - process_donation: Handle incoming donation
        - verify_payment: Verify a pending payment
        - generate_receipt: Create donation receipt
        - refund_request: Handle refund (admin only)
        - daily_summary: Generate donation summary
        """
        self.log("Donation processor activated...")

        if not task:
            return self._check_pending_donations()

        action = task.get("payload", {}).get("action", "process_donation")

        if action == "process_donation":
            return self._process_donation(task)
        elif action == "verify_payment":
            return self._verify_payment(task)
        elif action == "generate_receipt":
            return self._generate_receipt(task)
        elif action == "refund_request":
            return self._handle_refund_request(task)
        elif action == "daily_summary":
            return self._generate_daily_summary()

        return {"error": f"Unknown action: {action}"}

    def _check_pending_donations(self) -> Dict[str, Any]:
        """Check for any pending donations needing processing."""
        
        state = self.read_state()
        alerts = state.get("alerts", {}).get("priority", [])
        
        pending_count = 0
        processed = []
        
        for alert in alerts:
            msg = alert.get("message", "").lower()
            if "donation" in msg or "payment" in msg:
                # Attempt to extract donation data from alert
                self.log(f"Found pending donation alert: {alert.get('id')}")
                pending_count += 1
        
        return {
            "action": "check_pending",
            "pending_donations": pending_count,
            "processed": processed
        }

    def _process_donation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming donation.
        
        SECURITY: All donation data is untrusted. We verify:
        1. Payment method is supported
        2. Amount is positive
        3. Wallet addresses match treasury
        4. Message is sanitized
        """
        payload = task.get("payload", {})
        donation = payload.get("donation", {})

        donor_handle = donation.get("from", "anonymous")
        amount = float(donation.get("amount", 0))
        currency = donation.get("currency", "USD")
        method = donation.get("method", "unknown")
        message = donation.get("message", "")
        tx_id = donation.get("transaction_id", "")

        self.log(f"Processing donation: ${amount} from {donor_handle} via {method}")

        # VALIDATION 1: Amount check
        if amount <= 0:
            self.log(f"Invalid donation amount: {amount}", level="warning")
            return {"success": False, "error": "Invalid amount"}

        # VALIDATION 2: Method check
        if method not in self.SUPPORTED_METHODS:
            self.log(f"Unsupported payment method: {method}", level="warning")
            return {"success": False, "error": f"Unsupported method: {method}"}

        # VALIDATION 3: Crypto wallet validation (if applicable)
        if method == "crypto":
            wallet = donation.get("wallet_address")
            if wallet:
                treasury = self.read_treasury()
                is_valid, reason = validate_wallet_request(donor_handle, wallet, treasury)
                if not is_valid:
                    self.log(f"FRAUD ALERT: {reason}", level="critical")
                    self._log_fraud_attempt(donor_handle, donation)
                    return {"success": False, "error": "Invalid wallet", "fraud_flagged": True}

        # SANITIZATION: Clean the message
        safe_message = sanitize_payment_message(message)
        _, checked_message, meta = validate_interaction(donor_handle, safe_message, "donation")

        if meta.get("risk_level") == "high":
            checked_message = "Thanks for the support! 🎵"
            self.log(f"Message sanitized for safety from {donor_handle}", level="warning")

        # DETERMINE TIER
        tier = self._get_donation_tier(amount)

        # CALCULATE REWARDS
        rewards = calculate_dao_rewards(donor_handle, "dollar", amount, currency)

        # UPDATE LISTENER INTEL
        self.add_listener_intel(donor_handle, {
            "handle": donor_handle,
            "donation_total": amount,
            "dao_credits": rewards.get("amount", 0),
            "last_donation": datetime.now(timezone.utc).isoformat(),
            "donation_tier": tier["name"],
            "notes": [f"Donated ${amount}: {checked_message[:100]}"],
            "tags": ["donor", f"tier_{tier['name']}"]
        })

        # QUEUE SHOUTOUT
        self._queue_donation_shoutout(donor_handle, amount, tier, checked_message)

        # POST ALERT FOR DJ
        self.post_alert(
            f"💰 {tier['emoji']} {donor_handle} donated ${amount:.2f}! Message: \"{checked_message}\"",
            priority=True
        )

        # UPDATE ECONOMY STATE
        self._update_economy_state(amount, currency, tier["name"])

        # WRITE TO DONATION LOG (append-only for audit)
        self._log_donation(donor_handle, amount, currency, method, tx_id, tier["name"])

        return {
            "success": True,
            "action": "process_donation",
            "donor": donor_handle,
            "amount": amount,
            "currency": currency,
            "tier": tier["name"],
            "rewards": rewards,
            "shoutout_queued": True
        }

    def _verify_payment(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a payment transaction.
        
        In production, this would call payment provider APIs.
        For now, we implement the interface.
        """
        payload = task.get("payload", {})
        tx_id = payload.get("transaction_id")
        method = payload.get("method", "unknown")

        self.log(f"Verifying payment: {tx_id} via {method}")

        # Stub: In production, call Stripe/PayPal/blockchain APIs
        verification = {
            "transaction_id": tx_id,
            "method": method,
            "status": "pending_verification",
            "note": "Payment verification requires API integration"
        }

        return {
            "action": "verify_payment",
            "verification": verification
        }

    def _generate_receipt(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a donation receipt."""
        payload = task.get("payload", {})
        donor = payload.get("donor")
        amount = payload.get("amount")
        tx_id = payload.get("transaction_id", f"BL-{datetime.now().strftime('%Y%m%d%H%M%S')}")

        receipt = {
            "receipt_id": f"REC-{hashlib.sha256(tx_id.encode()).hexdigest()[:12].upper()}",
            "donor": donor,
            "amount": amount,
            "date": datetime.now(timezone.utc).isoformat(),
            "transaction_id": tx_id,
            "station": "Backlink Broadcast",
            "message": "Thank you for supporting independent radio!"
        }

        return {
            "action": "generate_receipt",
            "receipt": receipt
        }

    def _handle_refund_request(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle refund request - ADMIN ONLY.
        
        Only authorities can process refunds.
        """
        payload = task.get("payload", {})
        requester = payload.get("requester", "").lower().replace("@", "")

        if requester not in AUTHORITIES:
            self.log(f"Unauthorized refund request from {requester}", level="warning")
            return {
                "success": False,
                "error": "Refund requests require admin authorization"
            }

        # Process refund (stub)
        return {
            "action": "refund_request",
            "status": "pending_review",
            "note": "Refund requires manual processing"
        }

    def _generate_daily_summary(self) -> Dict[str, Any]:
        """Generate daily donation summary."""
        state = self.read_state()
        economy = state.get("economy", {})

        summary = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "total_donations_today": economy.get("total_donations_today", 0),
            "donation_count_today": economy.get("donation_count_today", 0),
            "top_donor_today": economy.get("top_donor_today"),
            "tier_breakdown": economy.get("tier_breakdown_today", {})
        }

        return {
            "action": "daily_summary",
            "summary": summary
        }

    def _get_donation_tier(self, amount: float) -> Dict[str, Any]:
        """Determine donation tier based on amount."""
        if amount >= 100:
            return {"name": "mega", "emoji": "🏆", "color": "gold", "shoutout": "mega"}
        elif amount >= 25:
            return {"name": "super", "emoji": "⭐", "color": "purple", "shoutout": "special"}
        elif amount >= 5:
            return {"name": "supporter", "emoji": "💙", "color": "blue", "shoutout": "standard"}
        else:
            return {"name": "tip", "emoji": "🎵", "color": "green", "shoutout": "quick"}

    def _queue_donation_shoutout(
        self,
        donor: str,
        amount: float,
        tier: Dict[str, Any],
        message: str
    ) -> None:
        """Queue a shoutout for the donor."""
        state = self.read_state()
        pending = state.get("economy", {}).get("pending_shoutouts", [])

        shoutout = {
            "node": donor,
            "type": "donation",
            "tier": tier["name"],
            "amount": amount,
            "message": message,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "priority": True,
            "template": self._get_shoutout_template(tier["name"])
        }

        # Priority shoutouts go to the front
        pending.insert(0, shoutout)

        self.write_state({
            "economy": {
                "pending_shoutouts": pending
            }
        })

    def _get_shoutout_template(self, tier: str) -> str:
        """Get shoutout template based on tier."""
        templates = {
            "mega": "MASSIVE love to {donor}! They just dropped ${amount} on the station! {message}",
            "super": "Big shoutout to {donor} for the ${amount} donation! {message}",
            "supporter": "Thanks to {donor} for supporting with ${amount}! {message}",
            "tip": "Quick thanks to {donor} for the tip! {message}"
        }
        return templates.get(tier, templates["tip"])

    def _update_economy_state(self, amount: float, currency: str, tier: str) -> None:
        """Update the economy state with donation data."""
        state = self.read_state()
        economy = state.get("economy", {})

        # Update totals
        economy["total_donations_today"] = economy.get("total_donations_today", 0) + amount
        economy["donation_count_today"] = economy.get("donation_count_today", 0) + 1
        economy["last_donation_at"] = datetime.now(timezone.utc).isoformat()

        # Update tier breakdown
        tier_breakdown = economy.get("tier_breakdown_today", {})
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
        economy["tier_breakdown_today"] = tier_breakdown

        self.write_state({"economy": economy})

    def _log_donation(
        self,
        donor: str,
        amount: float,
        currency: str,
        method: str,
        tx_id: str,
        tier: str
    ) -> None:
        """Log donation to append-only event log."""
        log_path = self.hive_path / "treasury_events.jsonl"

        event = {
            "type": "DONATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "donor": donor,
            "amount": amount,
            "currency": currency,
            "method": method,
            "transaction_id": tx_id,
            "tier": tier,
            "bee_id": self.bee_id
        }

        with open(log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def _log_fraud_attempt(self, handle: str, donation_data: Dict[str, Any]) -> None:
        """Log a potential fraud attempt."""
        log_path = self.hive_path / "security_events.jsonl"

        event = {
            "type": "FRAUD_ATTEMPT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "handle": handle,
            "data": donation_data,
            "bee_id": self.bee_id
        }

        with open(log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Also post critical alert
        self.post_alert(
            f"⚠️ FRAUD ATTEMPT: {handle} attempted unauthorized wallet routing",
            priority=True
        )


if __name__ == "__main__":
    bee = DonationProcessorBee()
    result = bee.run()
    print(result)
