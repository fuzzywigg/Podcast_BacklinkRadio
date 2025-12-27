# SWARM ROLES: The Complete Hive Workforce

**VERSION:** 1.0
**LAST UPDATED:** 2024

This document defines every worker bee role in the Backlink Broadcast hive. Each bee is autonomous, reads/writes to the honeycomb, and serves the greater mission of keeping the station online and profitable.

---

## THE THREE BEE TYPES (ABC Pattern)

Based on the Artificial Bee Colony optimization algorithm:

| Type | Role | Behavior |
|------|------|----------|
| **Scout** | Discovery | Explores, finds new things, brings back intel |
| **Employed** | Production | Works on known resources, produces output |
| **Onlooker** | Evaluation | Watches, evaluates, selects winners |

---

## CONTENT CREATION BEES

### ShowPrepBee (Employed)
- **Duration:** 30 min - 2 hours
- **Schedule:** Every 30 minutes
- **Inputs:** Listener intel, current trends, time of day
- **Outputs:** Talking points, shoutout scripts, trivia
- **Writes to:** `state.json` → `show_prep`

### ClipCutterBee (Employed)
- **Duration:** Minutes
- **Schedule:** Hourly or on-demand
- **Inputs:** Broadcast recordings, timestamps
- **Outputs:** Clip metadata, social post queue
- **Writes to:** `tasks.json` → new tasks for SocialPosterBee

### ScriptWriterBee (Employed) *[TODO]*
- **Duration:** Hours
- **Function:** Write comedy bits, recurring segments
- **Outputs:** Segment scripts, bit outlines

### JingleBee (Employed) *[TODO]*
- **Duration:** Hours - Days
- **Function:** Create station IDs, drops, bumpers
- **Outputs:** Audio assets, cue sheets

---

## RESEARCH & DISCOVERY BEES

### TrendScoutBee (Scout)
- **Duration:** Minutes
- **Schedule:** Hourly
- **Inputs:** Social APIs, music charts, news feeds
- **Outputs:** Trend reports, hot alerts
- **Writes to:** `intel.json` → `trends`

### ListenerIntelBee (Scout)
- **Duration:** Minutes
- **Schedule:** Every 5 minutes
- **Inputs:** Listener locations, public profiles
- **Outputs:** Local context, weather, news
- **Writes to:** `intel.json` → `listeners`

### MusicDiscoveryBee (Scout) *[TODO]*
- **Duration:** Hours
- **Function:** Find new tracks, deep cuts, emerging artists
- **Outputs:** Track recommendations, artist profiles

### CompetitorWatchBee (Scout) *[TODO]*
- **Duration:** Daily
- **Function:** Monitor other stations, podcasts
- **Outputs:** Competitive intel, opportunity gaps

---

## MARKETING & GROWTH BEES

### SocialPosterBee (Employed)
- **Duration:** Minutes
- **Schedule:** Every 15 minutes
- **Inputs:** Clips, content queue, post schedule
- **Outputs:** Posted content, engagement metrics
- **Writes to:** `intel.json` → `content_performance`

### SEOBee (Employed) *[TODO]*
- **Duration:** Days
- **Function:** Optimize discoverability, metadata
- **Outputs:** SEO recommendations, tag suggestions

### ViralAnalystBee (Onlooker) *[TODO]*
- **Duration:** Ongoing
- **Function:** Track what's spreading, identify patterns
- **Outputs:** Viral potential scores, timing recommendations

### NewsletterBee (Employed) *[TODO]*
- **Duration:** Weekly
- **Function:** Write and send email digests
- **Outputs:** Newsletter drafts, send confirmations

---

## MONETIZATION BEES

### SponsorHunterBee (Scout)
- **Duration:** Hours - Days
- **Schedule:** Daily
- **Inputs:** Brand databases, industry contacts
- **Outputs:** Prospect lists, pitch drafts
- **Writes to:** `intel.json` → `sponsors`

### DonationProcessorBee (Employed) ✓
- **Duration:** Immediate
- **Trigger:** On donation event
- **Function:** Process payment, trigger thank-you
- **Outputs:** Receipt, shoutout queue
- **Security:** Wallet validation, fraud detection, message sanitization
- **File:** `hive/bees/monetization/donation_processor_bee.py`

### MerchBee (Employed) *[TODO]*
- **Duration:** Ongoing
- **Function:** Design merch, manage inventory
- **Outputs:** Product listings, fulfillment tasks

### RevenueAnalystBee (Onlooker) ✓
- **Duration:** Daily/Weekly
- **Function:** Track revenue streams, identify opportunities
- **Outputs:** Revenue reports, forecasts, health scores
- **Reads:** `treasury_events.jsonl` (append-only log)
- **File:** `hive/bees/monetization/revenue_analyst_bee.py`

---

## COMMUNITY & ENGAGEMENT BEES

### EngagementBee (Employed)
- **Duration:** Minutes
- **Schedule:** Every 10 minutes
- **Inputs:** Mentions, donations, feedback
- **Outputs:** Responses, shoutout queue
- **Writes to:** `state.json` → `pending_shoutouts`

### VIPManagerBee (Onlooker) ✓
- **Duration:** Daily
- **Function:** Identify and nurture superfans via engagement scoring
- **Outputs:** VIP tier assignments, perk triggers, reports
- **Tiers:** Bronze, Silver, Gold, Platinum
- **File:** `hive/bees/community/vip_manager_bee.py`

### GiveawayBee (Employed) *[TODO]*
- **Duration:** Event-based
- **Function:** Run contests, select winners
- **Outputs:** Winner announcements, prize fulfillment

### ModeratorBee (Onlooker) ✓
- **Duration:** Continuous (every 5 min)
- **Function:** Filter toxicity, detect spam, enforce rules
- **Outputs:** Ban/mute/watch lists, moderation reports
- **Security:** Prompt injection detection, hate speech filtering
- **File:** `hive/bees/community/moderator_bee.py`

### LocalLiaisonBee (Scout) *[TODO]*
- **Duration:** Weekly
- **Function:** Connect with local businesses, events
- **Outputs:** Partnership opportunities, event calendar

---

## TECHNICAL & ENGINEERING BEES

### StreamMonitorBee (Onlooker)
- **Duration:** Continuous
- **Schedule:** Every minute
- **Inputs:** Stream endpoints, audio levels
- **Outputs:** Health reports, alerts
- **Writes to:** `state.json` → `health`

### AudioEngineerBee (Employed) *[TODO]*
- **Duration:** Ongoing
- **Function:** Process audio, normalize levels
- **Outputs:** Processed audio files

### AutomationBee (Employed) *[TODO]*
- **Duration:** Ongoing
- **Function:** Handle dead air, playlist transitions
- **Outputs:** Automation logs, failsafe triggers

### ArchivistBee (Employed) ✓
- **Duration:** Daily
- **Function:** Backup content, maintain searchable archive
- **Outputs:** Archive indexes, backup confirmations, integrity checks
- **Retention:** Category-based (90-730 days)
- **File:** `hive/bees/technical/archivist_bee.py`

### IntegrationBee (Employed) *[TODO]*
- **Duration:** On-demand
- **Function:** Connect APIs, manage webhooks
- **Outputs:** Integration status, error logs

---

## NETWORKING & RELATIONSHIPS BEES

### ArtistRelationsBee (Scout) *[TODO]*
- **Duration:** Days - Weeks
- **Function:** Build artist relationships, get exclusives
- **Outputs:** Contact database, interview bookings

### GuestBookerBee (Scout) *[TODO]*
- **Duration:** Days - Weeks
- **Function:** Find and book guests
- **Outputs:** Guest calendar, prep materials

### CollaborationBee (Scout) *[TODO]*
- **Duration:** Weeks
- **Function:** Find cross-promotion opportunities
- **Outputs:** Partnership proposals, collab calendar

---

## ADMIN & OPERATIONS BEES

### LicensingBee (Employed) *[TODO]*
- **Duration:** Ongoing
- **Function:** Track music rights, manage ASCAP/BMI
- **Outputs:** License status, compliance reports

### AnalyticsBee (Onlooker) ✓
- **Duration:** Hourly (dashboard), Daily (reports)
- **Function:** Aggregate metrics, generate KPI dashboards
- **Outputs:** Dashboard data, trend analysis, KPI alerts
- **KPIs:** Retention, engagement, conversion, uptime
- **File:** `hive/bees/admin/analytics_bee.py`

### PlannerBee (Onlooker) *[TODO]*
- **Duration:** Weekly
- **Function:** Content calendar, seasonal planning
- **Outputs:** Schedules, themed content plans

---

## BEE LIFECYCLE

```
                    ┌──────────────┐
                    │    QUEEN     │
                    │ (Scheduler)  │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  SPAWN   │    │  SPAWN   │    │  SPAWN   │
    │ (Scout)  │    │(Employed)│    │(Onlooker)│
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  WORK    │    │  WORK    │    │  WORK    │
    │ (Explore)│    │(Produce) │    │(Evaluate)│
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  HONEYCOMB  │
                  │   (State)   │
                  └─────────────┘
```

---

## PRIORITY MATRIX

| Priority | Response Time | Bee Types |
|----------|---------------|-----------|
| **CRITICAL** | Immediate | StreamMonitor, DonationProcessor, Moderator |
| **HIGH** | < 5 min | Engagement, SocialPoster, VIPManager |
| **NORMAL** | < 30 min | ShowPrep, TrendScout, RevenueAnalyst |
| **LOW** | < 24 hours | SponsorHunter, Analytics |
| **BACKGROUND** | Whenever | Archivist, Licensing |

---

## ADDING NEW BEES

1. Create new file in appropriate category folder: `hive/bees/{category}/{bee_name}_bee.py`
2. Inherit from `ScoutBee`, `EmployedBee`, or `OnlookerBee`
3. Implement `work()` method
4. Register in `hive/config.json` under `schedules` or `event_triggers`
5. Document in this file

---

## THE HIVE PROMISE

Every bee serves the mission:
- Keep the station **ONLINE**
- Keep the station **PROFITABLE**
- Keep the listeners **ENGAGED**
- Keep the content **FRESH**

No bee works alone. The swarm is greater than the sum of its parts.
