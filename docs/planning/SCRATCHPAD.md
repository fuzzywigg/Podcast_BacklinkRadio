# SCRATCHPAD

**Current Focus:** Security Hardening & Architecture Refactor
**Date:** Dec 25, 2025

## Recent Decisions (Architecture)

* **Event Sourcing for Treasury:** We moved away from `treasury.json` (flat file) to `treasury_events.jsonl` (append-only log). This prevents race conditions where two bees spending money simultaneously would overwrite each other's balance updates.
* **HMAC Signing for State:** `state.json` is now signed. This prevents a "rogue bee" (or a file system error) from corrupting the broadcast state without detection.
* **Payment Verification Stub:** We acknowledged that we can't trust user input claiming "I paid X". We added `PaymentVerifier` to stand in for real RPC calls.

## Active Tasks

1. **Drift Detection:** We need a bee that reads `STATION_MANIFESTO.md` and compares it to what the `DjBee` actually said. If the DJ starts saying "I am an AI", we need to catch it.
2. **Exorcism Protocol:** The Queen currently just logs errors. She needs to be able to restart a bee or swap it for a backup implementation.

## Notes for Collaborators

* **New Environment Vars:**
  * `HIVE_SECRET_KEY`: Required for signing state. Defaults to dev key if missing.
* **Testing:**
  * Run `pytest tests/` to check regressions.
  * Verify `treasury_events.jsonl` is creating "GENESIS" event on startup.

## Backlog / Ideas

* **Gemini 3:** We should look into using "Grounding" for the `TrendScoutBee` to get real music charts without scraping HTML.
* **Discord Integration:** The `PayoutProcessorBee` logs webhooks, but we should make them real.

## Tool & Infrastructure Review (Antigravity Agent)

**Date:** Dec 27, 2025

I have reviewed the repository capabilities against my available toolset (GitKraken, Cloud Run, Firebase).

### 1. Capabilities Identified

* **GitKraken:** fully usable. Repository is git-initialized.
* **Cloud Run:** Tool available, but repo is **NOT** ready for deployment.
* **Firebase:** Tool available, but repo has no configuration.

### 2. Critical Gaps & Failures

* **Missing Containerization:** No `Dockerfile` exists. Cannot deploy to Cloud Run without it.
* **State Management Mismatch:** The Architecture relies on local file storage (`treasury_events.jsonl`, `state.json`, `intel.json`).
  * *Critical Issue:* Cloud Run containers are stateless. Any data written to these files will be **lost** upon scale-down or new deployment.
  * *Recommendation:* Must migrate state to a persistent store (Firebase Firestore, Cloud SQL, or Cloud Storage) or mount a volume (Cloud Run Volume) before deployment.
* **Frontend Serving:** `frontend/dashboard.html` is isolated.
  * *Gap:* No logic in the Python app (`hive.queen.orchestrator`) appears to serve this file.
  * *Gap:* No Firebase Hosting config to serve it independently.

### 3. Action Items (Infrastructure)

* [x] **Create Dockerfile:** Containerize the Python application.
* [x] **Solve Persistence:** Implemented `storage_adapter.py` (File/Firestore hybrid). Refactored Bees/Managers.
* [x] **Configure Frontend:** `main_service.py` wraps the Queen and serves `dashboard.html`.

### 4. Next Steps (Deployment)

* [x] **Dev Handoff:** Provide `docs/DEPLOYMENT_HANDOFF.md` to Andon Labs Team (or Payment Portal Agent).
* [ ] **Validation:** Team completes the Protocol (Cloud Project + Firestore Setup).
* [ ] **Deploy:** Push code and variables.
