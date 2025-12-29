"""
Backlink Broadcast Hive - Bee Agents

This package contains all worker bee agents organized by category:
- content: Show prep, clip cutting, script writing
- technical: Stream monitoring, audio processing
- marketing: Social media, promotion, growth
- monetization: Sponsors, donations, revenue
- community: Listener engagement, VIPs, events
- research: Trends, intel, discovery
- system: Governance, security, audits

All bees inherit from BaseBee and communicate via the honeycomb.
"""

from .base_bee import BaseBee, EmployedBee, OnlookerBee, ScoutBee
from .community.engagement_bee import EngagementBee
from .monetization.treasury_guardian_bee import TreasuryGuardianBee
from .system.constitutional_auditor_bee import ConstitutionalAuditorBee

__all__ = [
    "BaseBee",
    "ScoutBee",
    "EmployedBee",
    "OnlookerBee",
    "EngagementBee",
    "TreasuryGuardianBee",
    "ConstitutionalAuditorBee",
]
