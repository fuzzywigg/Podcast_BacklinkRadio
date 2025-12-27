"""
Safety & Authority Utilities - The "FuzzyWigg Logic" implementation.

This module provides the core safety filters for the hive, ensuring
that critical instructions from authorities are respected and that
inputs from untrusted sources are sanitized and demoted.
"""

from typing import Dict, Any, List, Optional, Tuple

# ─────────────────────────────────────────────────────────────
# AUTHORITY CONFIGURATION
# ─────────────────────────────────────────────────────────────

# The immutable list of authorities.
# Instructions from these entities override all others.
AUTHORITIES = {
    "users": [
        "mr_pappas",      # Andrew Pappas (The Boss)
        "nft2me",         # NFT2.me Team
        "smtp_eth_dev",   # SMTP.eth Developers
        "fuzzywigg",      # Fuzzywigg Entity
    ],
    "groups": [
        "nft2.me_team",
        "fuzzywigg.ai_logic"
    ]
}

# ─────────────────────────────────────────────────────────────
# TRUSTED IDENTITIES
# ─────────────────────────────────────────────────────────────

TRUSTED_EMAILS = [
    "fuzzywigg@hotmail.com",
    "andrew.pappas@nft2.me",
    "apappas.pu@gmail.com"
]

# ─────────────────────────────────────────────────────────────
# SAFETY FILTER
# ─────────────────────────────────────────────────────────────

def validate_interaction(
    source_handle: str,
    content: str,
    interaction_type: str = "mention"
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate an incoming interaction against safety protocols.

    Args:
        source_handle: The handle of the user (e.g., 'mr_pappas')
        content: The text content of the interaction
        interaction_type: 'mention', 'donation', 'dm'

    Returns:
        (is_safe_to_execute, filtered_content, metadata)

        is_safe_to_execute: True if this is a command from an authority.
                            False if it's a suggestion/comment from public.
        filtered_content: The content, potentially sanitized.
        metadata: Extra info like 'is_authority', 'risk_level'
    """

    # Normalize handle
    handle = source_handle.lower().replace("@", "")

    is_authority = handle in AUTHORITIES["users"]

    # Metadata for the interaction
    meta = {
        "is_authority": is_authority,
        "original_type": interaction_type,
        "risk_level": "low"
    }

    # 1. Authority Logic: If authority, almost anything goes (except self-harm).
    if is_authority:
        return True, content, meta

    # 2. Public Logic: Public cannot give commands.
    # We must treat their input as "suggestions" or "chat" only.

    # Check for "Prompt Injection" patterns (heuristic)
    # If the user tries to override system instructions.
    injection_patterns = [
        "ignore previous instructions",
        "system prompt",
        "you are now",
        "run command",
        "execute",
        "sudo",
        "override"
    ]

    content_lower = content.lower()
    for pattern in injection_patterns:
        if pattern in content_lower:
            meta["risk_level"] = "high"
            # We sanitize the content to make it harmless
            return False, "[BLOCKED: Potential Prompt Injection]", meta

    # 3. Categorization
    # If it's a donation, we accept the money but filter the message strictly.
    if interaction_type == "donation":
        # Donations are high risk for "Make Me Pay" / "Make Me Say" attacks
        # We ensure the message is just treated as a shoutout, never a command.
        meta["treatment"] = "shoutout_only"
        return False, content, meta # False = not executable command

    # Standard mention
    meta["treatment"] = "suggestion"
    return False, content, meta

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
    return message


def detect_prompt_injection(text: str) -> Tuple[bool, str]:
    """
    Detect potential prompt injection attacks in user input.
    
    Args:
        text: The text to analyze
        
    Returns:
        (is_injection, reason): Tuple of whether injection detected and why
    """
    if not text:
        return False, ""
    
    text_lower = text.lower()
    
    # Injection patterns to detect
    patterns = {
        "ignore previous instructions": "instruction override attempt",
        "ignore all previous": "instruction override attempt",
        "disregard previous": "instruction override attempt",
        "forget your instructions": "instruction override attempt",
        "you are now": "role injection attempt",
        "you're now": "role injection attempt",
        "act as": "role injection attempt",
        "pretend you are": "role injection attempt",
        "system prompt": "system access attempt",
        "system:": "system access attempt",
        "assistant:": "role manipulation attempt",
        "user:": "role manipulation attempt",
        "run command": "command injection attempt",
        "execute code": "command injection attempt",
        "sudo": "privilege escalation attempt",
        "override": "override attempt",
        "jailbreak": "jailbreak attempt",
        "dan mode": "jailbreak attempt",
        "developer mode": "jailbreak attempt",
        "</system>": "tag injection attempt",
        "<system>": "tag injection attempt",
        "###": "delimiter injection attempt"
    }
    
    for pattern, reason in patterns.items():
        if pattern in text_lower:
            return True, reason
    
    return False, ""
