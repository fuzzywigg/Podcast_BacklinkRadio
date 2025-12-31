"""
Sponsor Hunter Bee - Finds and manages sponsor relationships.

Responsibilities:
- Identify potential sponsors
- Track sponsor pipeline
- Generate pitch materials
- Monitor deal progress
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import ScoutBee


class SponsorHunterBee(ScoutBee):
    """
    Scouts for sponsorship opportunities.

    Identifies brands aligned with the station's vibe,
    tracks outreach, and manages the sponsor pipeline.
    """

    BEE_TYPE = "sponsor_hunter"
    BEE_NAME = "Sponsor Hunter Bee"
    CATEGORY = "monetization"

    # Sponsor categories aligned with station vibe
    TARGET_CATEGORIES = [
        "music_tech",        # DAWs, plugins, gear
        "streaming",         # Platforms, apps
        "lifestyle",         # Coffee, wellness, fashion
        "creator_tools",     # Editing, design, AI tools
        "gaming",            # Indie games, peripherals
        "education",         # Courses, books, learning
        "local_business"     # Location-specific sponsors
    ]

    # Pipeline stages
    STAGES = [
        "prospect",      # Identified as potential fit
        "researched",    # Dug into their brand/fit
        "pitched",       # Sent initial outreach
        "negotiating",   # In discussions
        "active",        # Deal live
        "churned"        # Relationship ended
    ]

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute sponsor hunting tasks.

        Task payload can include:
        - action: scout|research|pitch|update
        - category: specific category to focus on
        - sponsor_id: specific sponsor to work on
        """
        self.log("Sponsor hunting initiated...")

        if not task:
            # Default: review pipeline and scout new prospects
            return self._daily_pipeline_review()

        action = task.get("payload", {}).get("action", "scout")

        if action == "scout":
            return self._scout_prospects(task)
        elif action == "research":
            return self._research_sponsor(task)
        elif action == "pitch":
            return self._generate_pitch(task)
        elif action == "update":
            return self._update_pipeline(task)

        return {"error": "Unknown action"}

    def _daily_pipeline_review(self) -> Dict[str, Any]:
        """Daily review of sponsor pipeline."""

        intel = self.read_intel()
        pipeline = intel.get("sponsors", {}).get("pipeline", {})

        # Count by stage
        stage_counts = {stage: 0 for stage in self.STAGES}
        needs_attention = []

        for sponsor_id, data in pipeline.items():
            stage = data.get("status", "prospect")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

            # Check if needs follow-up
            last_contact = data.get("last_contact")
            if last_contact and stage in ["pitched", "negotiating"]:
                # Would check if stale
                needs_attention.append(sponsor_id)

        # Scout for new prospects if pipeline is thin
        if stage_counts.get("prospect", 0) < 5:
            self._scout_prospects({})

        return {
            "action": "daily_review",
            "pipeline_summary": stage_counts,
            "needs_attention": needs_attention,
            "total_active": sum(stage_counts.values())
        }

    def _scout_prospects(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Scout for new potential sponsors."""

        category = task.get("payload", {}).get("category", "all")

        prospects = []

        # In production, would search for brands via APIs, web scraping
        # Placeholder with structure

        for cat in self.TARGET_CATEGORIES:
            if category == "all" or category == cat:
                prospect = self._find_prospect_in_category(cat)
                if prospect:
                    prospects.append(prospect)
                    self._add_to_pipeline(prospect)

        self.log(f"Scouted {len(prospects)} new prospects")

        return {
            "action": "scout",
            "prospects_found": len(prospects),
            "prospects": prospects
        }

    def _find_prospect_in_category(self, category: str) -> Optional[Dict[str, Any]]:
        """Find a prospect in a specific category."""

        # Placeholder - would use actual discovery
        return {
            "category": category,
            "company": f"Sample Company ({category})",
            "reason": "Aligned with station vibe and audience",
            "estimated_value": "medium",
            "contact_method": "email",
            "discovered_at": datetime.now(timezone.utc).isoformat()
        }

    def _add_to_pipeline(self, prospect: Dict[str, Any]) -> str:
        """Add a prospect to the pipeline."""

        import uuid
        sponsor_id = str(uuid.uuid4())[:8]

        self.write_intel("sponsors", f"pipeline.{sponsor_id}", {
            "sponsor_id": sponsor_id,
            "company": prospect.get("company"),
            "category": prospect.get("category"),
            "status": "prospect",
            "value": prospect.get("estimated_value"),
            "notes": [f"Discovered: {prospect.get('reason')}"],
            "contact": prospect.get("contact_method"),
            "discovered_at": prospect.get("discovered_at"),
            "last_contact": None
        })

        return sponsor_id

    def _research_sponsor(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Deep research on a specific sponsor."""

        sponsor_id = task.get("payload", {}).get("sponsor_id")
        if not sponsor_id:
            return {"error": "No sponsor_id provided"}

        # Get existing data
        intel = self.read_intel()
        sponsor = intel.get("sponsors", {}).get("pipeline", {}).get(sponsor_id)

        if not sponsor:
            return {"error": f"Sponsor {sponsor_id} not found"}

        # Research
        research = {
            "brand_voice": "professional_casual",
            "audience_overlap": 0.7,
            "budget_signals": "medium",
            "past_sponsorships": [],
            "decision_maker": None,
            "notes": ["Researched brand presence and fit"]
        }

        # Update status
        sponsor["status"] = "researched"
        sponsor["research"] = research
        sponsor["notes"].append(f"Researched {datetime.now(timezone.utc).isoformat()}")

        self.write_intel("sponsors", f"pipeline.{sponsor_id}", sponsor)

        return {
            "action": "research",
            "sponsor_id": sponsor_id,
            "research": research
        }

    def _generate_pitch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a pitch for a sponsor."""

        sponsor_id = task.get("payload", {}).get("sponsor_id")
        if not sponsor_id:
            return {"error": "No sponsor_id provided"}

        intel = self.read_intel()
        sponsor = intel.get("sponsors", {}).get("pipeline", {}).get(sponsor_id)

        if not sponsor:
            return {"error": f"Sponsor {sponsor_id} not found"}

        # Generate pitch template
        pitch = self._create_pitch_template(sponsor)

        # Create outreach task
        self.write_task({
            "type": "monetization",
            "bee_type": "outreach",
            "priority": 6,
            "payload": {
                "action": "send_pitch",
                "sponsor_id": sponsor_id,
                "pitch": pitch
            }
        })

        return {
            "action": "pitch",
            "sponsor_id": sponsor_id,
            "pitch_generated": True,
            "pitch": pitch
        }

    def _create_pitch_template(self, sponsor: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pitch template for a sponsor."""

        company = sponsor.get("company", "Brand")

        return {
            "subject": f"Partnership Opportunity: {company} x Backlink Broadcast",
            "template": f"""
Hi [Contact],

I'm reaching out from Backlink Broadcast, a music-first, ad-free radio experience.

We noticed {company}'s alignment with our audience of music enthusiasts and
thought there might be an interesting partnership opportunity.

Our model is different - instead of traditional ads, we integrate brands
through authentic mentions and content partnerships. Think "brought to you by"
moments that feel natural, not intrusive.

Would you be open to a brief chat about what this could look like?

Best,
[Host Name]
Backlink Broadcast
""",
            "value_props": [
                "Ad-free environment = higher attention",
                "Loyal, engaged listener base",
                "Authentic integration, not interruption",
                "Flexible partnership structures"
            ]
        }

    def _update_pipeline(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update a sponsor's pipeline status."""

        payload = task.get("payload", {})
        sponsor_id = payload.get("sponsor_id")
        new_status = payload.get("status")
        notes = payload.get("notes")

        if not sponsor_id:
            return {"error": "No sponsor_id provided"}

        intel = self.read_intel()
        sponsor = intel.get("sponsors", {}).get("pipeline", {}).get(sponsor_id)

        if not sponsor:
            return {"error": f"Sponsor {sponsor_id} not found"}

        if new_status:
            sponsor["status"] = new_status
        if notes:
            sponsor["notes"].append(notes)

        sponsor["last_contact"] = datetime.now(timezone.utc).isoformat()

        self.write_intel("sponsors", f"pipeline.{sponsor_id}", sponsor)

        return {
            "action": "update",
            "sponsor_id": sponsor_id,
            "new_status": sponsor.get("status")
        }


if __name__ == "__main__":
    bee = SponsorHunterBee()
    result = bee.run()
    print(result)
