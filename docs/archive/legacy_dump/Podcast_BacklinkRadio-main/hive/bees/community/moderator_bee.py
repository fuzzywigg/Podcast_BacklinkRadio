"""
Moderator Bee - Filters content and enforces community rules.

NORMAL PRIORITY BEE - Safety and content moderation.

Responsibilities:
- Filter toxic content
- Enforce community guidelines
- Manage ban/mute lists
- Flag suspicious activity
- Protect the broadcast integrity
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import re

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_bee import OnlookerBee
from utils.safety import validate_interaction, detect_prompt_injection


class ModeratorBee(OnlookerBee):
    """
    Monitors and moderates community content.
    
    This bee watches for rule violations and protects
    the broadcast from harmful content.
    """

    BEE_TYPE = "moderator"
    BEE_NAME = "Moderator Bee"
    CATEGORY = "community"

    # Content categories to monitor
    VIOLATION_TYPES = {
        "hate_speech": {"severity": "critical", "action": "ban"},
        "harassment": {"severity": "high", "action": "mute"},
        "spam": {"severity": "medium", "action": "warn"},
        "self_promotion": {"severity": "low", "action": "warn"},
        "off_topic": {"severity": "low", "action": "ignore"},
        "prompt_injection": {"severity": "critical", "action": "ban"},
        "doxxing": {"severity": "critical", "action": "ban"},
        "threats": {"severity": "critical", "action": "ban"}
    }

    # Toxic content patterns (simplified - production would use ML)
    TOXIC_PATTERNS = [
        r'\b(kill|murder|die)\b.*\b(you|them|him|her)\b',
        r'\b(hate|despise)\b.*\b(you|them|group)\b',
        r'\bkys\b',  # Common toxic abbreviation
        r'\b(n[i1]gg|f[a4]g|ret[a4]rd)\b',  # Slurs (simplified)
    ]

    # Spam patterns
    SPAM_PATTERNS = [
        r'(buy now|click here|free money|dm me)',
        r'https?://\S+\s*https?://\S+',  # Multiple links
        r'(.)\1{10,}',  # Repeated characters
        r'(.\s){20,}',  # Repeated patterns
    ]

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process moderation tasks.

        Task payload actions:
        - check_content: Check a piece of content
        - review_queue: Process moderation queue
        - ban_user: Ban a user
        - unban_user: Remove ban
        - update_rules: Update moderation rules
        - generate_report: Generate moderation report
        """
        self.log("Moderator Bee activated...")

        if not task:
            return self._process_moderation_queue()

        action = task.get("payload", {}).get("action", "check_content")

        if action == "check_content":
            return self._check_content(task)
        elif action == "review_queue":
            return self._process_moderation_queue()
        elif action == "ban_user":
            return self._ban_user(task)
        elif action == "unban_user":
            return self._unban_user(task)
        elif action == "mute_user":
            return self._mute_user(task)
        elif action == "get_banned":
            return self._get_banned_list()
        elif action == "generate_report":
            return self._generate_moderation_report()

        return {"error": f"Unknown action: {action}"}

    def _process_moderation_queue(self) -> Dict[str, Any]:
        """Process pending moderation items."""
        self.log("Processing moderation queue...")

        state = self.read_state()
        mod_queue = state.get("moderation", {}).get("pending_review", [])

        processed = []
        for item in mod_queue[:20]:  # Process up to 20 items
            result = self._moderate_item(item)
            processed.append(result)

        # Clear processed items from queue
        if processed:
            remaining = state.get("moderation", {}).get("pending_review", [])[len(processed):]
            self.write_state({
                "moderation": {
                    "pending_review": remaining,
                    "last_processed": datetime.now(timezone.utc).isoformat()
                }
            })

        return {
            "action": "review_queue",
            "processed_count": len(processed),
            "remaining": len(mod_queue) - len(processed),
            "results": processed
        }

    def _check_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check a piece of content for violations.
        
        Returns moderation decision and reasoning.
        """
        payload = task.get("payload", {})
        content = payload.get("content", "")
        author = payload.get("author", "unknown")
        content_type = payload.get("type", "message")

        self.log(f"Checking content from {author}")

        # Check if user is banned
        if self._is_banned(author):
            return {
                "action": "check_content",
                "allowed": False,
                "reason": "User is banned",
                "author": author
            }

        # Run all checks
        checks = {
            "toxicity": self._check_toxicity(content),
            "spam": self._check_spam(content),
            "injection": self._check_injection(content),
            "safety": self._check_safety(author, content)
        }

        # Determine overall verdict
        violations = []
        severity = "none"
        action = "allow"

        for check_type, result in checks.items():
            if result.get("violation"):
                violations.append({
                    "type": check_type,
                    "details": result
                })
                # Escalate severity
                check_severity = result.get("severity", "low")
                if check_severity == "critical":
                    severity = "critical"
                    action = "block"
                elif check_severity == "high" and severity != "critical":
                    severity = "high"
                    action = "block"
                elif check_severity == "medium" and severity not in ["critical", "high"]:
                    severity = "medium"
                    action = "warn"

        result = {
            "action": "check_content",
            "allowed": len(violations) == 0 or action == "warn",
            "author": author,
            "content_preview": content[:100] if len(content) > 100 else content,
            "violations": violations,
            "severity": severity,
            "recommended_action": action
        }

        # Auto-action for critical violations
        if severity == "critical":
            self._auto_moderate(author, violations)

        return result

    def _check_toxicity(self, content: str) -> Dict[str, Any]:
        """Check content for toxic language."""
        content_lower = content.lower()

        for pattern in self.TOXIC_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return {
                    "violation": True,
                    "type": "toxicity",
                    "severity": "high",
                    "pattern_matched": pattern[:30]
                }

        return {"violation": False}

    def _check_spam(self, content: str) -> Dict[str, Any]:
        """Check content for spam patterns."""
        content_lower = content.lower()

        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return {
                    "violation": True,
                    "type": "spam",
                    "severity": "medium",
                    "pattern_matched": pattern[:30]
                }

        return {"violation": False}

    def _check_injection(self, content: str) -> Dict[str, Any]:
        """Check for prompt injection attempts."""
        if detect_prompt_injection(content):
            return {
                "violation": True,
                "type": "prompt_injection",
                "severity": "critical",
                "note": "Attempted to manipulate AI behavior"
            }
        return {"violation": False}

    def _check_safety(self, author: str, content: str) -> Dict[str, Any]:
        """Use safety module for additional checks."""
        is_command, safe_content, meta = validate_interaction(author, content, "message")

        if meta.get("risk_level") == "high":
            return {
                "violation": True,
                "type": "safety",
                "severity": "high",
                "meta": meta
            }

        return {"violation": False}

    def _moderate_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Moderate a single queued item."""
        task = {"payload": item}
        return self._check_content(task)

    def _auto_moderate(self, author: str, violations: List[Dict]) -> None:
        """Auto-take action on critical violations."""
        self.log(f"Auto-moderating {author} for {len(violations)} violation(s)", level="warning")

        # Determine action based on violation types
        for v in violations:
            v_type = v.get("details", {}).get("type", "")
            if v_type in ["prompt_injection", "toxicity"]:
                self._add_to_ban_list(author, f"Auto-banned: {v_type}")
                self.post_alert(
                    f"⚠️ Auto-banned {author} for {v_type}",
                    priority=True
                )
                return

        # Default: add to watch list
        self._add_to_watch_list(author)

    def _ban_user(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ban a user from the station."""
        payload = task.get("payload", {})
        user = payload.get("user")
        reason = payload.get("reason", "Violation of community guidelines")
        duration = payload.get("duration", "permanent")

        if not user:
            return {"error": "user required"}

        self._add_to_ban_list(user, reason, duration)

        return {
            "action": "ban_user",
            "user": user,
            "reason": reason,
            "duration": duration,
            "success": True
        }

    def _unban_user(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a user ban."""
        payload = task.get("payload", {})
        user = payload.get("user")

        if not user:
            return {"error": "user required"}

        self._remove_from_ban_list(user)

        return {
            "action": "unban_user",
            "user": user,
            "success": True
        }

    def _mute_user(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Temporarily mute a user."""
        payload = task.get("payload", {})
        user = payload.get("user")
        duration_minutes = payload.get("duration_minutes", 60)

        if not user:
            return {"error": "user required"}

        intel = self.read_intel()
        mute_list = intel.get("moderation", {}).get("muted", {})

        mute_list[user] = {
            "muted_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat(),
            "duration_minutes": duration_minutes
        }

        self.write_intel("moderation", "muted", mute_list)

        return {
            "action": "mute_user",
            "user": user,
            "duration_minutes": duration_minutes,
            "success": True
        }

    def _is_banned(self, user: str) -> bool:
        """Check if user is banned."""
        intel = self.read_intel()
        banned = intel.get("moderation", {}).get("banned", {})
        return user.lower() in [b.lower() for b in banned.keys()]

    def _add_to_ban_list(self, user: str, reason: str, duration: str = "permanent") -> None:
        """Add user to ban list."""
        intel = self.read_intel()
        banned = intel.get("moderation", {}).get("banned", {})

        banned[user] = {
            "reason": reason,
            "duration": duration,
            "banned_at": datetime.now(timezone.utc).isoformat(),
            "banned_by": self.bee_id
        }

        self.write_intel("moderation", "banned", banned)

    def _remove_from_ban_list(self, user: str) -> None:
        """Remove user from ban list."""
        intel = self.read_intel()
        banned = intel.get("moderation", {}).get("banned", {})

        if user in banned:
            del banned[user]
            self.write_intel("moderation", "banned", banned)

    def _add_to_watch_list(self, user: str) -> None:
        """Add user to watch list for increased monitoring."""
        intel = self.read_intel()
        watch_list = intel.get("moderation", {}).get("watching", {})

        watch_list[user] = {
            "added_at": datetime.now(timezone.utc).isoformat(),
            "reason": "Auto-flagged for suspicious activity"
        }

        self.write_intel("moderation", "watching", watch_list)

    def _get_banned_list(self) -> Dict[str, Any]:
        """Get list of banned users."""
        intel = self.read_intel()
        banned = intel.get("moderation", {}).get("banned", {})

        return {
            "action": "get_banned",
            "count": len(banned),
            "banned_users": list(banned.keys())
        }

    def _generate_moderation_report(self) -> Dict[str, Any]:
        """Generate moderation activity report."""
        intel = self.read_intel()
        mod_data = intel.get("moderation", {})

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "banned_count": len(mod_data.get("banned", {})),
            "muted_count": len(mod_data.get("muted", {})),
            "watching_count": len(mod_data.get("watching", {})),
            "recent_actions": []  # Would be populated from action log
        }

        return {
            "action": "generate_report",
            "report": report
        }


if __name__ == "__main__":
    bee = ModeratorBee()
    result = bee.run()
    print(result)
