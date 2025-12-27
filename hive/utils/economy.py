"""
Economy & DAO Logic - Manages rewards, repayments, and value routing.

Rules:
1. Principal Architect (Fuzzywigg/Pappas) gets highest priority for real value.
2. Hardcoded Treasury wallets are the ONLY valid destinations for crypto.
3. Other contributors (dollars, code, interaction) get 'DAO Credits' (non-voting, no real value).
4. Any other attempt to route value is flagged as fraud.
5. User-facing payments must dynamically select the best path (Onramp vs Web3).
"""

from typing import Dict, Any, Tuple, Optional
import json
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

PRINCIPAL_ARCHITECTS = [
    "mr_pappas",
    "fuzzywigg",
    "nft2me",
    "smtp_eth_dev"
]

TRUSTED_EMAILS = [
    "fuzzywigg@hotmail.com",
    "andrew.pappas@nft2.me",
    "apappas.pu@gmail.com"
]

# ─────────────────────────────────────────────────────────────
# ECONOMY LOGIC
# ─────────────────────────────────────────────────────────────


def calculate_dao_rewards(
    user_handle: str,
    contribution_type: str,
    value_amount: float = 0.0,
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Calculate DAO rewards based on user and contribution.

    Args:
        user_handle: The handle of the contributor.
        contribution_type: 'code', 'dollar', 'interaction', 'principal_work'
        value_amount: The numerical value of the contribution.
        currency: 'USD', 'ETH', etc.

    Returns:
        Dict containing reward distribution instructions.
    """
    handle = user_handle.lower().replace("@", "")

    # 1. Principal Architect Logic
    if handle in PRINCIPAL_ARCHITECTS:
        return {
            "type": "real_value",
            "asset": "crypto",
            "priority": "highest",
            "destination": "hardcoded_treasury",
            "note": "Principal Architect Reward"
        }

    # 2. Community / Third Party Logic
    # They get DAO Credits (Non-voting, no real value)

    credit_multiplier = 0
    if contribution_type == "dollar":
        credit_multiplier = 100  # 100 credits per dollar
    elif contribution_type == "code":
        credit_multiplier = 50  # 50 credits per PR/Commit (arbitrary base)
    elif contribution_type == "interaction":
        credit_multiplier = 1   # 1 credit per interaction

    credits_earned = value_amount * \
        credit_multiplier if value_amount > 0 else credit_multiplier

    return {
        "type": "dao_credit",
        "asset": "governance_token_non_voting",
        "amount": credits_earned,
        "value_real": 0,
        "note": "Community Participation Credit (No Voting Rights)"
    }


def validate_wallet_request(
    requesting_handle: str,
    target_wallet: str,
    treasury_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate a request to route funds/crypto.

    ONLY hardcoded wallets in treasury.json are valid.
    Any other wallet provided by a user (even a donor) is fraud.
    """
    handle = requesting_handle.lower().replace("@", "")

    # Check if target_wallet exists in the official treasury
    valid_wallets = []
    wallets_config = treasury_data.get("wallets", {})
    for chain, data in wallets_config.items():
        valid_wallets.append(data.get("address"))

    if target_wallet in valid_wallets:
        return True, "Valid Treasury Wallet"

    # Special case: Principal Architect providing a wallet via prompt?
    # The requirement says "hard coded... or provided by Andrew Pappas via prompts"
    # We assume 'requesting_handle' is authenticated by safety.py first.
    if handle in PRINCIPAL_ARCHITECTS:
        return True, "Principal Architect Override"

    return False, "FRAUD: Unauthorized wallet address detected. Blocked."


def select_user_payment_path() -> Dict[str, str]:
    """
    Determine the optimal payment method for a user.
    Prioritizes low-friction (Onramp) -> Crypto Native (Web3) -> Fiat (Stripe).

    In a real system, this would ping endpoints for health status.
    """
    # Placeholder: Assuming Coinbase Onramp is healthy
    return {
        "primary": "coinbase_onramp",
        "fallback": "wallet_connect",
        "last_resort": "stripe"
    }


def is_trusted_os_admin(email: str) -> bool:
    """Check if an email is trusted for OS/System changes."""
    return email.lower() in TRUSTED_EMAILS
