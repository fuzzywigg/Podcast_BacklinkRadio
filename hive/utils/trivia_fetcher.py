"""
Trivia Fetcher Utility.

Fetches trivia from various public APIs with failover support.
"""

import requests
import html
import random
from typing import List, Dict, Any, Optional

from hive.utils.keys import KeyManager


class TriviaFetcher:
    """
    Fetches trivia from configured providers.

    Supported Providers:
    - Open Trivia DB (opentdb.com)
    - Useless Facts (uselessfacts.jsph.pl)
    - API Ninjas (api-ninjas.com)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize with hive config.

        Args:
            config: The full hive configuration dictionary
        """
        self.config = config
        self.trivia_config = config.get("integrations", {}).get("trivia", {})
        self.key_manager = KeyManager()

        # Fallback static trivia
        self.static_backup = [
            {
                "type": "music",
                "text": "The first song played on MTV was 'Video Killed the Radio Star.' Ironic.",
                "use_after_genre": "rock"
            },
            {
                "type": "tech",
                "text": "The first radio broadcast was in 1906. We've been connecting nodes ever since.",
                "use_after_genre": None
            },
            {
                "type": "station",
                "text": "Commercial-free since day one. That's the Backlink promise.",
                "use_after_genre": None
            },
            {
                "type": "science",
                "text": "Honey bees communicate through a 'waggle dance' to share locations of food sources.",
                "use_after_genre": None
            }
        ]

    def fetch(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Fetch trivia items from enabled providers.

        Args:
            count: Number of items to try to return

        Returns:
            List of trivia items in internal format.
        """
        if not self.trivia_config.get("enabled", True):
            return self.static_backup[:count]

        providers = self.trivia_config.get("providers", [])
        # Shuffle providers to distribute load/variety
        # (Make a copy to not affect the config order permanently if we wanted strict priority)
        active_providers = [p for p in providers if p.get("enabled", True)]

        # We might want to try random providers or iterate in order.
        # Let's try to get content from them until we fill the count.

        results = []
        # Attempt to get results from random providers until we have enough
        # or run out of attempts.

        # Shuffle for variety
        random.shuffle(active_providers)

        for provider in active_providers:
            if len(results) >= count:
                break

            try:
                new_items = self._fetch_from_provider(provider, count - len(results))
                results.extend(new_items)
            except Exception as e:
                print(f"Error fetching from {provider['name']}: {e}")
                continue

        # Fill remaining slots with static backup if needed
        if len(results) < count:
            needed = count - len(results)
            # Pick random backup items
            results.extend(random.sample(self.static_backup, min(needed, len(self.static_backup))))

        return results[:count]

    def _fetch_from_provider(self, provider: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Dispatch to specific provider method."""
        name = provider.get("name")

        if name == "opentdb":
            return self._fetch_opentdb(count)
        elif name == "uselessfacts":
            return self._fetch_uselessfacts(count)
        elif name == "api_ninjas":
            return self._fetch_api_ninjas(provider, count)
        else:
            return []

    def _fetch_opentdb(self, count: int) -> List[Dict[str, Any]]:
        """Fetch from Open Trivia DB."""
        # OpenTDB allows up to 50 items.
        # URL: https://opentdb.com/api.php?amount=X

        url = "https://opentdb.com/api.php"
        params = {
            "amount": count,
            "type": "boolean"  # 'multiple' or 'boolean' or omit for mixed.
                               # Boolean (True/False) often makes for good "Did you know?" facts.
                               # Actually, let's use default (mixed) and format it appropriately.
        }

        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        items = []
        if data.get("response_code") == 0:
            for result in data.get("results", []):
                question = html.unescape(result.get("question", ""))
                correct_answer = html.unescape(result.get("correct_answer", ""))

                # Format as a fact or Q&A
                text = f"Trivia: {question} The answer is {correct_answer}."

                category = result.get("category", "General").lower()
                genre_map = self._map_category_to_genre(category)

                items.append({
                    "type": "trivia",
                    "text": text,
                    "use_after_genre": genre_map,
                    "source": "OpenTDB"
                })

        return items

    def _fetch_uselessfacts(self, count: int) -> List[Dict[str, Any]]:
        """Fetch from Useless Facts API."""
        # URL: https://uselessfacts.jsph.pl/api/v2/facts/random
        # Only returns 1 at a time usually.

        items = []
        url = "https://uselessfacts.jsph.pl/api/v2/facts/random"

        for _ in range(count):
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                data = resp.json()

                text = data.get("text", "")
                if text:
                    items.append({
                        "type": "fact",
                        "text": text,
                        "use_after_genre": None,
                        "source": "UselessFacts"
                    })
            except Exception:
                pass

        return items

    def _fetch_api_ninjas(self, provider_config: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        """Fetch from API Ninjas Facts API."""
        # Requires Key
        env_var = provider_config.get("api_key_env")
        if not env_var:
            return []

        api_key = self.key_manager.get_key(env_var)
        if not api_key:
            # Key not found, skip silently
            return []

        url = "https://api.api-ninjas.com/v1/facts"
        headers = {"X-Api-Key": api_key}
        params = {"limit": count}

        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for fact in data:
            text = fact.get("fact", "")
            if text:
                items.append({
                    "type": "fact",
                    "text": text,
                    "use_after_genre": None,
                    "source": "APINinjas"
                })

        return items

    def _map_category_to_genre(self, category: str) -> Optional[str]:
        """Map generic trivia categories to music genres for DJ flow."""
        category = category.lower()

        if "music" in category:
            if "rock" in category: return "rock"
            if "pop" in category: return "pop"
            return "any" # Generic music trivia is good for any music slot

        if "entertainment" in category: return None
        if "science" in category: return "electronic" # Sci-tech vibes
        if "computer" in category: return "electronic"
        if "history" in category: return None

        return None
