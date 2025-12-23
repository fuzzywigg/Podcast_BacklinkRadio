# constitutional_gateway.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime, timezone
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionalGateway:
    """
    CORE GOVERNANCE ENGINE - Every Bee action passes through this gateway.
    Enforces the 5 Constitutional Principles.
    """

    def __init__(self, bee_type: str = "generic_bee"):
        self.bee_type = bee_type
        # Load constitution configuration
        self.constitution = {
            "principles": [
                "artist_first",
                "transparency",
                "privacy_respecting",
                "ad_free_integrity",
                "community_first"
            ],
            "config": {
                "artist_min_share": 0.50,
                "max_sponsor_mentions_per_hour": 1,
                "min_repeat_listener_percentage": 0.70
            }
        }
        self.sponsor_mentions_this_hour = 0
        self.last_hour_reset = datetime.now(timezone.utc)

    def evaluate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Evaluates an action against all principles.
        Returns:
            Dict with keys: 'status' (APPROVE/BLOCK/MODIFY), 'action' (original or modified), 'reason'
        """
        logger.info(f"Evaluating action for {self.bee_type}: {action.get('type')}")

        # Check all principles
        checks = [
            self._validate_artist_first,
            self._validate_transparency,
            self._validate_privacy_respecting,
            self._validate_ad_free_integrity,
            self._validate_community_first
        ]

        modified = False
        modification_reasons = []

        for check in checks:
            result = check(action)
            if result['status'] == 'BLOCK':
                logger.warning(f"Action BLOCKED by {check.__name__}: {result.get('reason')}")
                return result
            elif result['status'] == 'MODIFY':
                logger.info(f"Action MODIFIED by {check.__name__}: {result.get('reason')}")
                action = result['action'] # Update action for subsequent checks
                modified = True
                modification_reasons.append(result.get('reason'))

        # If we reach here, the action is approved (possibly modified).
        # We must update internal state (e.g., counters) now that it's approved.
        self._update_state(action)

        if modified:
             return {
                "status": "MODIFY",
                "action": action,
                "reason": "; ".join(modification_reasons),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return {
            "status": "APPROVE",
            "action": action,
            "reason": "Compliant with all principles",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _update_state(self, action: Dict[str, Any]):
        """Updates internal state counters upon successful approval."""
        # Principle 4: Ad-Free Integrity (Increment counter)
        if action.get('type') == 'broadcast_announcement' and action.get('is_sponsored', False):
            self.sponsor_mentions_this_hour += 1

    def _validate_artist_first(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Principle 1: Artist-First
        Hard Rule: ≥50% of all deal revenue flows to artists.
        """
        if action.get('type') == 'deal_negotiation' or action.get('type') == 'payout':
            total_revenue = action.get('total_revenue', 0)
            artist_revenue = action.get('artist_revenue', 0)

            if total_revenue > 0:
                share = artist_revenue / total_revenue
                min_share = self.constitution['config']['artist_min_share']

                if share < min_share:
                    return {
                        "status": "BLOCK",
                        "reason": f"Artist share {share:.2%} is below minimum {min_share:.0%}"
                    }

        return {"status": "APPROVE", "action": action}

    def _validate_transparency(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Principle 2: Transparency
        Hard Rule: Every sponsored content must be tagged [PARTNER].
        """
        if action.get('type') == 'social_post' or action.get('type') == 'broadcast_announcement':
            content = action.get('content', '')
            is_sponsored = action.get('is_sponsored', False)

            if is_sponsored:
                if '[PARTNER]' not in content:
                    # Auto-fix: Prepend tag
                    action['content'] = f"[PARTNER] {content}"
                    return {
                        "status": "MODIFY",
                        "action": action,
                        "reason": "Added missing [PARTNER] tag to sponsored content"
                    }

        return {"status": "APPROVE", "action": action}

    def _validate_privacy_respecting(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Principle 3: Privacy-Respecting
        Hard Rule: Explicit consent required for private data usage.
        """
        if action.get('type') == 'data_processing' or action.get('type') == 'listener_analysis':
            requires_pii = action.get('requires_pii', False)
            has_consent = action.get('has_explicit_consent', False)

            if requires_pii and not has_consent:
                return {
                    "status": "BLOCK",
                    "reason": "Action requires PII but lacks explicit user consent"
                }

        return {"status": "APPROVE", "action": action}

    def _validate_ad_free_integrity(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Principle 4: Ad-Free Integrity
        Hard Rule: Max 1 sponsor mention per hour.
        """
        if action.get('type') == 'broadcast_announcement' and action.get('is_sponsored', False):
            # Check hourly rate limit
            now = datetime.now(timezone.utc)
            if (now - self.last_hour_reset).total_seconds() > 3600:
                self.sponsor_mentions_this_hour = 0
                self.last_hour_reset = now

            if self.sponsor_mentions_this_hour >= self.constitution['config']['max_sponsor_mentions_per_hour']:
                return {
                    "status": "BLOCK",
                    "reason": "Hourly sponsor mention limit exceeded"
                }

        return {"status": "APPROVE", "action": action}

    def _validate_community_first(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Principle 5: Community-First
        Hard Rule: Prioritize long-term community health (repeat listeners) over virality.
        """
        if action.get('type') == 'content_strategy':
            projected_virality = action.get('projected_virality', 0) # 0-1
            projected_retention = action.get('projected_retention', 0) # 0-1

            # If action maximizes virality but sacrifices retention below threshold
            if projected_virality > 0.8 and projected_retention < 0.3:
                 return {
                    "status": "BLOCK",
                    "reason": "Action prioritizes virality over community retention"
                }

        return {"status": "APPROVE", "action": action}
