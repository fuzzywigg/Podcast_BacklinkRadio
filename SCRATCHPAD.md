# SCRATCHPAD

**Current Focus:** Security Hardening & Architecture Refactor
**Date:** Dec 25, 2025

## Recent Decisions (Architecture)
*   **Event Sourcing for Treasury:** We moved away from `treasury.json` (flat file) to `treasury_events.jsonl` (append-only log). This prevents race conditions where two bees spending money simultaneously would overwrite each other's balance updates.
*   **HMAC Signing for State:** `state.json` is now signed. This prevents a "rogue bee" (or a file system error) from corrupting the broadcast state without detection.
*   **Payment Verification Stub:** We acknowledged that we can't trust user input claiming "I paid X". We added `PaymentVerifier` to stand in for real RPC calls.

## Active Tasks
1.  **Drift Detection:** We need a bee that reads `STATION_MANIFESTO.md` and compares it to what the `DjBee` actually said. If the DJ starts saying "I am an AI", we need to catch it.
2.  **Exorcism Protocol:** The Queen currently just logs errors. She needs to be able to restart a bee or swap it for a backup implementation.

## Notes for Collaborators
*   **New Environment Vars:**
    *   `HIVE_SECRET_KEY`: Required for signing state. Defaults to dev key if missing.
*   **Testing:**
    *   Run `pytest tests/` to check regressions.
    *   Verify `treasury_events.jsonl` is creating "GENESIS" event on startup.

## Backlog / Ideas
*   **Gemini 3:** We should look into using "Grounding" for the `TrendScoutBee` to get real music charts without scraping HTML.
*   **Discord Integration:** The `PayoutProcessorBee` logs webhooks, but we should make them real.
