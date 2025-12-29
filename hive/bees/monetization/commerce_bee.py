from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import EmployedBee
from hive.utils.payment_processor import PaymentProcessor


class CommerceBee(EmployedBee):
    """
    Handles INCOMING payments (Commerce).
    Creates Payment Intents and processes Webhooks.
    """

    BEE_TYPE = "commerce"
    BEE_NAME = "Commerce Bee"
    CATEGORY = "monetization"

    def __init__(self, hive_path: str | None = None):
        super().__init__(hive_path)
        self.processor = PaymentProcessor()

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Process commerce tasks: 'create_intent' or 'handle_webhook'.
        """
        if not task:
            return {"status": "idle"}

        action = task.get("payload", {}).get("action")

        if action == "create_intent":
            return self._create_intent(task.get("payload", {}))
        elif action == "handle_webhook":
            return self._handle_webhook(task.get("payload", {}))

        return {"error": f"Unknown commerce action: {action}"}

    def _create_intent(self, payload: dict) -> dict:
        """Create a Stripe Payment Intent."""
        amount = float(payload.get("amount", 5.00))
        metadata = payload.get("metadata", {})

        # Call Utility
        result = self.processor.create_payment_intent(
            amount=amount, currency="usd", metadata=metadata
        )

        if "error" in result:
            self.log(f"Payment Creation Failed: {result['error']}", level="error")
            return result

        self.log(f"Created Payment Intent: {result['id']} for ${amount}")
        return result

    def _handle_webhook(self, payload: dict) -> dict:
        """
        Process a verified webhook event.
        Payload should contain 'event_data' (checked by API layer) or raw data to check signature.
        For internal Bee task, we assume API layer did sig check or we do it here if raw.
        """
        # In this Bee design, we assume the API route passed us the trusted Event object
        # or the Bee uses the Processor to verify.
        # Let's assume payload has 'raw_body' and 'sig_header' if verification needed

        raw_body = payload.get("raw_body")
        sig_header = payload.get("sig_header")

        if raw_body and sig_header:
            event = self.processor.verify_webhook(raw_body.encode("utf-8"), sig_header)
            if not event:
                return {"error": "Invalid Webhook Signature"}
        else:
            # Trusted internal simulation call
            event = payload.get("event", {})

        event_type = event.get("type")

        if event_type == "payment_intent.succeeded":
            data = event.get("data", {}).get("object", {})
            amount_received = data.get("amount_received", 0) / 100.0
            metadata = data.get("metadata", {})

            # 1. Update Treasury in Intel
            self._credit_treasury(amount_received, f"Stripe: {data.get('id')}")

            # 2. Alert the Hive (e.g., for DJ Request)
            if metadata.get("type") == "song_request":
                self.post_alert(
                    f"PAYMENT RECEIVED: ${amount_received} for {metadata.get('song')}",
                    priority=True,
                )
                # We could also spawn a DJ task here directly

            return {"status": "processed", "amount": amount_received}

        return {"status": "ignored", "type": event_type}

    def _credit_treasury(self, amount: float, source: str):
        """Add funds to global treasury."""
        intel = self.read_intel()
        if "treasury" not in intel:
            intel["treasury"] = {"balance": 0.0, "history": []}

        intel["treasury"]["balance"] += amount
        intel["treasury"]["history"].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "amount": amount,
                "type": "CREDIT",
                "source": source,
            }
        )
        self._write_json("intel.json", intel)


if __name__ == "__main__":
    bee = CommerceBee()
    # Test Intent
    print(
        bee.work(
            {
                "payload": {
                    "action": "create_intent",
                    "amount": 10.00,
                    "metadata": {"song": "Test Track"},
                }
            }
        )
    )
