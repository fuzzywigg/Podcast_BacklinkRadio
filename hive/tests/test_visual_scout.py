import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from hive.bees.research.trend_scout_bee import TrendScoutBee

class TestVisualScout:
    
    @pytest.mark.asyncio
    async def test_perform_visual_scout_no_llm(self):
        """Test failure when LLM is missing."""
        bee = TrendScoutBee()
        bee.llm_client = None
        result = await bee._perform_visual_scout("http://example.com", "find button")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_perform_visual_scout_success(self):
        """Test successful interaction simulation."""
        bee = TrendScoutBee()
        bee.llm_client = MagicMock()
        
        # Mock Gemini response
        mock_response = {
            "text": '{"action": "click", "reasoning": "Found the button using coordinates."}'
        }
        bee.llm_client.generate_content.return_value = mock_response
        
        result = await bee._perform_visual_scout("http://example.com", "find login")
        
        assert result["action"] == "click"
        assert "coordinates" in result["reasoning"] or "Found" in result["reasoning"]
        
        # Verify prompt construction (implied by success)
        bee.llm_client.generate_content.assert_called_once()
