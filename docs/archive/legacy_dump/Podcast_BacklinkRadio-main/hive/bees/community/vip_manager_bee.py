"""
VIP Manager Bee - Identifies and nurtures superfans.

HIGH PRIORITY BEE - Community relationship building.

Responsibilities:
- Identify VIP-worthy listeners based on engagement metrics
- Track VIP status and privileges
- Trigger special treatment workflows
- Manage VIP tiers and rewards
- Generate VIP reports
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_bee import OnlookerBee
from utils.economy import calculate_dao_rewards


class VIPManagerBee(OnlookerBee):
    """
    Manages VIP listener relationships and status.
    
    VIPs are superfans who consistently engage with the station.
    They get special treatment, early access, and recognition.
    """

    BEE_TYPE = "vip_manager"
    BEE_NAME = "VIP Manager Bee"
    CATEGORY = "community"

    # VIP tier thresholds (engagement_score based)
    VIP_TIERS = {
        "platinum": {
            "min_score": 0.9,
            "min_donations": 100,
            "min_interactions": 50,
            "perks": ["name_on_air", "early_access", "exclusive_content", "direct_line"]
        },
        "gold": {
            "min_score": 0.7,
            "min_donations": 25,
            "min_interactions": 20,
            "perks": ["name_on_air", "early_access", "exclusive_content"]
        },
        "silver": {
            "min_score": 0.5,
            "min_donations": 5,
            "min_interactions": 10,
            "perks": ["name_on_air", "exclusive_content"]
        },
        "bronze": {
            "min_score": 0.3,
            "min_donations": 0,
            "min_interactions": 5,
            "perks": ["name_on_air"]
        }
    }

    # Weights for engagement score calculation
    ENGAGEMENT_WEIGHTS = {
        "donation_total": 0.4,      # 40% weight
        "interaction_count": 0.3,   # 30% weight
        "listen_time_hours": 0.2,   # 20% weight
        "referrals": 0.1            # 10% weight
    }

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process VIP management tasks.

        Task payload actions:
        - scan_for_vips: Check all listeners for VIP eligibility
        - promote_vip: Manually promote a listener
        - demote_vip: Remove VIP status
        - generate_report: Create VIP status report
        - send_perks: Trigger perk delivery
        """
        self.log("VIP Manager activated...")

        if not task:
            return self._daily_vip_scan()

        action = task.get("payload", {}).get("action", "scan_for_vips")

        if action == "scan_for_vips":
            return self._daily_vip_scan()
        elif action == "promote_vip":
            return self._promote_vip(task)
        elif action == "demote_vip":
            return self._demote_vip(task)
        elif action == "generate_report":
            return self._generate_vip_report()
        elif action == "send_perks":
            return self._send_perks(task)
        elif action == "check_listener":
            return self._check_single_listener(task)

        return {"error": f"Unknown action: {action}"}

    def _daily_vip_scan(self) -> Dict[str, Any]:
        """
        Scan all known listeners and update VIP statuses.
        
        This is the main daily job for the VIP Manager.
        """
        self.log("Running daily VIP scan...")

        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        stats = {
            "scanned": 0,
            "new_vips": [],
            "promotions": [],
            "demotions": [],
            "tier_counts": {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0}
        }

        for node_id, data in known_nodes.items():
            stats["scanned"] += 1

            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(data)
            current_tier = data.get("vip_tier")
            current_vip = data.get("is_vip", False)

            # Determine new tier
            new_tier = self._determine_tier(engagement_score, data)

            # Update if changed
            if new_tier != current_tier:
                if new_tier and not current_vip:
                    # New VIP
                    stats["new_vips"].append({
                        "node": node_id,
                        "tier": new_tier,
                        "score": engagement_score
                    })
                    self._promote_to_vip(node_id, new_tier, engagement_score)
                elif new_tier and current_vip and self._is_promotion(current_tier, new_tier):
                    # Tier promotion
                    stats["promotions"].append({
                        "node": node_id,
                        "from": current_tier,
                        "to": new_tier
                    })
                    self._update_vip_tier(node_id, new_tier, engagement_score)
                elif current_vip and (not new_tier or self._is_demotion(current_tier, new_tier)):
                    # Demotion
                    if new_tier:
                        stats["demotions"].append({
                            "node": node_id,
                            "from": current_tier,
                            "to": new_tier
                        })
                        self._update_vip_tier(node_id, new_tier, engagement_score)
                    else:
                        stats["demotions"].append({
                            "node": node_id,
                            "from": current_tier,
                            "to": None
                        })
                        self._remove_vip_status(node_id)

            # Count tiers
            if new_tier:
                stats["tier_counts"][new_tier] = stats["tier_counts"].get(new_tier, 0) + 1

        # Log significant changes
        if stats["new_vips"]:
            self.log(f"New VIPs found: {len(stats['new_vips'])}")
            for vip in stats["new_vips"]:
                self.post_alert(
                    f"🌟 New {vip['tier'].upper()} VIP: {vip['node']}!",
                    priority=True
                )

        return {
            "action": "scan_for_vips",
            "stats": stats
        }

    def _calculate_engagement_score(self, listener_data: Dict[str, Any]) -> float:
        """
        Calculate engagement score for a listener.
        
        Score is 0.0 to 1.0 based on weighted metrics.
        """
        # Extract metrics with defaults
        donation_total = float(listener_data.get("donation_total", 0))
        interaction_count = int(listener_data.get("interaction_count", 0))
        listen_hours = float(listener_data.get("listen_time_hours", 0))
        referrals = int(listener_data.get("referral_count", 0))

        # Normalize each metric (assumes max thresholds)
        donation_norm = min(donation_total / 500, 1.0)  # $500 = max score
        interaction_norm = min(interaction_count / 100, 1.0)  # 100 = max
        listen_norm = min(listen_hours / 100, 1.0)  # 100 hours = max
        referral_norm = min(referrals / 10, 1.0)  # 10 referrals = max

        # Calculate weighted score
        score = (
            donation_norm * self.ENGAGEMENT_WEIGHTS["donation_total"] +
            interaction_norm * self.ENGAGEMENT_WEIGHTS["interaction_count"] +
            listen_norm * self.ENGAGEMENT_WEIGHTS["listen_time_hours"] +
            referral_norm * self.ENGAGEMENT_WEIGHTS["referrals"]
        )

        return round(score, 3)

    def _determine_tier(self, score: float, data: Dict[str, Any]) -> Optional[str]:
        """Determine VIP tier based on score and other criteria."""
        donation_total = float(data.get("donation_total", 0))
        interaction_count = int(data.get("interaction_count", 0))

        # Check tiers from highest to lowest
        for tier_name in ["platinum", "gold", "silver", "bronze"]:
            tier = self.VIP_TIERS[tier_name]
            if (score >= tier["min_score"] and
                donation_total >= tier["min_donations"] and
                interaction_count >= tier["min_interactions"]):
                return tier_name

        return None

    def _is_promotion(self, current: Optional[str], new: str) -> bool:
        """Check if tier change is a promotion."""
        tier_order = ["bronze", "silver", "gold", "platinum"]
        if not current:
            return True
        return tier_order.index(new) > tier_order.index(current)

    def _is_demotion(self, current: Optional[str], new: Optional[str]) -> bool:
        """Check if tier change is a demotion."""
        if not new:
            return True
        if not current:
            return False
        tier_order = ["bronze", "silver", "gold", "platinum"]
        return tier_order.index(new) < tier_order.index(current)

    def _promote_to_vip(self, node_id: str, tier: str, score: float) -> None:
        """Promote a listener to VIP status."""
        self.add_listener_intel(node_id, {
            "is_vip": True,
            "vip_tier": tier,
            "vip_since": datetime.now(timezone.utc).isoformat(),
            "engagement_score": score,
            "perks": self.VIP_TIERS[tier]["perks"],
            "notes": [f"Promoted to {tier.upper()} VIP status"]
        })

        # Queue celebration shoutout
        self._queue_vip_announcement(node_id, tier, "new")

    def _update_vip_tier(self, node_id: str, tier: str, score: float) -> None:
        """Update VIP tier."""
        self.add_listener_intel(node_id, {
            "vip_tier": tier,
            "engagement_score": score,
            "perks": self.VIP_TIERS[tier]["perks"],
            "tier_updated_at": datetime.now(timezone.utc).isoformat(),
            "notes": [f"Tier changed to {tier.upper()}"]
        })

    def _remove_vip_status(self, node_id: str) -> None:
        """Remove VIP status from a listener."""
        self.add_listener_intel(node_id, {
            "is_vip": False,
            "vip_tier": None,
            "perks": [],
            "vip_ended_at": datetime.now(timezone.utc).isoformat(),
            "notes": ["VIP status removed due to inactivity"]
        })

    def _promote_vip(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manually promote a listener to VIP."""
        payload = task.get("payload", {})
        node_id = payload.get("node_id")
        tier = payload.get("tier", "bronze")
        reason = payload.get("reason", "Manual promotion")

        if not node_id:
            return {"error": "node_id required"}

        if tier not in self.VIP_TIERS:
            return {"error": f"Invalid tier: {tier}"}

        self.add_listener_intel(node_id, {
            "is_vip": True,
            "vip_tier": tier,
            "vip_since": datetime.now(timezone.utc).isoformat(),
            "perks": self.VIP_TIERS[tier]["perks"],
            "notes": [f"Manual promotion: {reason}"]
        })

        self._queue_vip_announcement(node_id, tier, "new")

        return {
            "action": "promote_vip",
            "node_id": node_id,
            "tier": tier,
            "success": True
        }

    def _demote_vip(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manually demote or remove VIP status."""
        payload = task.get("payload", {})
        node_id = payload.get("node_id")
        reason = payload.get("reason", "Manual demotion")

        if not node_id:
            return {"error": "node_id required"}

        self._remove_vip_status(node_id)

        return {
            "action": "demote_vip",
            "node_id": node_id,
            "reason": reason,
            "success": True
        }

    def _generate_vip_report(self) -> Dict[str, Any]:
        """Generate a comprehensive VIP status report."""
        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        vips_by_tier = {"platinum": [], "gold": [], "silver": [], "bronze": []}
        total_vip_donations = 0

        for node_id, data in known_nodes.items():
            if data.get("is_vip"):
                tier = data.get("vip_tier", "bronze")
                vips_by_tier[tier].append({
                    "node": node_id,
                    "since": data.get("vip_since"),
                    "score": data.get("engagement_score", 0),
                    "donations": data.get("donation_total", 0)
                })
                total_vip_donations += float(data.get("donation_total", 0))

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_vips": sum(len(v) for v in vips_by_tier.values()),
            "by_tier": {
                tier: {"count": len(vips), "members": vips}
                for tier, vips in vips_by_tier.items()
            },
            "total_vip_donations": total_vip_donations,
            "top_vips": self._get_top_vips(known_nodes, 5)
        }

        return {
            "action": "generate_report",
            "report": report
        }

    def _get_top_vips(self, known_nodes: Dict, limit: int = 5) -> List[Dict]:
        """Get top VIPs by engagement score."""
        vips = [
            {"node": nid, **data}
            for nid, data in known_nodes.items()
            if data.get("is_vip")
        ]
        vips.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)
        return vips[:limit]

    def _send_perks(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger perk delivery for VIPs."""
        payload = task.get("payload", {})
        perk_type = payload.get("perk_type")
        target_tier = payload.get("tier")  # Optional: target specific tier

        intel = self.read_intel()
        known_nodes = intel.get("listeners", {}).get("known_nodes", {})

        recipients = []
        for node_id, data in known_nodes.items():
            if not data.get("is_vip"):
                continue

            tier = data.get("vip_tier")
            perks = data.get("perks", [])

            # Check if they should receive this perk
            if target_tier and tier != target_tier:
                continue

            if perk_type and perk_type not in perks:
                continue

            recipients.append({
                "node": node_id,
                "tier": tier,
                "perk": perk_type
            })

        # In production, this would trigger actual perk delivery
        # (emails, exclusive content access, etc.)

        return {
            "action": "send_perks",
            "perk_type": perk_type,
            "recipients_count": len(recipients),
            "recipients": recipients
        }

    def _check_single_listener(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Check VIP eligibility for a single listener."""
        payload = task.get("payload", {})
        node_id = payload.get("node_id")

        if not node_id:
            return {"error": "node_id required"}

        intel = self.read_intel()
        listener = intel.get("listeners", {}).get("known_nodes", {}).get(node_id)

        if not listener:
            return {"error": f"Listener not found: {node_id}"}

        score = self._calculate_engagement_score(listener)
        tier = self._determine_tier(score, listener)

        return {
            "action": "check_listener",
            "node_id": node_id,
            "current_vip": listener.get("is_vip", False),
            "current_tier": listener.get("vip_tier"),
            "engagement_score": score,
            "eligible_tier": tier,
            "would_change": tier != listener.get("vip_tier")
        }

    def _queue_vip_announcement(self, node_id: str, tier: str, event_type: str) -> None:
        """Queue a VIP announcement shoutout."""
        state = self.read_state()
        pending = state.get("economy", {}).get("pending_shoutouts", [])

        templates = {
            "new": f"Welcome to the {tier.upper()} VIP club, {{node}}! 🌟",
            "promotion": f"{{node}} just leveled up to {tier.upper()} VIP! 🚀",
        }

        shoutout = {
            "node": node_id,
            "type": "vip_announcement",
            "tier": tier,
            "template": templates.get(event_type, templates["new"]),
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "priority": True
        }

        pending.insert(0, shoutout)
        self.write_state({"economy": {"pending_shoutouts": pending}})


if __name__ == "__main__":
    bee = VIPManagerBee()
    result = bee.run()
    print(result)
