"""
Newsletter Bee - Creates and manages email newsletters.

The Newsletter Bee handles:
- Generating weekly digest content
- Personalization based on listener preferences
- Scheduling and queue management
- Template rendering
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee


class NewsletterBee(EmployedBee):
    """
    Newsletter Bee - Weekly digest creation.
    
    Features:
    - Generate content from hive intel
    - Create personalized digests
    - Track newsletter performance
    - Manage subscriber preferences
    """
    
    BEE_TYPE = "newsletter"
    BEE_NAME = "Newsletter Writer"
    CATEGORY = "marketing"
    LINEAGE_VERSION = "1.0.0"
    
    # Newsletter sections
    SECTIONS = [
        "highlights",      # Top moments from the week
        "upcoming",        # What's coming next
        "community",       # Shoutouts, VIPs
        "trending",        # Hot topics/trends
        "behind_scenes",   # Station news
        "call_to_action"   # Engagement prompt
    ]
    
    def __init__(self, hive_path: Optional[str] = None, gateway: Any = None):
        """Initialize Newsletter Bee."""
        super().__init__(hive_path, gateway)
        self.newsletters_file = self.honeycomb_path / "newsletters.json"
        self._ensure_newsletters_file()
    
    def _ensure_newsletters_file(self):
        """Ensure newsletters.json exists."""
        if not self.newsletters_file.exists():
            initial = {
                "_meta": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0"
                },
                "drafts": [],
                "sent": [],
                "templates": {},
                "stats": {
                    "total_sent": 0,
                    "total_opens": 0,
                    "total_clicks": 0
                }
            }
            with open(self.newsletters_file, 'w') as f:
                json.dump(initial, f, indent=2)
    
    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process newsletter tasks.
        
        Actions:
        - generate: Generate a new newsletter draft
        - preview: Preview a newsletter
        - send: Queue newsletter for sending
        - stats: Get newsletter performance stats
        """
        action = "generate"
        if task and "payload" in task:
            action = task["payload"].get("action", "generate")
        
        if action == "generate":
            return self._generate_newsletter(task.get("payload", {}) if task else {})
        elif action == "preview":
            return self._preview_newsletter(task["payload"].get("newsletter_id"))
        elif action == "send":
            return self._queue_for_send(task["payload"])
        elif action == "stats":
            return self._get_stats()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def _load_newsletters(self) -> Dict[str, Any]:
        """Load newsletters data."""
        with open(self.newsletters_file, 'r') as f:
            return json.load(f)
    
    def _save_newsletters(self, data: Dict[str, Any]) -> None:
        """Save newsletters data."""
        data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.newsletters_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _generate_newsletter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new newsletter draft from hive intel."""
        # Load intel for content
        intel = self.read_intel()
        state = self.read_state()
        
        # Determine date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        # Build sections
        sections = {}
        
        # Highlights section
        sections["highlights"] = self._build_highlights(intel, state)
        
        # Upcoming section
        sections["upcoming"] = self._build_upcoming(state)
        
        # Community section
        sections["community"] = self._build_community(intel, state)
        
        # Trending section
        sections["trending"] = self._build_trending(intel)
        
        # Behind the scenes
        sections["behind_scenes"] = payload.get("behind_scenes", {
            "title": "Station Update",
            "content": "Thanks for being part of the Backlink family!"
        })
        
        # Call to action
        sections["call_to_action"] = payload.get("call_to_action", {
            "title": "Join the Conversation",
            "content": "Reply to this email with your favorite moment from this week!",
            "button_text": "Listen Live",
            "button_url": "#"
        })
        
        # Create draft
        import hashlib
        newsletter_id = hashlib.sha256(
            f"newsletter:{end_date.isoformat()}".encode()
        ).hexdigest()[:12]
        
        draft = {
            "id": newsletter_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "subject": payload.get("subject", f"This Week at Backlink - {end_date.strftime('%B %d')}"),
            "preview_text": payload.get("preview_text", "Your weekly dose of Backlink goodness"),
            "sections": sections,
            "status": "draft"
        }
        
        data = self._load_newsletters()
        data["drafts"].append(draft)
        self._save_newsletters(data)
        
        self.log(f"Generated newsletter draft: {newsletter_id}")
        
        return {
            "success": True,
            "newsletter_id": newsletter_id,
            "subject": draft["subject"],
            "sections_generated": list(sections.keys()),
            "period": draft["period"]
        }
    
    def _build_highlights(self, intel: Dict, state: Dict) -> Dict[str, Any]:
        """Build highlights section from intel."""
        highlights = []
        
        # Get top content
        content_perf = intel.get("content_performance", {})
        if content_perf:
            top_content = sorted(
                content_perf.items(),
                key=lambda x: x[1].get("engagement", 0) if isinstance(x[1], dict) else 0,
                reverse=True
            )[:3]
            
            for content_id, perf in top_content:
                if isinstance(perf, dict):
                    highlights.append({
                        "title": perf.get("title", content_id),
                        "engagement": perf.get("engagement", 0),
                        "type": "content"
                    })
        
        return {
            "title": "This Week's Highlights",
            "items": highlights if highlights else [
                {"title": "Thanks for tuning in!", "type": "message"}
            ]
        }
    
    def _build_upcoming(self, state: Dict) -> Dict[str, Any]:
        """Build upcoming section."""
        upcoming = state.get("upcoming_events", [])
        
        return {
            "title": "Coming Up",
            "items": upcoming[:5] if upcoming else [
                {"title": "Stay tuned for exciting announcements!", "type": "teaser"}
            ]
        }
    
    def _build_community(self, intel: Dict, state: Dict) -> Dict[str, Any]:
        """Build community section."""
        # Get VIP shoutouts
        vips = state.get("vip_spotlight", [])
        shoutouts = state.get("pending_shoutouts", [])[:5]
        
        return {
            "title": "Community Corner",
            "vip_spotlight": vips[:3] if vips else [],
            "shoutouts": shoutouts,
            "message": "You make Backlink special. Thank you!"
        }
    
    def _build_trending(self, intel: Dict) -> Dict[str, Any]:
        """Build trending section from intel."""
        trends = intel.get("trends", {}).get("current", [])
        
        return {
            "title": "What's Trending",
            "items": trends[:5] if trends else [
                {"topic": "Music", "note": "Always trending with us!"}
            ]
        }
    
    def _preview_newsletter(self, newsletter_id: Optional[str]) -> Dict[str, Any]:
        """Preview a newsletter draft."""
        if not newsletter_id:
            return {"error": "Missing newsletter_id"}
        
        data = self._load_newsletters()
        
        for draft in data["drafts"]:
            if draft["id"] == newsletter_id:
                # Render to simple text preview
                preview = self._render_preview(draft)
                return {
                    "found": True,
                    "newsletter": draft,
                    "preview": preview
                }
        
        return {"found": False, "error": f"Newsletter {newsletter_id} not found"}
    
    def _render_preview(self, draft: Dict[str, Any]) -> str:
        """Render newsletter to text preview."""
        lines = []
        lines.append(f"Subject: {draft['subject']}")
        lines.append(f"Preview: {draft['preview_text']}")
        lines.append("-" * 50)
        
        sections = draft.get("sections", {})
        
        for section_key, section in sections.items():
            if isinstance(section, dict):
                title = section.get("title", section_key.replace("_", " ").title())
                lines.append(f"\n## {title}\n")
                
                # Handle items
                if "items" in section:
                    for item in section["items"]:
                        if isinstance(item, dict):
                            lines.append(f"  - {item.get('title', item.get('topic', str(item)))}")
                        else:
                            lines.append(f"  - {item}")
                
                # Handle content
                if "content" in section:
                    lines.append(f"\n{section['content']}")
                
                # Handle message
                if "message" in section:
                    lines.append(f"\n{section['message']}")
        
        return "\n".join(lines)
    
    def _queue_for_send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Queue a newsletter for sending."""
        newsletter_id = payload.get("newsletter_id")
        send_at = payload.get("send_at")  # ISO timestamp or "now"
        
        if not newsletter_id:
            return {"error": "Missing newsletter_id"}
        
        data = self._load_newsletters()
        
        # Find draft
        draft_idx = None
        draft = None
        for idx, d in enumerate(data["drafts"]):
            if d["id"] == newsletter_id:
                draft = d
                draft_idx = idx
                break
        
        if not draft:
            return {"error": f"Draft {newsletter_id} not found"}
        
        # Update status
        draft["status"] = "queued"
        draft["queued_at"] = datetime.now(timezone.utc).isoformat()
        draft["send_at"] = send_at or datetime.now(timezone.utc).isoformat()
        
        # Move to sent (in production, this would go to email service)
        data["drafts"].pop(draft_idx)
        data["sent"].append(draft)
        data["stats"]["total_sent"] += 1
        
        self._save_newsletters(data)
        
        self.log(f"Queued newsletter {newsletter_id} for sending")
        
        return {
            "success": True,
            "newsletter_id": newsletter_id,
            "subject": draft["subject"],
            "status": "queued",
            "send_at": draft["send_at"]
        }
    
    def _get_stats(self) -> Dict[str, Any]:
        """Get newsletter performance stats."""
        data = self._load_newsletters()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "drafts_pending": len(data["drafts"]),
            "total_sent": data["stats"]["total_sent"],
            "total_opens": data["stats"]["total_opens"],
            "total_clicks": data["stats"]["total_clicks"],
            "open_rate": (
                data["stats"]["total_opens"] / max(data["stats"]["total_sent"], 1)
            ),
            "click_rate": (
                data["stats"]["total_clicks"] / max(data["stats"]["total_opens"], 1)
            ),
            "recent_sent": [
                {
                    "id": n["id"],
                    "subject": n["subject"],
                    "sent_at": n.get("queued_at")
                }
                for n in data["sent"][-5:]
            ]
        }
