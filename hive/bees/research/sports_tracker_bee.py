"""
Sports Tracker Bee - Track sports scores for node locations.

Responsibilities:
- Monitor games in cities where nodes are listening.
- Tweet final scores.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone

from hive.bees.base_bee import EmployedBee

class SportsTrackerBee(EmployedBee):
    """
    Tracks sports scores relevant to listeners.
    """

    BEE_TYPE = "sports_tracker"
    BEE_NAME = "Sports Tracker Bee"
    CATEGORY = "research"

    async def work(self, task: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute sports tracking.
        """
        self.log("Sports Bee tracking games...")

        # 1. Get Locations
        intel = self.read_intel()
        # Simulated check for locations

        # 2. Check Games (Simulated)
        game = self._check_games_simulated()

        if game and game['status'] == 'final':
            # Tweet
            tweet = self._compose_score_tweet(game)

            # Spawn social task
            social_task = {
                "type": "marketing",
                "bee_type": "social_poster",
                "priority": 6,
                "payload": {
                    "action": "post",
                    "content": tweet,
                    "platforms": ["twitter"]
                }
            }
            self.write_task(social_task)

            return {"status": "success", "tweet": tweet}

        return {"status": "no_games_final"}

    def _compose_score_tweet(self, game: Dict) -> str:
        return (
            f"📊 Final: {game['team1']} {game['score1']} - "
            f"{game['team2']} {game['score2']} | "
            f"{game['node_count']} Nodes were tuned in. #BacklinkSports"
        )

    def _check_games_simulated(self) -> Optional[Dict]:
        import random
        if random.random() > 0.8: # Occasional game end
            return {
                "team1": "Bears", "score1": 24,
                "team2": "Packers", "score2": 21,
                "status": "final",
                "node_count": 15
            }
        return None
