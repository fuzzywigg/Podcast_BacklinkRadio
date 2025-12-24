# REFACTOR PROPOSAL: MIGRATING TO CREWAI + OPENAI SWARM

**Status:** Proposal
**Target Architecture:** Hybrid Agentic Swarm (CrewAI + OpenAI Swarm)

## Executive Summary
This document outlines the plan to refactor the current custom `QueenOrchestrator` system into a robust, enterprise-grade multi-agent system using **CrewAI** for role definition and **OpenAI Swarm** for lightweight handoffs.

## Why Refactor?
The current system uses a custom loop (`QueenOrchestrator`) which is efficient but requires manual state management and task routing. Moving to a framework allows for:
1.  **Semantic Handoffs:** Agents can "talk" to each other and pass tasks based on intent rather than hardcoded logic.
2.  **Scalability:** Easier to add new roles without modifying the core loop.
3.  **Observability:** Built-in tracing and debugging from frameworks.

## Architecture

### 1. CrewAI for Role Definition
We will replace `hive/bees/*.py` classes with CrewAI `Agent` definitions.

**Example `hive/bees/content/crew.py`:**
```python
from crewai import Agent, Task, Crew, Process

show_prep_agent = Agent(
    role='ShowPrepBee',
    goal='Prepare engaging broadcast content and scripts',
    backstory='You are the creative producer of Backlink Broadcast...',
    tools=[search_tool, trend_tool],
    verbose=True
)

# ... define other agents ...
```

### 2. OpenAI Swarm for Handoffs
We will use OpenAI Swarm patterns for the "Queen" logic where dynamic routing is needed (e.g., a "Triage Agent" deciding if a tweet needs Marketing or Support).

### 3. The New Honeycomb
Instead of raw JSON files, we will implement a proper `Memory` store (supported by CrewAI) or continue using the file-based `honeycomb` but accessed via custom Tools.

## Migration Steps

### Phase 1: Hybrid Core (The Bridge)
*   **Goal:** Run CrewAI agents *inside* the existing Queen loop.
*   **Action:** Modify `QueenOrchestrator.spawn_bee` to instantiate a mini-Crew for that specific task instead of the old Bee class.
*   **Benefit:** Allows gradual migration bee-by-bee.

### Phase 2: The New Queen
*   **Goal:** Replace `orchestrator.py` with a main Crew process.
*   **Action:** Define a `BroadcastCrew` that runs continuously.
*   **Challenge:** "Continuous" loops in CrewAI are less native than one-off tasks. We may need a wrapper loop (like the current Queen) that kicks off a Crew "Session" every minute.

### Phase 3: Full Swarm
*   **Goal:** Implement inter-agent communication.
*   **Action:** Allow `TrendScout` to directly delegate to `SocialPoster` without Queen intervention, using Swarm handoffs.

## Implementation Plan (Code Changes)

1.  **Dependencies:** Add `crewai`, `openai-swarm` to `requirements.txt`.
2.  **Base Class:** Create `hive/bees/agent_base.py` wrapping CrewAI Agent.
3.  **Migration:**
    *   Convert `ShowPrepBee` -> `ShowPrepAgent`
    *   Convert `TrendScoutBee` -> `TrendScoutAgent`
    *   ...etc.
4.  **Orchestrator:** Rewrite `hive/queen/orchestrator.py` to initialize the Crew and manage the `kickoff` cycle.

## Impact Analysis
*   **Pros:** Modern stack, easier logic for complex tasks (e.g. "Research this topic then write a script"), better LLM integration.
*   **Cons:** Higher complexity for simple tasks (e.g. "Play song" might be overkill for an Agent), potential latency increase.

## Recommendation
Start with **Phase 1**. Wrap complex logic (Research, Show Prep) in CrewAI agents, but keep the `DjBee` and `StreamMonitor` as lightweight scripts for now to ensure strict timing compliance (the "Sacred 60-Second Rule").
