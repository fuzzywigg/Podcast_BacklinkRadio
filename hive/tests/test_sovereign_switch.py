import pytest
import os
from unittest.mock import MagicMock, patch
from hive.utils.gemini_client import Gemini3Client

class TestSovereignSwitch:
    
    @patch.dict(os.environ, {"GOVERNANCE_AI_MODEL": "local", "GOVERNANCE_AI_ENDPOINT": "http://localhost:8080/v1"})
    @patch("hive.utils.gemini_client.OpenAI")
    def test_local_backend_initialization(self, mock_openai):
        """Test that LocalAI backend is initialized when env var is set."""
        client = Gemini3Client()
        
        assert client.backend == "local"
        mock_openai.assert_called_with(
            base_url="http://localhost:8080/v1",
            api_key="sk-xxx-local"
        )
    
    @patch.dict(os.environ, {"GOVERNANCE_AI_MODEL": "local"})
    @patch("hive.utils.gemini_client.OpenAI")
    def test_local_generation_routing(self, mock_openai):
        """Test that generate_content routes to OpenAI client."""
        # Setup Mock
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Sovereignty acheived."
        mock_instance.chat.completions.create.return_value = mock_completion
        
        client = Gemini3Client()
        response = client.generate_content("Hello Sovereign World")
        
        assert response["text"] == "Sovereignty acheived."
        mock_instance.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {"GOVERNANCE_AI_MODEL": "gemini-pro-3", "GEMINI_API_KEY": "fake_key"})
    @patch("hive.utils.gemini_client.genai")
    def test_google_backend_default(self, mock_genai):
        """Test fallback to Google backend."""
        # Setup Mock for Google Client
        client = Gemini3Client()
        assert client.backend == "google"
        # Verify genai.Client was called
        mock_genai.Client.assert_called()
