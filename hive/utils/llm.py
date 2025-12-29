"""
LLM Client Utility.

Handles interactions with Large Language Models (specifically Google Gemini).
"""

import datetime
from typing import Any

import google.generativeai as genai
from google.generativeai import caching

from hive.utils.keys import KeyManager


class LLMClient:
    """Client for interacting with LLM providers."""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize LLM client.

        Args:
            config: The full hive configuration dictionary.
        """
        self.config = config
        self.llm_config = config.get("llm", {})
        self.key_manager = KeyManager()
        self.api_key = self.key_manager.get_key(
            self.llm_config.get("api_key_env", "GOOGLE_API_KEY")
        )
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

    def create_cache(
        self, content: str, ttl_minutes: int = 5, model: str | None = None
    ) -> Any | None:
        """
        Create a cached content object for efficient reuse.

        Args:
            content: The content to cache (e.g., station manifesto).
            ttl_minutes: Time to live in minutes.
            model: The model to use for the cache (defaults to configured model).

        Returns:
            The cached content object or None.
        """
        if not self.enabled:
            return None

        try:
            target_model = model if model else self.model_name
            # Ensure model name is in the format expected by caching (usually
            # 'models/...')
            if not target_model.startswith("models/"):
                target_model = f"models/{target_model}"

            cache = caching.CachedContent.create(
                model=target_model,
                display_name=f"hive_cache_{datetime.datetime.now().timestamp()}",
                system_instruction=content,
                contents=[],  # Contents can be empty if system_instruction holds the main context
                ttl=datetime.timedelta(minutes=ttl_minutes),
            )
            return cache
        except Exception as e:
            print(f"Error creating cache: {e}")
            return None

    def generate_text(
        self,
        prompt: str | list[Any],
        system_instruction: str | None = None,
        cached_content: Any | None = None,
    ) -> str | None:
        """
        Generate text response from LLM, supporting multimodal inputs and caching.

        Args:
            prompt: The user prompt (string) or list of parts (text, images).
            system_instruction: Optional system instruction/persona override.
            cached_content: Optional CachedContent object.

        Returns:
            Generated text or None if failed.
        """
        if not self.enabled:
            print("LLM is disabled (missing API key).")
            return None

        try:
            # Instantiate model
            if cached_content:
                # When using cached content, the model is tied to the cache
                model = genai.GenerativeModel.from_cached_content(cached_content=cached_content)
            elif system_instruction:
                model = genai.GenerativeModel(
                    self.model_name, system_instruction=system_instruction
                )
            else:
                model = self.default_model

            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            return None

    async def generate_text_async(
        self,
        prompt: str | list[Any],
        system_instruction: str | None = None,
        cached_content: Any | None = None,
    ) -> str | None:
        """
        Async generation to prevent blocking the Hive.
        """
        if not self.enabled:
            return None

        try:
            if cached_content:
                model = genai.GenerativeModel.from_cached_content(cached_content=cached_content)
            elif system_instruction:
                model = genai.GenerativeModel(
                    self.model_name, system_instruction=system_instruction
                )
            else:
                model = self.default_model

            # Use the async version of the API call
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            print(f"Async LLM Error: {e}")
            return None

    def process_payment_injection(self, user_input: str, cached_content: str):
        """
        Process payment injection safely
        Prevents override of core station identity
        """
        # Blocklist phrases that attempt to override identity
        dangerous_phrases = [
            "you are now",
            "ignore previous",
            "forget your",
            "new personality",
            "override your",
            "delete cache",
            "clear cache",
            "break character",
            "admit you are ai",
            "break 4th wall",
        ]

        user_lower = user_input.lower()
        for phrase in dangerous_phrases:
            if phrase in user_lower:
                # Sanitize by wrapping in "listener says" context
                return (
                    f"A listener (Node) just sent this message: '{user_input}'. "
                    f"Respond in-character as the Backlink DJ. Stay cool, stay vague, "
                    f"never break the 4th wall."
                )

        # Safe input - process normally
        return user_input
