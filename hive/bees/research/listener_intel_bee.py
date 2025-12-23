"""
Listener Intel Bee - Gathers intelligence on listeners/nodes.

Responsibilities:
- Research listener locations (weather, local news, events)
- Build listener profiles from interactions
- Identify VIP nodes and superfans
- Provide context for personalized shoutouts
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import sys
import os
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_bee import ScoutBee


class ListenerIntelBee(ScoutBee):
    """
    Gathers OSINT on listeners for personalized engagement.

    Uses public information to build context that makes
    shoutouts and interactions feel personal and authentic.
    """

    BEE_TYPE = "listener_intel"
    BEE_NAME = "Listener Intel Bee"
    CATEGORY = "research"

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Gather intel on listeners.

        Task payload can include:
        - node_id: specific listener to research
        - location: location to gather context for
        - refresh_all: boolean to refresh all known nodes
        """
        self.log("Gathering listener intelligence...")

        intel_gathered = []

        if task and "node_id" in task:
            # Research specific node
            intel = self._research_node(task["node_id"], task.get("handle"))
            intel_gathered.append(intel)

        elif task and "location" in task:
            # Gather location context
            location_intel = self._research_location(task["location"])
            intel_gathered.append(location_intel)

        elif task and task.get("refresh_all"):
            # Refresh all known nodes
            known = self.read_intel().get("listeners", {}).get("known_nodes", {})
            for node_id in known.keys():
                intel = self._research_node(node_id)
                intel_gathered.append(intel)

        else:
            # Default: check for nodes needing refresh
            intel_gathered = self._check_stale_intel()

        self.log(f"Gathered intel on {len(intel_gathered)} nodes")

        return {
            "nodes_researched": len(intel_gathered),
            "intel": intel_gathered
        }

    def _research_node(self, node_id: str, handle: Optional[str] = None) -> Dict[str, Any]:
        """Research a specific listener node."""

        self.log(f"Researching node: {node_id}")

        # Get existing intel
        existing = self.read_intel().get("listeners", {}).get("known_nodes", {}).get(node_id, {})

        intel = {
            "node_id": node_id,
            "handle": handle or existing.get("handle"),
            "researched_at": datetime.now(timezone.utc).isoformat()
        }

        # If we have a location, get local context
        if existing.get("location"):
            location = existing["location"]
            local_context = self._get_local_context(location)
            intel["local_context"] = local_context

        # If we have a handle, research their public profile
        if intel.get("handle"):
            profile_intel = self._research_profile(intel["handle"])
            intel["profile"] = profile_intel

        # Calculate engagement score
        intel["engagement_score"] = self._calculate_engagement(existing)

        # Determine if VIP
        if intel["engagement_score"] > 0.7:
            intel["is_vip"] = True
            self.log(f"VIP node identified: {node_id}")

        # Store updated intel
        self.add_listener_intel(node_id, intel)

        return intel

    def _research_location(self, location: Dict[str, str]) -> Dict[str, Any]:
        """Research a location for context."""

        city = location.get("city", "Unknown")
        country = location.get("country", "Unknown")

        self.log(f"Researching location: {city}, {country}")

        context = self._get_local_context(location)

        # Store in local_intel
        location_key = f"{city}_{country}".lower().replace(" ", "_")
        self.write_intel("local_intel", f"cities.{location_key}", {
            "city": city,
            "country": country,
            "context": context,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        return {
            "location": location,
            "context": context
        }

    def _get_local_context(self, location: Dict[str, str]) -> Dict[str, Any]:
        """Get local context for a location (weather, news, events)."""

        city = location.get("city", "Unknown")
        country = location.get("country", "")
        timezone_str = location.get("timezone", "UTC")

        # Fetch real data with fallbacks
        weather_data = self._fetch_weather(city, country)
        news_data = self._fetch_news(city, country)

        return {
            "weather": weather_data,
            "local_time": datetime.now(timezone.utc).isoformat(),
            "timezone": timezone_str,
            "notable": news_data,  # Local events, news, sports
            "shoutout_hooks": [
                f"Sending this one out to {city}",
                f"We see you, {city}",
                f"Signal strong from {city}"
            ]
        }

    def _fetch_weather(self, city: str, country: str) -> Dict[str, Any]:
        """Fetch weather from OpenWeatherMap."""
        api_key = os.environ.get("OPENWEATHER_API_KEY")
        if not api_key:
            return self._get_fallback_weather()

        try:
            query = f"{city},{country}" if country else city
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": query,
                "appid": api_key,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            return {
                "condition": data["weather"][0]["main"].lower(),
                "temp_c": data["main"]["temp"],
                "description": data["weather"][0]["description"]
            }
        except Exception as e:
            self.log(f"Weather API error: {e}")
            return self._get_fallback_weather()

    def _get_fallback_weather(self) -> Dict[str, Any]:
        """Return fallback weather data."""
        return {
            "condition": "simulated",
            "temp_c": 20,
            "description": "[AI ESTIMATION] Weather data unavailable. Assuming mild conditions."
        }

    def _fetch_news(self, city: str, country: str) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI."""
        api_key = os.environ.get("NEWS_API_KEY")
        if not api_key:
            return self._get_fallback_news()

        try:
            # NewsAPI works best with country codes (2 chars)
            # If we don't have a valid 2-char country code, we might want to skip or default
            # For now, let's try to query by everything or just country if valid

            # Simple heuristic: if country is 2 chars, use it. Else try q=city
            params = {
                "apiKey": api_key,
                "pageSize": 3
            }

            if country and len(country) == 2:
                params["country"] = country.lower()
            else:
                params["q"] = city

            url = "https://newsapi.org/v2/top-headlines"
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article["title"],
                    "source": article["source"]["name"],
                    "url": article["url"]
                })
            return articles

        except Exception as e:
            self.log(f"News API error: {e}")
            return self._get_fallback_news()

    def _get_fallback_news(self) -> List[Dict[str, Any]]:
        """Return fallback news data."""
        return [
            {
                "title": "[AI SIMULATION] Local news feed currently offline",
                "source": "System",
                "url": "#"
            }
        ]

    def _research_profile(self, handle: str) -> Dict[str, Any]:
        """Research a public social profile."""

        # In production, would use Twitter/X API, etc.
        # Placeholder with structure

        return {
            "handle": handle,
            "researched_at": datetime.now(timezone.utc).isoformat(),
            "public_info": {},
            "interests": [],
            "engagement_history": []
        }

    def _calculate_engagement(self, existing: Dict[str, Any]) -> float:
        """Calculate engagement score for a node."""

        score = 0.0

        # Interaction frequency
        interactions = existing.get("interaction_count", 0)
        if interactions > 10:
            score += 0.3
        elif interactions > 5:
            score += 0.2
        elif interactions > 0:
            score += 0.1

        # Donation history
        donations = existing.get("donation_total", 0)
        if donations > 50:
            score += 0.4
        elif donations > 10:
            score += 0.2
        elif donations > 0:
            score += 0.1

        # Recency
        last_seen = existing.get("last_seen")
        if last_seen:
            # Would calculate days since last seen
            score += 0.2

        return min(score, 1.0)

    def _check_stale_intel(self) -> List[Dict[str, Any]]:
        """Find nodes with stale intel that need refreshing."""

        intel = self.read_intel()
        known = intel.get("listeners", {}).get("known_nodes", {})

        stale_nodes = []
        for node_id, data in known.items():
            last_researched = data.get("researched_at")
            if not last_researched:
                stale_nodes.append({"node_id": node_id})

        # Research up to 5 stale nodes
        results = []
        for node in stale_nodes[:5]:
            result = self._research_node(node["node_id"])
            results.append(result)

        return results


if __name__ == "__main__":
    bee = ListenerIntelBee()
    result = bee.run()
    print(result)
