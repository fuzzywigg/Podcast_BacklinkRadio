import json
import os
from typing import Any

from google import genai
from google.genai import types


class Gemini3Client:
    """
    Wrapper for Gemini 3 API with support for Thinking Level and Thought Signatures.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Gemini 3 Client.
        defaults to 2.0-flash-exp until 3-pro-preview is widely available/stable
        change default to 'gemini-3-pro-preview' when ready.
        """
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            # Fallback for old env var
            self.api_key = os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment.")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = model_name
        self.last_thought_signature = None

    def generate_content(
        self,
        prompt: str,
        system_instruction: str = None,
        thinking_level: str = "low",
        response_schema: dict[str, Any] | None = None,
        use_thought_signature: bool = False,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Generate content using Gemini 3 features.

        Args:
            prompt: User input.
            system_instruction: System role/goal.
            thinking_level: "low", "high", "minimal", "medium".
            response_schema: dict describing the desired JSON output structure.
            use_thought_signature: If True, includes previous thought signature (if any).
            tools: List of tools to enable (e.g. [{'google_search': {}}]).

        Returns:
            Dict containing text response or parsed JSON.
        """

        config_args = {"thinking_config": types.ThinkingConfig(thinking_level=thinking_level)}

        if tools:
            config_args["tools"] = tools

        # Handle Structured Output
        if response_schema:
            config_args["response_mime_type"] = "application/json"
            # In a real impl, we'd convert the dict schema to pydantic or use raw schema if supported
            # For now, we pass the schema dict directly if the SDK supports it, or rely on prompt engineering + MIME type
            config_args["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_args)

        # Construct message parts
        contents = []

        if use_thought_signature and self.last_thought_signature:
            # Opaque thought signature handling would go here
            # Currently simplistic as per docs (implicit in conversation history for chat, explicit for tools)
            pass

        # Call API
        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

            # Capture thought signature for next turn (if present)
            # This is a simplification; real handling requires parsing parts
            # self.last_thought_signature = response.candidates[0].content.parts[0].thought_signature

            if response_schema:
                return json.loads(response.text)

            return {"text": response.text}

        except Exception as e:
            return {"error": str(e)}

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> str | None:
        """
        Generate an image using Imagen 3 via Gemini API (if available).
        Currently a placeholder for future 'Low Lift' activation.

        Args:
           prompt: The image description.
           aspect_ratio: '1:1', '16:9', '9:16'

        Returns:
           URL or base64 string of image, or None if failed.
        """
        # TODO: Implement actual Imagen 3 wrapper when 'google-genai' SDK stabilizes image support
        # logic:
        # response = self.client.models.generate_images(
        #    model='imagen-3.0-generate-001',
        #    prompt=prompt,
        #    config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio=aspect_ratio)
        # )
        # return response.generated_images[0].image.uri
        return None

    async def live_connect(self, model: str = None):
        """
        Async context manager for a bidirectional live session with Gemini.
        Returns a websocket connection ready to send/receive Bidi RPCs.
        """
        import json

        import websockets  # Lazy import

        target_model = model or self.model_name
        # Note: The host and path might vary based on the exact Alpha version.
        # Using the standard path from the cookbook for v1alpha.
        host = "generativelanguage.googleapis.com"
        path = f"/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
        url = f"wss://{host}{path}"

        try:
            async with websockets.connect(url) as ws:
                # 1. Send Setup Message
                setup_msg = {
                    "setup": {
                        "model": f"models/{target_model}",
                        "generation_config": {"response_modalities": ["AUDIO"]},
                    }
                }
                await ws.send(json.dumps(setup_msg))

                # 2. Wait for Setup Complete (simplified handshake)
                # In a robust app, we'd wait for specific response, but here we yield immediately
                # effectively handing control to the caller (Main Service)
                yield ws

        except Exception as e:
            print(f"Gemini Live Connect Error: {e}")
            raise
