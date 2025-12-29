"""
Traffic Sponsor Bee - Manage sponsored traffic reports.

Responsibilities:
- Check for active traffic sponsors.
- Fetch traffic data.
- Trigger sponsored announcements.
"""

from datetime import datetime, timezone
from typing import Any

from hive.bees.base_bee import EmployedBee


class TrafficSponsorBee(EmployedBee):
    """
    Manages hourly traffic reports.
    """

    BEE_TYPE = "traffic_sponsor"
    BEE_NAME = "Traffic Sponsor Bee"
    CATEGORY = "monetization"

    async def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute traffic tasks.
        """
        self.log("Traffic Bee monitoring routes...")

        # Check time: Traffic on the hour (:00)
        now = datetime.now(timezone.utc)
        # Allow a small window (e.g. min 0 or 1)
        is_on_the_hour = now.minute <= 1

        if not is_on_the_hour and not task:
            return {"status": "skipped", "reason": "not_on_the_hour"}

        # Check Sponsor
        config = self._load_config()
        sponsor_cfg = config.get("sponsored_content", {}).get("traffic_sponsor", {})

        if not sponsor_cfg.get("active"):
            return {"status": "skipped", "reason": "no_active_sponsor"}

        # Fetch Traffic
        traffic_data = self._fetch_traffic_simulated()

        # Compose Script
        script = self._compose_traffic_report(sponsor_cfg, traffic_data)

        # Queue for DJ (simulated as task or direct intel update)
        # We'll push an announcement to the broadcast queue if we can access it,
        # or just log it for the DJ to pick up via intel.

        announcement = {
            "type": "sponsored_traffic",
            "duration": 20,
            "script": script,
            "sponsor": sponsor_cfg.get("name"),
        }

        # For now, we update intel so DJ sees it
        self._update_traffic_intel(announcement)

        return {"status": "success", "announcement": announcement}

    def _compose_traffic_report(self, sponsor: dict, data: list) -> str:
        """Format: Brought to you by [Sponsor]..."""
        intro = f"Traffic on the hour, brought to you by {sponsor.get('name', 'Sponsor')}. "

        reports = []
        for item in data:
            if item["incidents"] > 0:
                reports.append(f"{item['city']}: {item['incidents']} incidents reported.")
            else:
                reports.append(f"{item['city']}: clear.")

        outro = f" That's your traffic report from {sponsor.get('name')}."
        return intro + " ".join(reports) + outro

    def _fetch_traffic_simulated(self) -> list:
        return [
            {"city": "New York", "incidents": 2, "delays": "15m"},
            {"city": "London", "incidents": 0, "delays": "0m"},
        ]

    def _update_traffic_intel(self, announcement: dict):
        intel = self.read_intel()
        intel["traffic"] = {
            "latest_announcement": announcement,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_json("intel.json", intel)

    def _load_config(self) -> dict:
        """Load hive config."""
        try:
            with open(self.hive_path / "config.json") as f:
                import json

                return json.load(f)
        except BaseException:
            return {}
