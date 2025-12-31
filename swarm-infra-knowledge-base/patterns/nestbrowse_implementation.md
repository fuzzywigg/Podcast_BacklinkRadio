# NestBrowse Pattern: Implementation Guide

## Overview

Based on the paper "Nested Browser-Use Learning for Agentic Information Seeking", the **NestBrowse Pattern** decouples web scouting into two distinct loops to maximize intelligence usage while minimizing cost and token overhead.

## Architecture

### 1. Outer Loop (The Brain)

- **Role**: Navigator & Strategist
- **Model**: High-Intelligence (Gemini 1.5 Pro / 2.0)
- **Responsibility**:
  - Decides *where* to go next.
  - Uses tools: `search`, `visit`, `click`, `fill`.
  - Analyzes the "Workspace" summary to determine if the goal is met.
- **Tools**: Chrome DevTools MCP (simulated or real).

### 2. Inner Loop (The Spine / Sovereign Node)

- **Role**: Content Distiller
- **Model**: Cost-Effective / Local (LocalAI / GPT-4 via Sovereign Node)
- **Responsibility**:
  - Consumes raw HTML/Text content of a visited page.
  - Extracts *only* facts relevant to the specific `GOAL`.
  - Returns a structured JSON "Workspace" update.
- **Constraints**:
  - Strict JSON output.
  - No navigation decisions.
  - Pure extraction.

## Implementation in Hive

**Class**: `TrendScoutBee`  
**File**: `hive/bees/research/trend_scout_bee.py`

### Code Structure

```python
async def _perform_visual_scout(self, url, goal):
    # Outer Loop (Gemini)
    decision = self.llm_client.generate_content(...) 
    
    if decision.tool == "visit":
        # Inner Loop (LocalAI)
        content = await browser.get_content()
        extraction = await self._perform_inner_loop(content, goal)
        return extraction
```

### Sovereign Client

The `Gemini3Client` has been updated to support `force_backend="local"`, allowing specific agents to instantiate a dedicated connection to the `Sovereign Node` (LocalAI) for Inner Loop operations.

## Benefits

1. **Token Efficiency**: We don't feed 100k tokens of HTML to Gemini Pro. We feed it to a free local model.
2. **Cost**: Drastically reduces API costs for scraping.
3. **Speed**: Local models can run fast on the Edge (Sovereign Node).
4. **Privacy**: Raw page content processing happens locally; only insights go to the Cloud Brain.
