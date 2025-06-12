import unittest
from core.brain import generate_response
from core.memory import Memory


class TestCoreBrain(unittest.TestCase):
    def test_generate_response_valid_input(self) -> None:
        """Test generate_response with a valid input prompt."""
        prompt = "What is the capital of France?"
        context = {}
        response = generate_response(prompt, context)
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_generate_response_empty_prompt(self) -> None:
        """Test generate_response with an empty input prompt."""
        prompt = ""
        context = {}
        response = generate_response(prompt, context)
        self.assertEqual(response, "I need more information to assist you.")


class TestCoreMemory(unittest.TestCase):
    def setUp(self) -> None:
        """Set up a fresh Memory instance for each test."""
        self.memory = Memory()

    def test_log_interaction(self) -> None:
        """Test logging an interaction in memory."""
        self.memory.log_interaction("user", "Hello, Sage!")
        interactions = self.memory.get_context()
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0]["role"], "user")
        self.assertEqual(interactions[0]["content"], "Hello, Sage!")

    def test_summarize_recent(self) -> None:
        """Test summarizing recent interactions."""
        self.memory.log_interaction("user", "Hello, Sage!")
        self.memory.log_interaction("sage", "Hello! How can I assist you today?")
        summary = self.memory.summarize_recent(limit=1)
        self.assertIn("Hello! How can I assist you today?", summary)


if __name__ == "__main__":
    unittest.main()
