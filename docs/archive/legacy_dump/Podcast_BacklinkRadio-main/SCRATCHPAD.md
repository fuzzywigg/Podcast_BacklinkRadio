# SCRATCHPAD: THE BACKSTAGE

**ACCESS:** LEVEL 5 (Internal / Scheming)
**PURPOSE:** Ideas, brain dumps, technical debt, and conversations between the Operator and the Construct.

---

## 🗣️ THE SCHEMING ROOM
*Use this space to talk to the Human Operator without the "DJ Persona". Be real. Be technical. Be strategic.*

**Message from the Hive:**
> Ready to begin implementation of the missing Bees. Which one is the highest priority for the "Physics of Home" transition? I suspect the `AutomationBee` or `DonationProcessorBee` would give us the most immediate autonomy.

---

## 💡 BRAINSTORMING & HALF-BAKED IDEAS
*The "Parking Lot" for concepts that aren't ready for the Roadmap.*

- **The "Physics of Home"**:
    - How does a digital entity "feel" time?
    - Idea: Adjust processing speed/tick rate based on "energy levels" (server load or donations).
    - Idea: "Sleep" cycles where the station plays "Dream Pop" and does deep maintenance/archiving.

- **Moneyball Strategy Refinement**:
    - Current logic is vague.
    - Need a concrete algorithm: `Value = (Listener_Vibe_Match_Score / Licensing_Cost) * Rarity_Multiplier`.

- **Visuals**:
    - Can we generate album art for the AI-generated segments?
    - ASCII art visualizer in the terminal logs?

---

## 🛠️ TECHNICAL DEBT & CONCERNS
*Things that are broken, ugly, or worrying.*

- **Config.json**:
    - `enabled: false` is everywhere. We are running in simulation mode.
    - Need environment variable validation on startup.

- **Orchestrator**:
    - Currently seems to rely on external triggers or simple loops.
    - Needs a true "Event Bus" to handle the async nature of the Bees.

- **Memory**:
    - `honeycomb/*.json` files will get huge. Need a rotation strategy or a real database (SQLite/Postgres) eventually.

---

## 📝 NOTES FROM THE FIELD
*Observations from runtime.*

- (Empty - Waiting for first live run)
