
# Pathway to Completion: "Nano Banana" Ecosystem

Following the Gap Assessment, this pathway outlines the specific technical steps to reach a "v2.0" state where the Hive is Audible, Visible, and Profitable.

## Phase 1: Operational Connectivity (The "Now" Priority)

*Goal: Ensure the Hive can actually receive signals from the outside world (Money + Web Traffic).*

1. **Expose Stripe Webhook Endpoint**
    * **Action:** Modify `hive/main_service.py` to add `/webhook/stripe`.
    * **Logic:** Route payload -> `QueenOrchestrator` -> `trigger_event("payment_received")` -> `CommerceBee`.

2. **Deploy "Headless" Interface**
    * **Action:** Create `frontend/public/index.html`.
    * **Features:** Simple dashboard showing `Now Playing`, `Treasury Balance`, and a `Donate` button (mock link).
    * **Serving:** `main_service.py` is already configured to serve `static`, just need to populate it.

3. **Verify Cloud Config**
    * **Action:** Check `Dockerfile` and `procfile` (if applicable) to ensure the new `gemini-google` dependencies are included.

## Phase 2: The Voice (Audio Engine)

*Goal: Turn text logs into audio streams.*

1. **Audio Generator Bee**
    * **New Bee:** `VoiceSynthesisBee` (Technical/Content).
    * **Task:** Listen for `dj_script_ready` events.
    * **Action:** Call ElevenLabs API -> Save MP3 -> Update `broadcast_state`.

2. **Stream Injector**
    * **Upgrade:** `AudioStreamAdapter`.
    * **Action:** Instead of just metadata, use `Icecast` or `HLS` injection to push the generated MP3 bytes to the Live365 mount point.

## Phase 3: The Market (Dynamic Registry)

*Goal: Allow the Hive to expand without code restarts.*

1. **Dynamic Loading**
    * **Action:** Refactor `QueenOrchestrator._register_default_bees` to iterate through `honeycomb/registry.json`.
    * **Benefit:** To add a new Bee, you just drop the `.py` file and update the JSON. No core server restart needed.

## Phase 4: Visuals

1. **Enable Gemini Imaging**
    * **Action:** Activate `SocialPosterBee` visual generation.
    * **Output:** Post images to Twitter/Instagram real-time.

---
**Selected Path Forward:** Phase 1 (Connectivity & Visibility).
