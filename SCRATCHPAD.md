# Agent Collaboration Scratchpad

**Status:** Active
**Current Sprint:** Alignment & Requirements

## 🛑 SILO PREVENTION PROTOCOL
*   **Do not work in isolation.** Document all major architectural decisions here.
*   **Shared Vision:** We are building a unified, constitutional Hive.
*   **Source of Truth:** This file tracks the immediate path forward.

## 📝 Current Path Forward
*   **Goal:** Integrate Andon Labs stack for alignment tasks.
*   **Action Items:**
    1.  Initialize `hive/alignment/` directory.
    2.  Explore `claude-code-sdk-python-andon-special` capabilities.
    3.  Define specific "alignment tasks".

## 🧠 Joint Memory & Context
*   **Andon Labs SDK:** A Python SDK for Claude Code, allowing in-process MCP servers and hooks.
*   **Usage:** Useful for design work and alignment tasks.
*   **Repository:** `https://github.com/AndonLabs/claude-code-sdk-python-andon-special`

## 🚧 Active Drafts & Notes
*   **Alignment Strategy:** We will use the SDK to create custom tools (MCP servers) that help enforce the Constitutional Principles.
*   **Integration Point:** The `ConstitutionalGateway` might benefit from "hooks" provided by the SDK to validate actions before execution.
