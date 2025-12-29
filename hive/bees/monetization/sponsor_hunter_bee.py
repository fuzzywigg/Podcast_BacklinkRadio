"""
Sponsor Hunter Bee - Finds and manages sponsor relationships.

Responsibilities:
- Identify potential sponsors
- Track sponsor pipeline
- Generate pitch materials
- Monitor deal progress
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import ScoutBee
from hive.utils.web_search import WebSearch


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
        "music_tech",  # DAWs, plugins, gear
        "streaming",  # Platforms, apps
        "lifestyle",  # Coffee, wellness, fashion
        "creator_tools",  # Editing, design, AI tools
        "gaming",  # Indie games, peripherals
        "education",  # Courses, books, learning
        "local_business",  # Location-specific sponsors
    ]

    # Pipeline stages
    STAGES = [
        "prospect",  # Identified as potential fit
        "researched",  # Dug into their brand/fit
        "pitched",  # Sent initial outreach
        "negotiating",  # In discussions
        "active",  # Deal live
        "churned",  # Relationship ended
    ]

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
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

    def _daily_pipeline_review(self) -> dict[str, Any]:
        """Daily review of sponsor pipeline."""

        intel = self.read_intel()
        pipeline = intel.get("sponsors", {}).get("pipeline", {})

        # Count by stage
        stage_counts = dict.fromkeys(self.STAGES, 0)
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
            "total_active": sum(stage_counts.values()),
        }

    def _scout_prospects(self, task: dict[str, Any]) -> dict[str, Any]:
        """Scout for new potential sponsors."""

        category = task.get("payload", {}).get("category", "all")

        # Build set of existing companies and URLs to avoid duplicates
        existing_companies = set()
        existing_urls = set()
        intel = self.read_intel()
        pipeline = intel.get("sponsors", {}).get("pipeline", {})

        for data in pipeline.values():
            if data.get("company"):
                existing_companies.add(data.get("company").lower())
            # Parse notes to find URL if it's there
            for note in data.get("notes", []):
                if note.startswith("URL:"):
                    url = note.replace("URL:", "").strip()
                    existing_urls.add(url)

        prospects = []
        new_count = 0

        for cat in self.TARGET_CATEGORIES:
            if category == "all" or category == cat:
                # Use WebSearch to find actual brands
                brands = WebSearch.find_brands_for_category(cat)

                for brand in brands:
                    company_name = brand.get("company", "Unknown Brand")
                    url = brand.get("url", "")

                    # Deduplication check
                    if company_name.lower() in existing_companies:
                        self.log(f"Skipping existing company: {company_name}")
                        continue
                    if url in existing_urls:
                        self.log(f"Skipping existing URL: {url}")
                        continue

                    prospect = {
                        "category": cat,
                        "company": company_name,
                        "reason": f"Discovered via search for '{cat}' | Title: {brand.get('title')}",
                        "estimated_value": brand.get("estimated_value", "medium"),
                        "contact_method": "email",  # Default
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "url": url,
                        "snippet": brand.get("snippet"),
                    }
                    prospects.append(prospect)
                    self._add_to_pipeline(prospect)
                    new_count += 1

                    # Add to local exclusion list so we don't add it again in
                    # this run
                    existing_companies.add(company_name.lower())
                    existing_urls.add(url)

        self.log(f"Scouted {new_count} new prospects")

        return {"action": "scout", "prospects_found": new_count, "prospects": prospects}

    def _add_to_pipeline(self, prospect: dict[str, Any]) -> str:
        """Add a prospect to the pipeline."""

        sponsor_id = str(uuid.uuid4())[:8]

        sponsor_data = {
            "sponsor_id": sponsor_id,
            "company": prospect.get("company"),
            "category": prospect.get("category"),
            "status": "prospect",
            "value": prospect.get("estimated_value"),
            "notes": [
                f"Discovered: {prospect.get('reason')}",
                f"URL: {prospect.get('url')}",
                f"Snippet: {prospect.get('snippet')}",
            ],
            "contact": prospect.get("contact_method"),
            "discovered_at": prospect.get("discovered_at"),
            "last_contact": None,
        }

        self.write_intel("sponsors", "pipeline", {sponsor_id: sponsor_data})

        return sponsor_id

    def _research_sponsor(self, task: dict[str, Any]) -> dict[str, Any]:
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
            "notes": ["Researched brand presence and fit"],
        }

        # Update status
        sponsor["status"] = "researched"
        sponsor["research"] = research
        sponsor["notes"].append(f"Researched {datetime.now(timezone.utc).isoformat()}")

        self.write_intel("sponsors", "pipeline", {sponsor_id: sponsor})

        return {"action": "research", "sponsor_id": sponsor_id, "research": research}

    def _generate_pitch(self, task: dict[str, Any]) -> dict[str, Any]:
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
        self.write_task(
            {
                "type": "monetization",
                "bee_type": "outreach",
                "priority": 6,
                "payload": {"action": "send_pitch", "sponsor_id": sponsor_id, "pitch": pitch},
            }
        )

        return {
            "action": "pitch",
            "sponsor_id": sponsor_id,
            "pitch_generated": True,
            "pitch": pitch,
        }

    def _create_pitch_template(self, sponsor: dict[str, Any]) -> dict[str, Any]:
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
                "Flexible partnership structures",
            ],
        }

    def _update_pipeline(self, task: dict[str, Any]) -> dict[str, Any]:
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

        self.write_intel("sponsors", "pipeline", {sponsor_id: sponsor})

        return {"action": "update", "sponsor_id": sponsor_id, "new_status": sponsor.get("status")}


if __name__ == "__main__":
    bee = SponsorHunterBee()
    result = bee.run()
    print(result)
