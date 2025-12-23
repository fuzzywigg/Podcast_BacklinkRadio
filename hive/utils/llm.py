"""
LLM Client Utility.

Handles interactions with Large Language Models (specifically Google Gemini).
"""

import google.generativeai as genai
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Ensure hive module is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hive.utils.keys import KeyManager


class LLMClient:
    """Client for interacting with LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client.

        Args:
            config: The full hive configuration dictionary.
        """
        self.config = config
        self.llm_config = config.get("llm", {})
        self.key_manager = KeyManager()
        self.api_key = self.key_manager.get_key(self.llm_config.get("api_key_env", "GOOGLE_API_KEY"))
        self.model_name = self.llm_config.get("model", "gemini-1.5-flash")

        self.enabled = False
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # create a default model instance to check if it works
                self.default_model = genai.GenerativeModel(self.model_name)
                self.enabled = True
            except Exception as e:
                print(f"Error configuring LLM: {e}")
        else:
            print("Warning: No API key found for LLM. functionality disabled.")

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Generate text response from LLM.

        Args:
            prompt: The user prompt or content to process.
            system_instruction: Optional system instruction/persona override.

        Returns:
            Generated text or None if failed.
        """
        if not self.enabled:
            print("LLM is disabled (missing API key).")
            return None

        try:
            # Instantiate model with system instruction if provided
            if system_instruction:
                model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            else:
                model = self.default_model

            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            return None
