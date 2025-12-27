"""
Backlink Broadcast Hive - Bee Agents

This package contains all worker bee agents organized by category:
- content: Show prep, clip cutting, script writing
- technical: Stream monitoring, audio processing
- marketing: Social media, promotion, growth
- monetization: Sponsors, donations, revenue
- community: Listener engagement, VIPs, events
- research: Trends, intel, discovery

All bees inherit from BaseBee and communicate via the honeycomb.
"""

from .base_bee import BaseBee, ScoutBee, EmployedBee, OnlookerBee

__all__ = [
    "BaseBee",
    "ScoutBee",
    "EmployedBee",
    "OnlookerBee"
]
