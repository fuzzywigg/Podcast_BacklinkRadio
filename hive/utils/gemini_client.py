import json
import os
import logging
from typing import Any

# Conditional imports
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger("gemini_client")

class Gemini3Client:
    """
    Wrapper for Gemini 3 API with support for Thinking Level and Thought Signatures.
    Now updated to support Sovereign (LocalAI) backend via OpenAI compatibility.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp", force_backend: str | None = None):
        """
        Initialize the Client. Checks GOVERNANCE_AI_MODEL to decide backend.
        Args:
            model_name: The model to use.
            force_backend: Explicitly set "local" or "google" to override env vars.
        """
        self.backend = "google"
        self.client = None
        self.model_name = model_name
        
        # Check Configuration
        # We reuse the gov config or a simpler GENAI_BACKEND flag
        self.gov_model = os.environ.get("GOVERNANCE_AI_MODEL", "gemini-pro-3")
        self.local_endpoint = os.environ.get("GOVERNANCE_AI_ENDPOINT", "http://localhost:8080/v1")

        # Determine backend: Explicit force > Env Var > Default (Google)
        if force_backend:
            self.backend = force_backend
        elif self.gov_model == "local":
            self.backend = "local"
        else:
            self.backend = "google"

        if self.backend == "local":
            self._init_local_backend()
        else:
            self._init_google_backend()

    def _init_local_backend(self):
        """Initialize OpenAI client pointing to LocalAI."""
        if not OpenAI:
            logger.error("OpenAI sdk not installed. Cannot use LocalAI.")
            return

        self.backend = "local"
        # LocalAI doesn't strictly need a real key, but OpenAI client might check for one
        api_key = os.environ.get("LOCALAI_API_KEY", "sk-xxx-local") 
        
        self.client = OpenAI(
            base_url=self.local_endpoint,
            api_key=api_key
        )
        # Use a model name expected by LocalAI or just pass 'gpt-3.5-turbo' as generic alias
        # Often LocalAI requires the specific model filename or alias loaded
        self.model_name = "gpt-4" # Generic fallback or use mapped name

    def _init_google_backend(self):
        """Initialize Google GenAI client."""
        if not genai:
            logger.error("Google genai sdk not installed.")
            return

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not found in environment.")

        self.client = genai.Client(api_key=api_key)
        self.backend = "google"

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
        Generate content using the configured backend.
        """
        if self.backend == "local":
            return self._generate_local(prompt, system_instruction, response_schema)
        else:
            return self._generate_google(
                prompt, system_instruction, thinking_level, response_schema, use_thought_signature, tools
            )

    def _generate_local(self, prompt: str, system_instruction: str, response_schema: dict | None) -> dict:
        """Execute via LocalAI (OpenAI compatible)."""
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            # Check if JSON mode is requested
            response_format = None
            if response_schema:
                response_format = {"type": "json_object"}

            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format=response_format
            )
            
            content = completion.choices[0].message.content
            if response_schema:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON from LocalAI", "raw": content}
            
            return {"text": content}

        except Exception as e:
            return {"error": str(e)}

    def _generate_google(self, prompt, system_instruction, thinking_level, response_schema, use_thought_signature, tools):
        """Execute via Google GenAI."""
        if not self.client:
             return {"error": "Google Client not initialized"}

        config_args = {"thinking_config": types.ThinkingConfig(thinking_level=thinking_level)}
        if tools:
            config_args["tools"] = tools

        if response_schema:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_schema
        
        # In newer SDK, system_instruction might be part of config or method
        # We assume it goes into contents as 'model' role or config
        # For simplicity in this wrapper, if system instruction is present, we prepend it or use config
        # types.GenerateContentConfig has system_instruction in some versions
        if system_instruction:
            # check SDK version support or prepend
             config.system_instruction = system_instruction


        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
            
            if response_schema:
                try:
                    return json.loads(response.text)
                except:
                    return {"text": response.text} # Fallback
            
            return {"text": response.text}
        
        except Exception as e:
            return {"error": str(e)}

    def generate_image(self, prompt: str, aspect_ratio: str = "1:1") -> str | None:
        # TODO: Implement actual Imagen 3 wrapper
        return None

    async def live_connect(self, model: str = None):
        """
        Async context manager for a bidirectional live session with Gemini.
        Note: LocalAI might not support Bidi RPCs yet.
        """
        if self.backend == "local":
             # Wait for LocalAI Websocket support
             raise NotImplementedError("Live Connect not supported on LocalAI yet")

        import websockets
        target_model = model or self.model_name
        host = "generativelanguage.googleapis.com"
        path = f"/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.client.api_key}"
        url = f"wss://{host}{path}"

        try:
            async with websockets.connect(url) as ws:
                setup_msg = {
                    "setup": {
                        "model": f"models/{target_model}",
                        "generation_config": {"response_modalities": ["AUDIO"]},
                    }
                }
                await ws.send(json.dumps(setup_msg))
                yield ws
        except Exception as e:
            print(f"Gemini Live Connect Error: {e}")
            raise
