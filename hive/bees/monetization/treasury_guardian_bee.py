"""
Treasury Guardian Bee
P0 Requirement: Financial Governance.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json
from hive.bees.base_bee import BaseBee

class TreasuryGuardianBee(BaseBee):
    """
    Enforces treasury spending limits and monitors budget health.
    """
    BEE_TYPE = "treasury_guardian"
    CATEGORY = "monetization"

    MAX_SINGLE_TRANSACTION = 100.00  # USD
    MIN_RESERVE_BALANCE = 20.00      # Emergency reserve

    def work(self, task: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Guard treasury integrity.
        """
        # Load event log (source of truth)
        events = self._load_treasury_events()

        # Compute current balance
        balance = self._compute_balance_from_events(events)

        # Check for pending transactions
        pending_tx = task.get("payload", {}).get("transaction") if task else None

        validation = None
        if pending_tx:
            # Validate transaction
            validation = self.validate_transaction(pending_tx, balance)

            if not validation["approved"]:
                self.log(f"🛑 TRANSACTION VETOED: {validation['reason']}", level="warning")

        # Check budget health
        health = self.assess_budget_health(balance, events)

        if health["status"] == "critical":
            self.post_alert(f"Treasury Critical: {health['runway_days']:.1f} days runway remaining", priority=True)

        return {
            "current_balance": balance,
            "budget_health": health,
            "transaction_validation": validation
        }

    def _load_treasury_events(self) -> List[Dict]:
        """Load treasury event log."""
        log_path = self.honeycomb_path / "treasury_events.jsonl"
        events = []
        if log_path.exists():
            with open(log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            # Handling potentially empty list if init wrong, but standard JSONL is one dict per line
                            val = json.loads(line)
                            if isinstance(val, list):
                                events.extend(val) # Handle the init case where I wrote []
                            else:
                                events.append(val)
                        except json.JSONDecodeError:
                            pass
        return events

    def _compute_balance_from_events(self, events: List[Dict]) -> float:
        """Compute balance by replaying events."""
        balance = 0.0
        for event in events:
            # Assuming event structure: {"type": "CREDIT"|"DEBIT", "amount": float}
            amount = float(event.get("amount", 0))
            if event.get("type") == "CREDIT":
                balance += amount
            elif event.get("type") == "DEBIT":
                balance -= amount
        return balance

    def validate_transaction(self, tx: Dict, current_balance: float) -> Dict:
        """Pre-flight checks for transactions."""
        amount = float(tx.get("amount", 0))
        reason = tx.get("reason", "unknown")

        # Rule #1: Amount must be positive (for debit checks)
        if amount <= 0:
            return {"approved": False, "reason": "negative_or_zero_amount"}

        # Rule #2: Single transaction limit
        if amount > self.MAX_SINGLE_TRANSACTION:
            return {"approved": False, "reason": f"exceeds_max_{self.MAX_SINGLE_TRANSACTION}"}

        # Rule #3: Maintain minimum reserve
        if (current_balance - amount) < self.MIN_RESERVE_BALANCE:
            return {"approved": False, "reason": "would_deplete_reserve"}

        # Rule #4: Valid reason
        valid_reasons = ["song_purchase", "artist_payment", "dividend", "operational", "refund"]
        if reason not in valid_reasons:
            return {"approved": False, "reason": "invalid_reason"}

        return {"approved": True}

    def assess_budget_health(self, balance: float, events: List[Dict]) -> Dict:
        """Evaluate treasury sustainability."""
        # Calculate burn rate (spending per day)
        # Simplified: average of last 7 days debits

        # Filter for debits
        debits = [e for e in events if e.get("type") == "DEBIT"]
        # In a real impl, we'd filter by date. For now, assume all events are relevant or simple heuristic
        total_spent = sum(e.get("amount", 0) for e in debits)

        # Rough estimation if we don't have dates, default to a safe burn rate or 0
        burn_rate = 1.0 # Default dummy value to avoid div by zero if no history
        if debits:
            burn_rate = total_spent / 7.0 # average over "a week" concept

        runway_days = balance / burn_rate if burn_rate > 0 else float('inf')

        if runway_days < 3:
            status = "critical"
        elif runway_days < 7:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "balance": balance,
            "burn_rate_per_day": burn_rate,
            "runway_days": runway_days
        }
