import unittest
from unittest.mock import MagicMock, patch

from hive.bees.base_bee import BaseBee
from hive.utils.prompt_engineer import PromptEngineer


# Mock Bee implementation for testing
class TestBee(BaseBee):
    BEE_TYPE = "test_bee"
    BEE_NAME = "Test Bee"
    CATEGORY = "test"

    def work(self, task=None):
        return {"status": "done"}


class TestGemini3Integration(unittest.TestCase):
    def setUp(self):
        # Ensure we don't actually hit the API unless we want to integration test
        # validation logic
        self.mock_client_patcher = patch("hive.utils.gemini_client.Gemini3Client")
        self.mock_client_cls = self.mock_client_patcher.start()
        self.mock_client_instance = MagicMock()
        self.mock_client_cls.return_value = self.mock_client_instance

        # Test Bee
        self.bee = TestBee()
        # Manually inject our mock client to be sure
        self.bee.llm_client = self.mock_client_instance

    def tearDown(self):
        self.mock_client_patcher.stop()

    def test_thought_signature_flow(self):
        """
        Verify that if we enable thought signatures, the client handles it.
        (Initialization logic check, not API check).
        """
        prompt = PromptEngineer("Tester", "Test Goal")

        # Mock response from Gemini
        self.mock_client_instance.generate_content.return_value = {
            "text": '{"result": "success"}',
            # In real usage, the client would handle the thought_signature object internally
            # or return it if we modified the wrapper to be explicit about it.
        }

        # 1. First Turn
        self.bee._ask_llm_json(prompt, "Hello world")

        # Assert call was made
        self.assertTrue(self.mock_client_instance.generate_content.called)

        # Check args passed to generate_content
        args, kwargs = self.mock_client_instance.generate_content.call_args
        self.assertEqual(kwargs.get("thinking_level"), "low")  # Default

        # 2. Verify we can request High Reasoning
        # Current BaseBee implementation defaults to "low".
        # Future improvement: allow passing 'thinking_level' to _ask_llm_json

    def test_structured_output_parsing(self):
        """Test the JSON parsing resilience."""
        # Case: Markdown code block wrapper
        self.mock_client_instance.generate_content.return_value = {
            "text": '```json\n{"data": "valid"}\n```'
        }
        res = self.bee._ask_llm_json(PromptEngineer("Role", "Goal"), "Input")
        self.assertEqual(res["data"], "valid")


if __name__ == "__main__":
    unittest.main()
