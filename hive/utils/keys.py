"""
Key Management Utility.

Handles secure retrieval of API keys from environment variables
or a local keys.json file (not in version control).
"""

import json
import os
from pathlib import Path


class KeyManager:
    """Manages API keys and secrets."""

    def __init__(self, hive_path: str | None = None):
        """Initialize with path to hive."""
        if hive_path is None:
            # Default to hive directory relative to this file
            hive_path = Path(__file__).parent.parent
        self.hive_path = Path(hive_path)
        self.keys_path = self.hive_path / "keys.json"
        self._local_keys = self._load_local_keys()

    def _load_local_keys(self) -> dict:
        """Load keys from local JSON file if it exists."""
        if self.keys_path.exists():
            try:
                with open(self.keys_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load keys.json: {e}")
                return {}
        return {}

    def get_key(self, env_var_name: str) -> str | None:
        """
        Retrieve a key by its environment variable name.

        Priority:
        1. OS Environment Variable
        2. keys.json file
        """
        # 1. Try environment variable
        key = os.getenv(env_var_name)
        if key:
            return key

        # 2. Try local keys file
        return self._local_keys.get(env_var_name)
