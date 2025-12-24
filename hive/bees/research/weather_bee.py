"""
Weather Bee - Provides weather updates on the 8s.

Responsibilities:
- Fetch weather for top listener locations.
- Trigger weather tweets at :08 and :38.
- Provide weather snippets for the DJ.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import EmployedBee
from hive.utils.plausible_andon import analytics

class WeatherBee(EmployedBee):
    """
    Manages weather intel and updates.
    """

    BEE_TYPE = "weather"
    BEE_NAME = "Weather Bee"
    CATEGORY = "research"

    async def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute weather tasks.
        """
        self.log("Weather Bee scanning skies...")

        # Check time for "On the 8s"
        now = datetime.now(timezone.utc)
        is_on_the_8s = now.minute in [8, 38]

        # 1. Fetch Weather Data (Simulated for now, would use OpenWeatherMap)
        intel = self.read_intel()
        top_nodes = self._get_top_node_locations(intel)

        weather_reports = []
        for location in top_nodes:
            report = self._fetch_weather_simulated(location)
            weather_reports.append(report)

        # 2. Update Honeycomb (for DJ to read)
        latest_snippet = f"{weather_reports[0]['city']}: {weather_reports[0]['temp']}F, {weather_reports[0]['conditions']}"
        self._update_weather_intel(weather_reports, latest_snippet)

        # 3. Tweet if time match
        tweet_result = None
        if is_on_the_8s:
            tweet_result = await self._tweet_weather_on_8s(weather_reports)

        return {
            "status": "success",
            "reports_fetched": len(weather_reports),
            "tweet_sent": tweet_result
        }

    async def _tweet_weather_on_8s(self, weather_data: list):
        """Post weather for active node locations."""
        tweet = self._compose_weather_tweet(weather_data)

        # Spawn social poster task
        task = {
            "type": "marketing",
            "bee_type": "social_poster",
            "priority": 8,
            "payload": {
                "action": "post",
                "content": tweet,
                "platforms": ["twitter"]
            }
        }
        self.write_task(task)
        return tweet

    def _compose_weather_tweet(self, data: list) -> str:
        """Format: City: Temp, Conditions (X Nodes)."""
        lines = []
        for item in data[:3]:  # Top 3
            lines.append(
                f"{item['city']}: {item['temp']}°F, {item['conditions']} "
                f"({item['node_count']} Nodes)"
            )

        return (
            f"🌤️ Weather Check ({datetime.now().strftime('%I:%M %p')})\n" +
            "\n".join(lines) +
            f"\n#Backlink #WeatherOnThe8s"
        )

    def _fetch_weather_simulated(self, location: Dict) -> Dict:
        """Simulate fetching weather."""
        import random
        conditions = ["Clear", "Rain", "Cloudy", "Windy", "Snow"]
        return {
            "city": location["city"],
            "temp": random.randint(30, 90),
            "conditions": random.choice(conditions),
            "node_count": location.get("count", 0)
        }

    def _get_top_node_locations(self, intel: Dict) -> list:
        """Get top locations from intel."""
        # Simulated
        return [
            {"city": "New York", "count": 12},
            {"city": "London", "count": 8},
            {"city": "Tokyo", "count": 5}
        ]

    def _update_weather_intel(self, reports: list, snippet: str):
        """Update intel.json with latest weather."""
        intel = self.read_intel()
        intel["weather"] = {
            "reports": reports,
            "latest_snippet": snippet,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self._write_json("intel.json", intel)
