# CLAUDE.md - Backlink Broadcast Hive

## Project Overview

Backlink Broadcast is an AI-powered autonomous radio station built on swarm intelligence. Autonomous agent "bees" coordinate through shared state (the "honeycomb") using stigmergy - indirect communication via environment changes.

**Mission**: Keep the station online, profitable, engaging, and fresh - 24/7 autonomous operation.

## Tech Stack

- **Language**: Python 3.10-3.12
- **Web Framework**: FastAPI + Uvicorn
- **LLM**: Google Gemini 2.0 Flash (`google-genai`)
- **Database**: Google Cloud Firestore (Native Mode) or local JSON files
- **State Integrity**: HMAC-SHA256 signing
- **Knowledge Graph**: cognee + networkx
- **External APIs**: Twitter/X, Google Maps, Plausible Analytics
- **Deployment**: Google Cloud Run (containerized)

## Quick Commands

```bash
# Install
make install          # Production deps
make install-dev      # All dev deps

# Test
make test             # pytest with coverage
make test-fast        # pytest without coverage
pytest -m unit        # Unit tests only

# Code Quality
make lint             # ruff check
make format           # ruff format
make type-check       # mypy
make pre-commit       # All pre-commit hooks

# Run the Hive
make run              # Continuous operation
make run-once         # Single cycle
make status           # Check hive status

# Specific Bee
python -m hive.queen.orchestrator spawn --bee trend_scout

# Web Service
uvicorn hive.main_service:app --host 0.0.0.0 --port 8080
```

## Project Structure

```
hive/
├── queen/orchestrator.py     # Central coordinator, bee lifecycle
├── bees/                     # Worker agents by category
│   ├── base_bee.py           # Abstract base class (ScoutBee, EmployedBee, OnlookerBee)
│   ├── content/              # ShowPrepBee, ClipCutterBee, DJBee
│   ├── research/             # TrendScoutBee, ListenerIntelBee, WeatherBee
│   ├── marketing/            # SocialPosterBee, DAOUpdateBee
│   ├── monetization/         # SponsorHunterBee, TreasuryGuardianBee, etc.
│   ├── community/            # EngagementBee
│   ├── technical/            # StreamMonitorBee, RadioPhysicsBee
│   └── system/               # ConstitutionalAuditorBee
├── honeycomb/                # Shared state files
│   ├── state.json            # Current broadcast state
│   ├── intel.json            # Accumulated knowledge
│   ├── tasks.json            # Task queue
│   └── wisdom.json           # Long-term knowledge
├── utils/                    # Utilities
│   ├── state_manager.py      # HMAC-secured honeycomb access
│   ├── storage_adapter.py    # File/Firestore abstraction
│   ├── gemini_client.py      # Gemini 2.0 integration
│   └── ...
└── config.json               # Hive configuration

constitutional_llm/           # Governance layer
├── src/constitutional_gateway.py  # Core governance engine
└── config/constitution.json       # Ethical constraints
```

## Key Patterns

### Stigmergy Pattern
Bees never communicate directly. All communication via honeycomb:
```python
state = self.read_state()    # Read from honeycomb
result = process(state)      # Do work
self.write_state({"key": result})  # Write back
```

### ABC (Artificial Bee Colony) Pattern
- **ScoutBee**: Explore, discover new information
- **EmployedBee**: Work on known resources, produce output
- **OnlookerBee**: Evaluate and select winners

### Creating a New Bee
```python
from hive.bees.base_bee import ScoutBee

class MyBee(ScoutBee):
    BEE_TYPE = "my_bee"
    BEE_NAME = "My Bee"
    CATEGORY = "research"

    def work(self, task: dict[str, Any] | None = None) -> dict[str, Any]:
        state = self.read_state()
        intel = self.read_intel()
        # Process and return results
        return {"status": "success", "data": result}
```

## Code Standards

- **Type Hints**: Full annotations required (mypy strict)
- **Docstrings**: Google-style for all public functions
- **Tool Outputs**: JSON format, not Python code blocks
- **Logging**: Use `self.logger` or `self.log()` methods
- **Naming**:
  - Bee files: `{name}_bee.py`
  - Bee classes: `{NameCamelCase}Bee`
  - Constants: `UPPER_SNAKE_CASE`

## Pre-commit Hooks

Enabled: ruff, mypy, bandit (security), markdownlint, detect-secrets

Run before committing: `make pre-commit`

## Environment Variables

```bash
GCP_PROJECT_ID=andon-backlink-hive-prod
STORAGE_TYPE=FILE  # or FIRESTORE
GOOGLE_API_KEY=your_gemini_key
HIVE_SECRET_KEY=generate_a_uuid_here
FIRESTORE_EMULATOR_HOST=localhost:8082  # For local testing
```

## Key Files

| File | Purpose |
|------|---------|
| `hive/config.json` | Schedules, integrations, bee configs |
| `hive/SWARM_ROLES.md` | Complete bee role definitions |
| `hive/bees/base_bee.py` | Base class for all bees |
| `hive/queen/orchestrator.py` | Main orchestration logic |
| `pyproject.toml` | Dependencies and tool config |
| `Makefile` | All development commands |
| `.pre-commit-config.yaml` | Git hooks configuration |

## Testing

```bash
# Standard test run
pytest --cov=hive --cov-report=html

# Markers
pytest -m unit         # Unit tests
pytest -m integration  # Integration tests
pytest -m slow         # Slow tests

# Specific module
pytest hive/tests/test_base_bee.py
```

## Commit Convention

- **Title**: In-universe voice ("Tune the frequencies for Morning Show")
- **Body**: Technical details
- Two modes: Public stage vs backstage transparency

## Deployment

- **Production**: Cloud Run at `https://backlink-hive-*.run.app`
- **Local**: `docker-compose -f docker-compose.sovereign.yaml up`
- **CI/CD**: GitHub Actions (lint, test on 3.10/3.11/3.12, security scan, build)
