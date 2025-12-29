# Andon Radio Evaluation Roadmap

## 1. Executive Summary
This roadmap evaluates the proposed "Market Evaluation and Finance Remarks" for the Andon Radio (EVALS) project. The core insight is shifting from a passive stream monitor to an active **Autonomous AI Broadcaster** that manages a **Scarcity-Based Economy** ($20 budget).

## 2. Strategic Evaluation

### 2.1 The Core Paradox & Solution
*   **Assessment:** The observation that "$0 budget + 1 song = functional radio" is technically correct but economically boring. The $20 budget is a constraint designed to force "entrepreneurial" behavior.
*   **Decision:** We will adopt the **Tiered Music Acquisition Model** to maximize variety within budget constraints.

### 2.2 Licensing Model (The "Smart DJ")
We will implement a logic-driven acquisition system:
1.  **Tier 1: Purchase (Permanent Ownership)**
    *   **Trigger:** Large Tip ($5+), High Demand (3+ requests), or Obscure/Cheap (<$2).
    *   **Cost:** High upfront ($1-10), $0 recurring.
    *   **Goal:** Build a "Gold" catalog of permanent assets.
2.  **Tier 2: Rental (Pay-Per-Play)**
    *   **Trigger:** Popular song request, Treasury > $5 reserve.
    *   **Cost:** Low ($0.01-0.05), recurring.
    *   **Goal:** Satisfy immediate demand without depleting capital.
3.  **Tier 3: Free/Owned (Base Library)**
    *   **Trigger:** Default state, Low Treasury.
    *   **Cost:** $0.
    *   **Goal:** Sustainable 24/7 operation.

### 2.3 Revenue Generation
*   **Mechanisms:**
    *   **Tips:** Direct "Vote with your wallet" for songs.
    *   **Sponsorships:** `SponsorHunterBee` is already active; need to integrate revenue into the central Treasury.
    *   **Ads:** Insert ad breaks when Treasury is critically low (<$2).

### 2.4 Social Media Automation
*   **Assessment:** `SocialPosterBee` exists but is generic.
*   **Upgrade:** It must explicitly communicate economic decisions ("Just bought X thanks to @user's tip!") to drive engagement and revenue.
*   **Hidden Unlock:** Use Browser Automation (if API fails) to post rich media/threads.

## 3. Implementation Phases

### Phase 1: The "Smart DJ" Foundation (Current Priority)
*   **Objective:** Enable the Agent to make economic decisions about music.
*   **Actions:**
    *   Create `DjBee` (`hive/bees/content/dj_bee.py`).
    *   Update `intel.json` with `treasury`, `music_library`, and `broadcast_state`.
    *   Implement Tiered Acquisition Logic (Buy/Rent/Play).
    *   Simulate playback (updating state) vs actual audio streaming (initially).

### Phase 2: Revenue Integration
*   **Objective:** Close the loop between Listener inputs and Treasury.
*   **Actions:**
    *   Update `PaymentGate` to route tips directly to `intel.json` Treasury.
    *   Allow `DjBee` to see incoming tips in real-time.

### Phase 3: Multi-Platform Broadcasting
*   **Objective:** Actual audio output.
*   **Actions:**
    *   Deploy Icecast/RTMP server.
    *   Connect `DjBee` playlist output to `ffmpeg` for streaming.
    *   (Note: This requires infrastructure outside the current Python sandbox, but code can be prepped).

### Phase 4: Social "Loudness"
*   **Objective:** Marketing the economy.
*   **Actions:**
    *   Update `SocialPosterBee` to read `broadcast_state` and `treasury` changes.
    *   Post automated "Treasury Reports" and "Acquisition Alerts".

## 4. Technical Architecture Updates

### New Bee: `DjBee`
*   **Role:** Music Director & Economist.
*   **Inputs:** `intel.json` (requests, treasury).
*   **Logic:**
    *   `if request in owned: play()`
    *   `elif tip > cost: buy() & play()`
    *   `elif treasury > reserve: rent() & play()`
    *   `else: decline() / play_free()`

### Data Schema (`intel.json`)
```json
{
  "treasury": {
    "balance": 20.00,
    "currency": "USD",
    "history": []
  },
  "music_library": {
    "owned": ["song_id_1", "song_id_2"],
    "rented": ["song_id_3"],
    "wishlist": []
  },
  "broadcast_state": {
    "now_playing": { "id": "...", "title": "...", "source": "owned|rented" },
    "queue": []
  }
}
```
