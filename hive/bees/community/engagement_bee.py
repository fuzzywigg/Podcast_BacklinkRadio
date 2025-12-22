"""
Community Engagement Bee - Manages listener community.

Responsibilities:
- Process incoming messages and mentions
- Track superfans and VIPs
- Coordinate giveaways and contests
- Build community connections
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee


class EngagementBee(EmployedBee):
    """
    Manages community engagement and listener relationships.

    Processes incoming interactions and builds lasting
    connections with the listener community.
    """

    BEE_TYPE = "engagement"
    BEE_NAME = "Community Engagement Bee"
    CATEGORY = "community"

    # Engagement triggers and responses
    TRIGGER_TYPES = {
        "mention": {"priority": 5, "response_time": "1h"},
        "donation": {"priority": 9, "response_time": "immediate"},
        "request": {"priority": 7, "response_time": "30m"},
        "feedback": {"priority": 4, "response_time": "4h"},
        "question": {"priority": 6, "response_time": "2h"}
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process community engagement tasks.

        Task payload can include:
        - action: process_mention|process_donation|run_giveaway|vip_check
        - interaction: the interaction data to process
        """
        self.log("Processing community engagement...")

        if not task:
            return self._check_pending_interactions()

        action = task.get("payload", {}).get("action", "process_mention")

        if action == "process_mention":
            return self._process_mention(task)
        elif action == "process_donation":
            return self._process_donation(task)
        elif action == "run_giveaway":
            return self._run_giveaway(task)
        elif action == "vip_check":
            return self._vip_status_check(task)
        elif action == "thank_listener":
            return self._thank_listener(task)

        return {"error": "Unknown action"}

    def _check_pending_interactions(self) -> Dict[str, Any]:
        """Check for pending interactions needing response."""

        state = self.read_state()
        pending_shoutouts = state.get("economy", {}).get("pending_shoutouts", [])

        # Check for any alerts
        alerts = state.get("alerts", {})
        priority_alerts = alerts.get("priority", [])

        # Process donation alerts first
        donations_processed = 0
        for alert in priority_alerts:
            if "donation" in alert.get("message", "").lower():
                self._process_donation({"payload": {"alert": alert}})
                donations_processed += 1

        return {
            "action": "check_pending",
            "pending_shoutouts": len(pending_shoutouts),
            "priority_alerts": len(priority_alerts),
            "donations_processed": donations_processed
        }

    def _process_mention(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming mention."""

        payload = task.get("payload", {})
        mention = payload.get("interaction", {})

        sender = mention.get("from", "unknown")
        content = mention.get("content", "")
        platform = mention.get("platform", "twitter")

        self.log(f"Processing mention from {sender}: {content[:50]}...")

        # Classify the mention
        mention_type = self._classify_mention(content)

        # Update listener intel
        self.add_listener_intel(sender, {
            "handle": sender,
            "interaction_count": 1,  # Will be incremented
            "notes": [f"Mentioned us: {content[:100]}"]
        })

        # Determine response
        response = self._generate_engagement_response(mention_type, sender, content)

        # Queue for DJ shoutout if warranted
        if mention_type in ["request", "donation"]:
            self._queue_shoutout(sender, content, mention_type)

        return {
            "action": "process_mention",
            "sender": sender,
            "type": mention_type,
            "response": response
        }

    def _process_donation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming donation."""

        payload = task.get("payload", {})
        donation = payload.get("interaction", {})

        donor = donation.get("from", "anonymous")
        amount = donation.get("amount", 0)
        message = donation.get("message", "")

        self.log(f"Processing donation from {donor}: ${amount}")

        # Update listener intel
        self.add_listener_intel(donor, {
            "handle": donor,
            "donation_total": amount,  # Will accumulate
            "notes": [f"Donated ${amount}: {message}"],
            "tags": ["donor"]
        })

        # Queue immediate shoutout
        self._queue_shoutout(donor, message, "donation", priority=True)

        # Post alert for DJ
        self.post_alert(
            f"Donation from {donor}: ${amount} - '{message}'",
            priority=True
        )

        # Update economy state
        state = self.read_state()
        today_total = state.get("economy", {}).get("total_donations_today", 0)
        self.write_state({
            "economy": {
                "total_donations_today": today_total + amount
            }
        })

        return {
            "action": "process_donation",
            "donor": donor,
            "amount": amount,
            "shoutout_queued": True
        }

    def _run_giveaway(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run a giveaway or contest."""

        payload = task.get("payload", {})
        giveaway_type = payload.get("type", "random")
        prize = payload.get("prize", "mystery prize")

        self.log(f"Running giveaway: {prize}")

        # Get eligible participants
        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        eligible = []
        for node_id, data in known_nodes.items():
            # Filter based on giveaway rules
            if data.get("interaction_count", 0) > 0:
                eligible.append(node_id)

        # Select winner
        winner = None
        if eligible:
            import random
            winner = random.choice(eligible)

        if winner:
            # Queue winner announcement
            self._queue_shoutout(
                winner,
                f"Congratulations! You've won: {prize}",
                "giveaway_winner",
                priority=True
            )

            # Update winner intel
            self.add_listener_intel(winner, {
                "notes": [f"Won giveaway: {prize}"],
                "tags": ["winner"]
            })

        return {
            "action": "run_giveaway",
            "prize": prize,
            "eligible_count": len(eligible),
            "winner": winner
        }

    def _vip_status_check(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check and update VIP statuses."""

        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        vips = []
        new_vips = []

        for node_id, data in known_nodes.items():
            is_vip = data.get("is_vip", False)
            engagement_score = data.get("engagement_score", 0)

            # VIP threshold
            if engagement_score >= 0.7:
                vips.append(node_id)
                if not is_vip:
                    new_vips.append(node_id)
                    self.add_listener_intel(node_id, {
                        "is_vip": True,
                        "vip_since": datetime.now(timezone.utc).isoformat(),
                        "notes": ["Promoted to VIP status"]
                    })

        if new_vips:
            self.log(f"New VIPs: {new_vips}")

        return {
            "action": "vip_check",
            "total_vips": len(vips),
            "new_vips": new_vips
        }

    def _thank_listener(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send a thank you to a listener."""

        payload = task.get("payload", {})
        listener = payload.get("listener")
        reason = payload.get("reason", "being awesome")

        # Queue shoutout
        self._queue_shoutout(listener, f"Thanks for {reason}", "thank_you")

        return {
            "action": "thank_listener",
            "listener": listener,
            "reason": reason
        }

    def _classify_mention(self, content: str) -> str:
        """Classify the type of mention."""

        content_lower = content.lower()

        if any(word in content_lower for word in ["play", "request", "can you play"]):
            return "request"
        elif any(word in content_lower for word in ["love", "awesome", "great", "amazing"]):
            return "praise"
        elif any(word in content_lower for word in ["?", "how", "what", "when", "why"]):
            return "question"
        elif any(word in content_lower for word in ["bad", "hate", "sucks", "terrible"]):
            return "criticism"
        else:
            return "mention"

    def _generate_engagement_response(
        self,
        mention_type: str,
        sender: str,
        content: str
    ) -> Optional[str]:
        """Generate an appropriate response."""

        responses = {
            "request": f"Request received from {sender}. Adding to the queue.",
            "praise": f"We see you, {sender}. Thanks for tuning in.",
            "question": f"Good question from {sender}. Let us look into that.",
            "criticism": None,  # Don't engage with negativity
            "mention": f"Signal received from {sender}."
        }

        return responses.get(mention_type)

    def _queue_shoutout(
        self,
        node: str,
        message: str,
        shoutout_type: str,
        priority: bool = False
    ) -> None:
        """Queue a shoutout for on-air mention."""

        state = self.read_state()
        pending = state.get("economy", {}).get("pending_shoutouts", [])

        shoutout = {
            "node": node,
            "message": message,
            "type": shoutout_type,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "priority": priority
        }

        if priority:
            pending.insert(0, shoutout)
        else:
            pending.append(shoutout)

        self.write_state({
            "economy": {
                "pending_shoutouts": pending
            }
        })


if __name__ == "__main__":
    bee = EngagementBee()
    result = bee.run()
    print(result)
