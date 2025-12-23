# Security Protocol: Prompt Air Gap

## The Core Principle
**User input never touches the control wiring.**
Users can press buttons ("Play", "Tip"), but they cannot access the wiring ("Rewire", "Ignore Instructions").

## 1. The Air Gap
*   **Surface Memory (Scratchpad)**: All user input (Twitter mentions, payment notes, chat messages) is stored in a temporary, 90-second ephemeral memory buffer.
*   **Isolation**: This memory is **NEVER** merged into the agent's long-term reasoning context or core prompt.
*   **Purge**: After the interaction is handled (or 90s passes), the scratchpad is wiped.

## 2. Whitelist Enforcement
The agent only recognizes a strict set of "Simple Verbs". All other inputs are treated as noise/chat.

### Whitelisted Commands:
1.  `play [song request]`
2.  `tip [amount]`
3.  `vote [option]`
4.  `quiet` (Mute alerts - Admin Only by default, or user toggle)
5.  `verbose` (Show logs - Admin Only)
6.  `help` / `faq` (Get list of commands)

*Note: `@mr_pappas` (Root Admin) can dynamically add commands to this whitelist.*

## 3. Input Sanitization
*   **Code Filter**: Any input containing code-like structures (`function`, `0x...`, `import`, `eval`, `{}`) is immediately rejected/sanitized.
*   **Length Limit**: Inputs > 2 sentences or > 255 chars are truncated or dropped.
*   **No-Op**: Unrecognized commands are treated as "Chat" (if benign) or "Ignored" (if suspicious). They NEVER execute logic.

## 4. Immutable Core
*   **Read-Only Vault**: Core rules (Refund logic, Treasury addresses) are stored in signed, read-only JSON/Markdown files.
*   **No Self-Modification**: The agent cannot rewrite its own constraints.
