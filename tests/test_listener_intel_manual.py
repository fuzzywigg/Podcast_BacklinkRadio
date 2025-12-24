import unittest
from unittest.mock import patch, MagicMock
import os

from hive.bees.research.listener_intel_bee import ListenerIntelBee

class TestListenerIntelBeeIntegration(unittest.TestCase):
    def setUp(self):
        self.bee = ListenerIntelBee()
        self.location = {"city": "New York", "country": "US", "timezone": "America/New_York"}

    def test_fallback_when_no_keys(self):
        """Test that we get fallback data when no API keys are present."""
        # Ensure env vars are not set
        with patch.dict(os.environ, {}, clear=True):
            result = self.bee._get_local_context(self.location)

            self.assertEqual(result["weather"]["condition"], "simulated")
            self.assertIn("[AI ESTIMATION]", result["weather"]["description"])

            self.assertTrue(len(result["notable"]) == 1)
            self.assertIn("[AI SIMULATION]", result["notable"][0]["title"])

    @patch('requests.get')
    def test_weather_api_success(self, mock_get):
        """Test successful weather API call."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"main": "Clouds", "description": "broken clouds"}],
            "main": {"temp": 15.5}
        }
        mock_get.return_value = mock_response

        # Set API key
        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key", "NEWS_API_KEY": ""}):
            # We focus on weather here, news will fallback
            result = self.bee._get_local_context(self.location)

            self.assertEqual(result["weather"]["condition"], "clouds")
            self.assertEqual(result["weather"]["temp_c"], 15.5)
            self.assertEqual(result["weather"]["description"], "broken clouds")

            # Check if API was called correctly
            mock_get.assert_called()
            args, kwargs = mock_get.call_args
            self.assertIn("api.openweathermap.org", args[0])
            self.assertEqual(kwargs['params']['q'], "New York,US")

    @patch('requests.get')
    def test_news_api_success(self, mock_get):
        """Test successful news API call."""
        # We need to handle multiple calls if weather is also tried.
        # But if we only set NEWS_API_KEY, weather will fallback immediately without call.

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {"title": "News 1", "source": {"name": "Source 1"}, "url": "http://1"},
                {"title": "News 2", "source": {"name": "Source 2"}, "url": "http://2"}
            ]
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"NEWS_API_KEY": "test_key", "OPENWEATHER_API_KEY": ""}):
            result = self.bee._get_local_context(self.location)

            self.assertEqual(len(result["notable"]), 2)
            self.assertEqual(result["notable"][0]["title"], "News 1")
            self.assertEqual(result["notable"][1]["source"], "Source 2")

            # Check if API was called correctly
            mock_get.assert_called()
            args, kwargs = mock_get.call_args
            self.assertIn("newsapi.org", args[0])
            self.assertEqual(kwargs['params']['country'], "us")

    @patch('requests.get')
    def test_api_failure_fallback(self, mock_get):
        """Test fallback when API call fails."""
        mock_get.side_effect = Exception("API Connection Error")

        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"}):
            result = self.bee._get_local_context(self.location)

            self.assertEqual(result["weather"]["condition"], "simulated")
            self.assertIn("[AI ESTIMATION]", result["weather"]["description"])

if __name__ == '__main__':
    unittest.main()
