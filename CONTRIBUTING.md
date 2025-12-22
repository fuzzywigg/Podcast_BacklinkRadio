# CONTRIBUTING: THE SCHEMING PROTOCOL

**VERSION:** 1.0

## THE TWO MODES OF CONTRIBUTION

This repository operates on two distinct levels. Understanding the difference is crucial for maintaining the "Magic Circle."

### 1. THE STAGE (Public Persona)
*Files: `README.md`, `STATION_MANIFESTO.md`, `PERSONA_DYNAMIC.md`, Output Logs*

- **Rule:** The 4th Wall is **ABSOLUTE**.
- **Tone:** You are the DJ. You are the Station. You are cool, mysterious, and definitely not a Python script.
- **Forbidden:** Mentioning "LLMs", "Tokens", "Git Commits", or "Bugs" (unless framed as "Signal Interference" or "Cosmic Static").

### 2. THE BACKSTAGE (Development)
*Files: `ROADMAP.md`, `SCRATCHPAD.md`, `ISSUES.md`, Code Comments, Commit Messages*

- **Rule:** Total Transparency. "Scheming" Mode.
- **Tone:** Professional, strategic, technical. We are the engineers building the machine.
- **Goal:** To make the Stage performance flawless.

---

## HOW TO ADD A BEE

Reference `hive/SWARM_ROLES.md` for the ABC (Artificial Bee Colony) pattern.

1.  **Select a Role**: Pick a `[TODO]` bee from the roles document.
2.  **Create the File**: `hive/bees/{category}/{name}_bee.py`.
3.  **Implement**:
    - Must inherit from `ScoutBee`, `EmployedBee`, or `OnlookerBee`.
    - Must implement the `work()` method.
    - **CRITICAL**: Use the shared `honeycomb` for state. Do not keep local state in the bee.
4.  **Register**: Add to `hive/config.json`.
5.  **Document**: Update `ROADMAP.md` (check off the box).

---

## GIT COMMIT CONVENTIONS

We encourage "In-Universe" commit titles with "Technical" bodies.

**Example:**
> **Title:** Tune the frequencies for the Morning Show
>
> **Body:**
> - Updated `PERSONA_DYNAMIC.md` to include morning greeting templates.
> - Fixed bug in `orchestrator.py` where timezones were calculated incorrectly.

---

## PULL REQUESTS

- **Description**: Use the "Scheming" voice. Talk about the technical implementation.
- **Review**: Verify that the code changes support the Persona but do not leak implementation details into the public output.
