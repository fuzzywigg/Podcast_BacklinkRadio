
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

try:
    import stripe
except ImportError:
    stripe = None

class PaymentProcessor:
    """
    Handles payments via Stripe (or Simulation).
    """

    def __init__(self):
        self.logger = logging.getLogger("PaymentProcessor")
        self.stripe_key = os.environ.get("STRIPE_SECRET_KEY")
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        self.mode = "LIVE" if self.stripe_key else "SIMULATION"

        if self.mode == "LIVE" and stripe:
            stripe.api_key = self.stripe_key
            self.logger.info("Stripe initialized in LIVE mode.")
        else:
            self.logger.warning("Stripe not configured. Running in SIMULATION mode.")

    def create_payment_intent(self, amount: float, currency: str = "usd", metadata: Dict = None) -> Dict[str, Any]:
        """
        Create a payment intent for a tip/request.
        
        Args:
            amount: Float amount in dollars (e.g. 5.00)
            currency: 'usd'
            metadata: Dict of extra info (song, request_id)
        """
        amount_cents = int(amount * 100)
        
        if self.mode == "SIMULATION":
            return {
                "id": f"pi_sim_{datetime.now().timestamp()}",
                "client_secret": "sim_secret_123",
                "status": "requires_payment_method",
                "amount": amount_cents,
                "metadata": metadata or {}
            }

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True},
            )
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status
            }
        except Exception as e:
            self.logger.error(f"Stripe Create Error: {e}")
            return {"error": str(e)}

    def verify_webhook(self, payload: bytes, sig_header: str) -> Optional[Dict]:
        """
        Verify incoming Stripe webhook signature.
        """
        if self.mode == "SIMULATION":
            # Just return parsed JSON for simulation check
            import json
            return json.loads(payload)

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError:
            return None
        except stripe.error.SignatureVerificationError:
            return None
