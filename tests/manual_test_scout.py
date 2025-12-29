import json
import os
import sys

# Add root to path so we can import hive
sys.path.append(os.getcwd())

from hive.bees.research.trend_scout_bee import TrendScoutBee


# Mocking the Gemini Client response for testing purposes
# In production, this would hit the real API
class MockGeminiClient:
    def generate_content(self, prompt, thinking_level="low", response_schema=None, tools=None):
        print(f"    [MOCK API] Received Prompt: {prompt[:50]}...")
        if tools and "google_maps_grounding" in str(tools):
            print("    [MOCK API] Detected Google Maps Grounding Tool")
            return {
                "text": json.dumps(
                    {
                        "venues": [
                            {
                                "title": "The White Horse",
                                "address": "500 Comal St, Austin, TX",
                                "rating": 4.7,
                                "place_id": "ChIJa_...",
                            },
                            {
                                "title": "Mohawk Austin",
                                "address": "912 Red River St, Austin, TX",
                                "rating": 4.6,
                                "place_id": "ChIJb...",
                            },
                        ]
                    }
                )
            }
        return {"text": "{}"}


def test_scout_venues():
    print("--- Testing TrendScoutBee: Venue Scouting ---")

    bee = TrendScoutBee()

    # Inject Mock Client
    bee.llm_client = MockGeminiClient()

    # Define task for just location
    task = {"categories": ["location"]}

    print("1. Starting Work (Source: trending_venues)...")
    bee.work(task)

    print("\n2. Reviewing Intel...")
    intel = bee.read_intel()
    current_trends = intel.get("trends", {}).get("current", [])

    venues = [t for t in current_trends if t["type"] == "venue"]

    if venues:
        print(f"SUCCESS: Found {len(venues)} venues.")
        for v in venues:
            print(f" - {v['title']} ({v['description']}) [Rating: {v['relevance']:.2f}]")
    else:
        print("FAILURE: No venues found in intel.")


if __name__ == "__main__":
    test_scout_venues()
