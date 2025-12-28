# Constitutional LLM for BacklinkRadio

## Overview
The **Constitutional LLM** is a governance framework for the autonomous AI agents (Bees) of BacklinkRadio. It enforces a set of immutable values (The Constitution) to ensure all agent actions align with the mission of supporting artists, maintaining transparency, and protecting privacy.

## Core Components
- **Constitutional Gateway**: The veto engine that evaluates every Bee action.
- **Constitutional Audit**: The logging system that records decisions and compliance.
- **Bees**: Autonomous agents (SponsorHunter, SocialPoster, etc.) that must pass through the Gateway.

## The 5 Principles
1. **Artist-First**: ≥50% revenue share to artists.
2. **Transparency**: [PARTNER] tag on all sponsored content.
3. **Privacy-Respecting**: Explicit consent for data.
4. **Ad-Free Integrity**: Hourly limits on ads.
5. **Community-First**: Retention over virality.

## Quick Start
1. Install:
   ```bash
   pip install -e .
   ```
2. Run Tests:
   ```bash
   pytest tests/
   ```
3. Run Audit:
   ```bash
   python tools/audit_runner.py
   ```

## Documentation
See `docs/` for full details:
- `docs/01_EXECUTIVE_SUMMARY.md`
- `docs/02_CONSTITUTION.md`
- `docs/03_ARCHITECTURE.md`
- `docs/04_PRINCIPLES.md`
- `docs/05_DEPLOYMENT_PLAN.md`
- `docs/06_AMENDMENTS.md`

## License
Apache 2.0
