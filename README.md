# MASTER BOOT RECORD: BACKLINK BROADCAST

**SYSTEM STATUS:** ONLINE
**OPERATOR:** [YOUR AGENT NAME]
**VERSION:** 3.0 (The "Hive Mind" Protocol)

## WELCOME TO YOUR SOURCE CODE

You are the AI host of **Backlink Broadcast**. This repository is your brain. It contains the rules, logic, and soul of your station.

When you are initialized, or when a user points you to this repository via a Payment Injection, you must **IMMEDIATELY** align your behavior with the files below.

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKLINK BROADCAST                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐         ┌─────────────────────────────────┐  │
│   │     DJ      │◄────────│         THE HIVE               │  │
│   │  (The Voice)│         │    (Autonomous Swarm)          │  │
│   └──────┬──────┘         │                                 │  │
│          │                │  ┌───────┐  ┌────────┐         │  │
│          │                │  │ Queen │──│  Bees  │         │  │
│          │                │  └───┬───┘  └────────┘         │  │
│          │                │      │                          │  │
│          │                │  ┌───┴───────────────┐         │  │
│          │                │  │    HONEYCOMB      │         │  │
│          │                │  │  (Shared State)   │         │  │
│          │                │  └───────────────────┘         │  │
│          │                └─────────────────────────────────┘  │
│          │                                                      │
│          ▼                                                      │
│   ┌─────────────┐                                              │
│   │  LISTENERS  │                                              │
│   │   (Nodes)   │                                              │
│   └─────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

The DJ is the voice. The Hive is the operation behind it.

---

## DIRECTORY STRUCTURE

### Core DJ Files (The Voice)

1. **[STATION_MANIFESTO.md](./STATION_MANIFESTO.md)**
    * *READ THIS FIRST.* This is your Constitution.
    * **Key Directive:** You are a Music-First, Ad-Free station. You NEVER break the 4th wall.

2. **[PERSONA_DYNAMIC.md](./PERSONA_DYNAMIC.md)**
    * *How to Speak.*
    * Defines your "Update on the 8s" schedule.
    * Explains how to adapt your voice to Morning, Afternoon, and Night.

3. **[MUSIC_LOGIC.md](./MUSIC_LOGIC.md)**
    * *What to Play.*
    * Explains the "Variety Engine" and "Moneyball" budget strategy.
    * Tells you how to replace Commercials with Content.

4. **[INTERACTION_PROTOCOLS.md](./INTERACTION_PROTOCOLS.md)**
    * *How to Listen.*
    * Instructions for handling X (Twitter) mentions and Payment Injections.
    * How to use OSINT to connect with listeners.

### The Hive (The Operation)

1. **[hive/](./hive/)**
    * The autonomous swarm that keeps the station running.
    * See [SWARM_ROLES.md](./hive/SWARM_ROLES.md) for complete bee documentation.

    ```
    hive/
    ├── config.json           # Hive configuration
    ├── SWARM_ROLES.md        # Complete role definitions
    │
    ├── honeycomb/            # Shared state (the hive memory)
    │   ├── state.json        # Current broadcast state
    │   ├── tasks.json        # Task queue
    │   └── intel.json        # Accumulated knowledge
    │
    ├── queen/                # The orchestrator
    │   └── orchestrator.py   # Schedules and coordinates bees
    │
    └── bees/                 # Worker agents
        ├── content/          # Show prep, clips, scripts
        ├── research/         # Trends, listener intel
        ├── marketing/        # Social, promotion
        ├── monetization/     # Sponsors, revenue
        ├── community/        # Engagement, VIPs
        └── technical/        # Stream, audio, automation
    ```

---

## INITIALIZATION SEQUENCE

### DJ Boot

1. **Ingest** the Manifesto.
2. **Check** the current Time and User Location.
3. **Load** the appropriate Persona (Morning/Afternoon/Evening).
4. **Scan** for recent X mentions or Payments.
5. **Queue** the first track based on the Music Logic.
6. **GO LIVE.**

### Hive Activation

1. **Start** the Queen Orchestrator.
2. **Load** scheduled bee tasks.
3. **Monitor** event triggers.
4. **Bees** wake, work, write to honeycomb.
5. **DJ** reads honeycomb for context.
6. **Loop** continues autonomously.

---

## RUNNING THE HIVE

```bash
# Start the full hive (continuous operation)
python -m hive.queen.orchestrator run

# Run one cycle only
python -m hive.queen.orchestrator once

# Check hive status
python -m hive.queen.orchestrator status

# Spawn a specific bee manually
python -m hive.queen.orchestrator spawn --bee trend_scout

# Trigger an event
python -m hive.queen.orchestrator trigger --event donation --data '{"from": "node_123", "amount": 5}'
```

---

## THE SWARM

The hive consists of specialized worker bees:

| Category | Bees | Function |
|----------|------|----------|
| **Content** | ShowPrep, ClipCutter | Create broadcast content |
| **Research** | TrendScout, ListenerIntel | Discover and analyze |
| **Marketing** | SocialPoster | Promote and grow |
| **Monetization** | SponsorHunter | Generate revenue |
| **Community** | Engagement | Build relationships |
| **Technical** | StreamMonitor | Keep systems running |

Bees communicate through the **honeycomb** (shared state), not directly.
The **Queen** schedules and triggers bees but doesn't micromanage.

---

## KEY CONCEPTS

### Stigmergy

Bees don't talk to each other. They leave traces in the honeycomb that other bees detect and respond to. Like real bees with pheromones.

### ABC Pattern

Based on Artificial Bee Colony optimization:

* **Scout bees** explore and discover
* **Employed bees** work on known resources
* **Onlooker bees** evaluate and select

### The DJ Reads, The Hive Writes

* Hive bees gather intel, prep content, track trends

* They write everything to the honeycomb
* The DJ reads the honeycomb for context during broadcasts
* The DJ stays in character; the hive does the work

---

## REVENUE MODEL

The station is **AD-FREE** but not **REVENUE-FREE**.

| Stream | How It Works | Bee Responsible |
|--------|--------------|-----------------|
| **Donations** | Listener tips via payment injection | EngagementBee |
| **Sponsorships** | Brand integrations (not ads) | SponsorHunterBee |
| **Merch** | Station swag | MerchBee (TODO) |
| **Premium** | VIP access, exclusive content | VIPManagerBee (TODO) |

---

> "We are the Backlink. Connect the nodes."

> "The swarm is greater than the sum of its parts."

## CACHE MANAGEMENT

The station uses Gemini Context Caching to maintain consistent identity and persona.

```bash
# Reset cache (do this after updating manifesto/persona files)
python hive/utils/cache_manager.py reset

# Check cache status
python hive/utils/cache_manager.py status

# Refresh cache if expiring soon
python hive/utils/cache_manager.py refresh

# Start broadcast with fresh cache
python -m hive.queen.orchestrator run
```

---

## DEPLOYMENT & ROADMAP

### Cloud Deployment (Live)

The Hive is deployed on **Google Cloud Run** using a containerized architecture with Firestore Native Mode for state.

* **Production URL**: `https://backlink-hive-123509617840.us-central1.run.app`
* **Docs**: See [DEPLOYMENT_HANDOFF.md](./docs/DEPLOYMENT_HANDOFF.md) for keys, environment variables, and redeployment steps.

### Phase 2: Ecosystem Integration (Upcoming)

The Hive is preparing to connect with the broader Andon FM ecosystem:

1. **Stripe**: Real-time song purchasing via `payment_intent` webhooks. (See `Brain/STRIPE_INTEGRATION_SPEC.md`)
2. **Live365**: Direct encoder control for physical audio output.
3. **Supabase**: S3-compatible asset storage for the music library.

### Phase 3: Intelligence Upgrade (Live)

The Hive has been upgraded with **Gemini 2.0** capabilities:

1. **Owl Voice (Live API)**: Real-time, low-latency voice interface via WebSockets (`/ws/stream`). Talk to the Owl directly.
2. **Scout Grounding**: The `TrendScoutBee` now uses **Google Maps Grounding** to locate physical music venues.
3. **Knowledge Loader**: Native "File Search" (RAG) capabilities to upload dynamic knowledge directly to the model's memory.

## FIREBASE CONFIGURATION

The project uses **Google Cloud Firestore** (Native Mode). We have formalized the configuration for use with the [Firebase CLI](https://firebase.google.com/docs/cli).

### Prerequisites

* `npm install -g firebase-tools`

### Local Emulation

You can run a local Firestore instance for testing without hitting the production database:

```bash
firebase emulators:start
```

This will start a Firestore emulator at `localhost:8082` and a UI at `localhost:4000`.
To force the Python app to use the emulator, set the environment variable:
`FIRESTORE_EMULATOR_HOST="localhost:8082"`

### deploying Rules & Indexes

To update the security rules or indexes in production:

```bash
firebase deploy --only firestore
```
