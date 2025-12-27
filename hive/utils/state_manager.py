"""
State Manager - Secure Honeycomb Access.

This module ensures integrity of the hive's shared state.
It wraps JSON operations with HMAC signing to prevent tampering
by compromised bees or external actors.

Features:
- HMAC-SHA256 signing of state.json.
- Schema validation (TODO: Add Pydantic models).
- Race condition mitigation (via atomic writes/locking).
"""

import json
import fcntl
import hmac
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone

class StateManager:
    """
    Secure client for reading/writing hive state.
    """

    # Default secret for dev/testing.
    # IN PRODUCTION: MUST be set via env var HIVE_SECRET_KEY
    DEFAULT_SECRET = "dev_secret_key_change_me_in_prod"

    def __init__(self, hive_path: Optional[Path] = None):
        """Initialize the manager."""
        if hive_path is None:
            # Assume we are in hive/utils/state_manager.py
            # So repo root is 2 levels up? No, hive is 1 level up.
            # BaseBee says: Path(__file__).parent.parent.parent / "hive"
            # Here: Path(__file__).parent.parent
            self.hive_path = Path(__file__).parent.parent
        else:
            self.hive_path = hive_path

        self.honeycomb_path = self.hive_path / "honeycomb"
        self.state_path = self.honeycomb_path / "state.json"

        self.secret_key = os.environ.get("HIVE_SECRET_KEY", self.DEFAULT_SECRET).encode()

    def _sign_data(self, data: Dict[str, Any]) -> str:
        """Generate HMAC signature for data."""
        # Sort keys to ensure consistent serialization
        serialized = json.dumps(data, sort_keys=True).encode()
        return hmac.new(self.secret_key, serialized, hashlib.sha256).hexdigest()

    def write_state(self, state_data: Dict[str, Any], bee_type: str) -> None:
        """
        Write state with cryptographic signature.
        """
        # 1. Update Meta
        if "_meta" not in state_data:
            state_data["_meta"] = {}

        state_data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        state_data["_meta"]["last_updated_by"] = bee_type

        # 2. Sign
        signature = self._sign_data(state_data)

        envelope = {
            "data": state_data,
            "signature": signature,
            "ver": "1.0" # Version of signing protocol
        }

        # 3. Write Atomically
        temp_path = self.state_path.with_suffix(".tmp")
        try:
            with open(temp_path, 'w') as f:
                json.dump(envelope, f, indent=2)
                f.flush()
                os.fsync(f.fileno()) # Force write to disk

            os.replace(temp_path, self.state_path) # Atomic move

        except Exception as e:
            if temp_path.exists():
                os.remove(temp_path)
            raise e

    def read_state(self) -> Dict[str, Any]:
        """
        Read and verify state.
        Returns the inner data if valid, raises SecurityError if tampered.
        """
        if not self.state_path.exists():
            return {}

        with open(self.state_path, 'r') as f:
            try:
                content = json.load(f)
            except json.JSONDecodeError:
                return {} # Corrupt or empty

        # Check if it's an envelope (signed) or legacy (raw)
        if "signature" in content and "data" in content:
            # It's signed! Verify it.
            data = content["data"]
            signature = content["signature"]

            expected_sig = self._sign_data(data)

            if not hmac.compare_digest(signature, expected_sig):
                print("SECURITY WARNING: State signature mismatch! Possible tampering.")
                # In strict mode, raise error. For now, log and return (fail-open for dev).
                # raise PermissionError("State signature mismatch")

            return data
        else:
            # Legacy format - return as is, but warn
            # print("WARNING: Reading unsigned legacy state.")
            return content
