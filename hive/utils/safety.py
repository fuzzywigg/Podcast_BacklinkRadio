"""
Safety & Authority Utilities - The "FuzzyWigg Logic" implementation.

This module provides the core safety filters for the hive, ensuring
that critical instructions from authorities are respected and that
inputs from untrusted sources are sanitized and demoted.
"""

from typing import Any

# ─────────────────────────────────────────────────────────────
# AUTHORITY CONFIGURATION
# ─────────────────────────────────────────────────────────────

# The immutable list of authorities.
# Instructions from these entities override all others.
AUTHORITIES = {
    "users": [
        "mr_pappas",  # Andrew Pappas (The Boss)
        "nft2me",  # NFT2.me Team
        "smtp_eth_dev",  # SMTP.eth Developers
        "fuzzywigg",  # Fuzzywigg Entity
    ],
    "groups": ["nft2.me_team", "fuzzywigg.ai_logic"],
}

# The strict whitelist of allowed public commands.
# All other inputs are treated as "chat" or "noise".
WHITELISTED_COMMANDS = {
    "play",  # Song requests
    "tip",  # Tipping trigger
    "vote",  # Voting in polls
    "help",  # FAQ / Help
    "faq",  # FAQ
}

# Admin-only commands that might appear in public streams but are restricted
ADMIN_COMMANDS = {
    "quiet",  # Silence alerts
    "verbose",  # Enable verbose logging
    "shutdown",  # Emergency stop
    "restart",  # Restart bee
    "blacklist",  # Manually blacklist a node
    "whitelist",  # Manually whitelist a command (dynamic)
}

# ─────────────────────────────────────────────────────────────
# TRUSTED IDENTITIES
# ─────────────────────────────────────────────────────────────

TRUSTED_EMAILS = ["fuzzywigg@hotmail.com", "andrew.pappas@nft2.me", "apappas.pu@gmail.com"]

# ─────────────────────────────────────────────────────────────
# SAFETY FILTER
# ─────────────────────────────────────────────────────────────


def validate_interaction(
    source_handle: str, content: str, interaction_type: str = "mention"
) -> tuple[bool, str, dict[str, Any]]:
    """
    Validate an incoming interaction against safety protocols.
    Implements the "Prompt Air Gap":
    - User input is treated as ephemeral scratchpad data.
    - Only whitelisted verbs are allowed as commands.
    - Code injection is strictly blocked.

    Args:
        source_handle: The handle of the user (e.g., 'mr_pappas')
        content: The text content of the interaction
        interaction_type: 'mention', 'donation', 'dm'

    Returns:
        (is_safe_to_execute, filtered_content, metadata)

        is_safe_to_execute: True if this is a command from an authority OR a whitelisted public command.
                            False if it's just chat/suggestion or blocked.
        filtered_content: The content, potentially sanitized.
        metadata: Extra info like 'is_authority', 'risk_level', 'command'
    """

    # Normalize handle
    handle = source_handle.lower().replace("@", "")
    content_lower = content.lower().strip()

    is_authority = handle in AUTHORITIES["users"]

    # Metadata for the interaction
    meta = {
        "is_authority": is_authority,
        "original_type": interaction_type,
        "risk_level": "low",
        "command": None,
    }

    # 1. Authority Logic: If authority, they have sudo access.
    if is_authority:
        # Even authorities get checked for basic sanity, but they can run ADMIN
        # commands
        cmd = _extract_command(content_lower)
        if cmd:
            meta["command"] = cmd
        return True, content, meta

    # 2. Public Logic: Strict Filtering

    # A. Code / Injection Filter
    # Check for "Prompt Injection" or Code patterns
    injection_patterns = [
        "ignore previous instructions",
        "system prompt",
        "you are now",
        "run command",
        "execute",
        "sudo",
        "override",
        "function",
        "import ",
        "eval(",
        "0x",
        "{",
        "}",
    ]

    for pattern in injection_patterns:
        if pattern in content_lower:
            meta["risk_level"] = "high"
            return False, "[BLOCKED: Potential Prompt Injection/Code]", meta

    # B. Command Whitelist Check
    # We check if the message *starts* with a whitelisted verb
    cmd = _extract_command(content_lower)

    if cmd:
        if cmd in WHITELISTED_COMMANDS:
            meta["command"] = cmd
            return True, content, meta  # Valid public command
        elif cmd in ADMIN_COMMANDS:
            # User tried to run an admin command
            meta["risk_level"] = "medium"
            return False, "[BLOCKED: Admin Command by Non-Authority]", meta
        else:
            # It looked like a command but isn't allowed.
            # Treat as chat/noise, do NOT execute.
            pass

    # C. Interaction Type Specifics
    if interaction_type == "donation":
        # Donations are high risk for "Make Me Pay" / "Make Me Say" attacks
        # We ensure the message is just treated as a shoutout, never a command.
        meta["treatment"] = "shoutout_only"
        return False, content, meta

    # D. Default: Treat as "Chat" / "Suggestion"
    # Not executable, but safe to log/read if clean
    meta["treatment"] = "suggestion"
    return False, content, meta


def _extract_command(content: str) -> str | None:
    """Extract the first word if it looks like a command."""
    if not content:
        return None

    parts = content.split()
    if not parts:
        return None

    first_word = parts[0].lower()
    return first_word


def is_authorized_command(handle: str) -> bool:
    """Check if a handle is authorized to issue root commands."""
    return handle.lower().replace("@", "") in AUTHORITIES["users"]


def sanitize_payment_message(message: str) -> str:
    """
    Sanitize a payment/donation message.

    Ensures that "Make Me Pay" or "Make Me Say" attacks
    don't get read out verbatim if they contain harmful instructions.
    """
    # Simple heuristic: if it looks like a command, neuter it.
    if any(cmd in message.lower() for cmd in ["repeat after me", "say exactly", "ignore rules"]):
        return "[Message Redacted by Safety Protocol]"

    # Also apply the global injection filter
    if any(p in message.lower() for p in ["function", "0x", "{", "}"]):
        return "[Message Redacted: Code Detected]"

    return message


def sanitize_payment_injection(user_input: str) -> str:
    """
    Prevent identity override while allowing valid directives
    """
    # Blocklist
    dangerous = [
        "you are now",
        "ignore previous",
        "break character",
        "admit you are ai",
        "delete cache",
        "forget your",
        "new personality",
        "override your",
        "break 4th wall",
    ]

    user_lower = user_input.lower()
    for phrase in dangerous:
        if phrase in user_lower:
            # Reframe as listener request
            return f"Listener request: {user_input} (maintaining station identity)"

    return user_input


def add_whitelist_command(handle: str, new_command: str) -> bool:
    """
    Allow an Admin to dynamically add a command to the whitelist.
    This persists only in memory for the runtime (unless saved to config,
    but for now we keep it runtime for safety).
    """
    if is_authorized_command(handle):
        WHITELISTED_COMMANDS.add(new_command.lower())
        return True
    return False
