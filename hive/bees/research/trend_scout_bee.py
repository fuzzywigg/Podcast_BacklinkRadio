"""
Trend Scout Bee - Discovers trending topics and music.

Responsibilities:
- Monitor social platforms for trending topics
- Track music charts and viral tracks
- Identify cultural moments worth mentioning on air
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from hive.utils.prompt_engineer import PromptEngineer
import asyncio

from hive.bees.base_bee import ScoutBee


class TrendScoutBee(ScoutBee):
    """
    Scouts for trending content and cultural moments.

    Explores social platforms, music charts, and news to find
    content worth incorporating into broadcasts.
    """

    BEE_TYPE = "trend_scout"
    BEE_NAME = "Trend Scout Bee"
    CATEGORY = "research"

    # Sources to monitor
    SOURCES = [
        {"name": "twitter_trending", "type": "social", "priority": "high"},
        {"name": "spotify_viral", "type": "music", "priority": "high"},
        {"name": "reddit_music", "type": "community", "priority": "medium"},
        {"name": "music_news", "type": "industry", "priority": "medium"},
        {"name": "cultural_moments", "type": "zeitgeist", "priority": "high"}
    ]

    def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scout for trends across configured sources.

        Task payload can include:
        - sources: specific sources to check
        - categories: music|social|cultural|all
        """
        self.log("Beginning trend reconnaissance...")

        discovered_trends = []

        categories = ["all"]
        if task and "categories" in task:
            categories = task["categories"]

        # Scout each source
        for source in self.SOURCES:
            if "all" in categories or source["type"] in categories:
                trends = self._scout_source(source)
                discovered_trends.extend(trends)

        # Evaluate and rank trends
        ranked_trends = self._rank_trends(discovered_trends)

        # Update intel directly to avoid merge issues with lists
        intel = self.read_intel()

        # Initialize structure if missing
        if "trends" not in intel:
            intel["trends"] = {"current": [], "archive": []}

        # Archive old trends
        current_trends = intel["trends"].get("current", [])
        if current_trends:
            intel["trends"]["archive"].extend(
                current_trends[:5])  # Archive top 5 old ones

        # Set new current trends
        intel["trends"]["current"] = ranked_trends[:10]  # Top 10

        # Update timestamp
        intel["trends"]["last_scan"] = datetime.now(timezone.utc).isoformat()
        intel["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Write full intel object back
        self._write_json("intel.json", intel)

        # Check for Breaking News (Task extension)
        if task and task.get("payload", {}).get(
                "action") == "monitor_breaking_news":
            # Running async method in sync context
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.monitor_breaking_news())
            except RuntimeError:
                asyncio.run(self.monitor_breaking_news())
        if task and task.get("payload", {}).get("action") == "monitor_breaking_news":
             # Fix: asyncio.run for async method in synchronous work()
             try:
                 asyncio.run(self.monitor_breaking_news())
             except Exception as e:
                 self.log(f"Error running async breaking news monitor: {e}", level="error")

        # Alert DJ if high-priority trend found
        hot_trends = [
            t for t in ranked_trends if t.get("priority") == "urgent"]
        if hot_trends:
            self.post_alert(
                f"Hot trend detected: {hot_trends[0]['title']}",
                priority=True
            )

        self.log(
            f"Discovered {
                len(discovered_trends)} trends, {
                len(hot_trends)} hot")

        return {
            "trends_found": len(discovered_trends),
            "top_trends": ranked_trends[:5],
            "hot_trends": hot_trends
        }

    def monitor_breaking_news(self):
        """
        Detect breaking news relevant to node locations
        """
        # Monitor news APIs (simulated)
        news_items = self._fetch_breaking_news_simulated()

        # Filter for relevance (simulated)
        relevant = news_items  # Assume all relevant for demo

        for item in relevant:
            # Tweet immediately via SocialPoster
            tweet_text = self._compose_news_tweet(item)
            task = {
                "type": "marketing",
                "bee_type": "social_poster",
                "priority": 9,
                "payload": {
                    "action": "post",
                    "content": tweet_text,
                    "platforms": ["twitter"]
                }
            }
            self.write_task(task)

            # Queue for on-air mention (if major)
            if item.get('severity') == 'high':
                script = self._compose_news_brief(item)
                # Update intel for DJ
                intel = self.read_intel()
                if "breaking_news" not in intel:
                    intel["breaking_news"] = []
                intel["breaking_news"].append({
                    "script": script,
                    # + 1 hour usually
                    "expires_at": datetime.now(timezone.utc).isoformat()
                })
                self._write_json("intel.json", intel)

    def _compose_news_brief(self, news_item: Dict) -> str:
        """
        On-air breaking news (15 seconds max)
        """
        pe = PromptEngineer(
            role="News Anchor",
            goal="Write a 15-second radio script for breaking news."
        )
        pe.add_context(f"News Item: {news_item}")
        pe.add_constraint("LENGTH: Under 40 words. 15 seconds read time.")
        pe.add_constraint("TONE: Serious but fast-paced.")
        pe.set_output_format('{"script": "The spoken text"}')
        
        result = self._ask_llm_json(pe, "Draft radio brief.")
        return result.get("script", "")

    def _compose_news_tweet(self, news_item: Dict) -> str:
        """Compose a breaking news tweet using specific framing."""
        if not self.llm_client:
             # Fallback
             return f"🚨 Signal Intel: {news_item['headline']} | More: {news_item.get('url', 'backlink.radio')}"

        pe = PromptEngineer(
            role="News Curation Bot",
            goal="Compose a tweet for breaking news relative to the station's lore."
        )
        pe.add_context(f"News Item: {news_item}")
        pe.add_constraint("LENGTH: Max 280 chars.")
        pe.add_constraint("TONE: Urgent, Tech-focused, 'Signal' terminology.")
        pe.add_constraint("FORMAT: Output JSON with 'tweet_text'.")
        
        pe.set_output_format('{"tweet_text": "The tweet content"}')
        
        result = self._ask_llm_json(pe, "Draft tweet.")
        return result.get("tweet_text", "")

    def _fetch_breaking_news_simulated(self) -> list:
        import random
        if random.random() > 0.95:  # Rare event
            return [{
                "headline": "Major Solar Flare Detected",
                "source": "NASA",
                "severity": "high",
                "affected_nodes": 50,
                "url": "nasa.gov"
            }]
        return []

    def _scout_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scout a specific source for trends."""

        # In production, this would call actual APIs
        # For now, return structured placeholders

        source_name = source["name"]

        if source["type"] == "music":
            return self._scout_music_trends(source_name)
        elif source["type"] == "social":
            return self._scout_social_trends(source_name)
        elif source["type"] == "zeitgeist":
            return self._scout_cultural_moments(source_name)

        return []

    def _scout_music_trends(self, source: str) -> List[Dict[str, Any]]:
        """Scout music-specific trends."""

        # Placeholder - would integrate with Spotify/Apple Music APIs
        return [
            {
                "source": source,
                "type": "music",
                "title": "New viral track emerging",
                "description": "Track gaining momentum on streaming platforms",
                "relevance": 0.8,
                "priority": "normal",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "actionable": True,
                "action_suggestion": "Consider adding to playlist rotation"
            }
        ]

    def _scout_social_trends(self, source: str) -> List[Dict[str, Any]]:
        """Scout social media trends."""

        # Placeholder - would integrate with Twitter/X API
        return [
            {
                "source": source,
                "type": "social",
                "title": "Music-related hashtag trending",
                "description": "Community discussion around music topic",
                "relevance": 0.6,
                "priority": "normal",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "actionable": True,
                "action_suggestion": "Potential talking point for broadcast"
            }
        ]

    def _scout_cultural_moments(self, source: str) -> List[Dict[str, Any]]:
        """Scout broader cultural moments."""

        # Placeholder - would aggregate news and cultural feeds
        return [
            {
                "source": source,
                "type": "cultural",
                "title": "Cultural moment detected",
                "description": "Significant event in music/entertainment",
                "relevance": 0.7,
                "priority": "normal",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "actionable": True,
                "action_suggestion": "Worth mentioning on air if relevant"
            }
        ]

    def _rank_trends(
            self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank trends by relevance and priority."""

        def score(trend):
            relevance = trend.get("relevance", 0.5)
            priority_weights = {
                "urgent": 1.0,
                "high": 0.8,
                "normal": 0.5,
                "low": 0.2}
            priority_score = priority_weights.get(
                trend.get("priority", "normal"), 0.5)
            return relevance * 0.6 + priority_score * 0.4

        return sorted(trends, key=score, reverse=True)


if __name__ == "__main__":
    bee = TrendScoutBee()
    result = bee.run()
    print(result)
