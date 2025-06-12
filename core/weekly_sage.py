"""
core/weekly_sage.py

This module provides the `WeeklySage` class for generating weekly reflections and insights. It leverages Sage's capabilities to analyze recent interactions and produce meaningful summaries and titles.

Classes:
- `WeeklySage`: A class for weekly reflections and insights.

Usage:
Use the `WeeklySage` class to reflect on the past week and generate thematic titles or insights.
"""

from typing import Optional, List, Dict, Any
from core.memory import Memory
from core.brain import generate_response


class WeeklySage:
    """
    A class for generating weekly reflections and insights.

    Attributes:
        memory (Memory): An instance of the Memory class for storing interactions.
        mode (str): The current mode of Sage (e.g., "philosopher").

    Methods:
        reflect_on_week() -> str: Produces a weekly review with themes, questions, and suggestions.
        generate_title_for_week() -> str: Creates a poetic or metaphorical title for the past week.
    """

    def __init__(self, memory: Memory, mode: str = "philosopher") -> None:
        """
        Initializes the WeeklySage instance.

        Args:
            memory (Memory): An instance of the Memory class for storing interactions.
            mode (str): The current mode of Sage. Defaults to "philosopher".
        """
        self.memory: Memory = memory
        self.mode: str = mode

    def reflect_on_week(self) -> str:
        """
        Produces a weekly review with themes, questions, and suggestions.

        Analyzes recent logs to identify:
        - Key themes
        - Emotional undercurrents
        - Questions for reflection
        - Suggestions for the upcoming week

        Returns:
            str: A structured weekly review.
        """
        recent_log: str = self.memory.summarize_recent(limit=30)

        prompt: str = (
            f"Here's a reflection log from the last week:\n\n{recent_log}\n\n"
            f"As Sage in '{self.mode}' mode, reflect on the following:\n"
            "- What are 2–3 recurring themes or emotional threads?\n"
            "- Any contradictions, doubts, or unresolved patterns?\n"
            "- Offer one provocative reflection question.\n"
            "- Suggest a framing or intention for next week.\n"
            "Keep it poetic, sharp, and gentle."
        )

        return generate_response(prompt, mode=self.mode, context=None)

    def generate_title_for_week(self) -> str:
        """
        Creates a poetic or metaphorical title for the past week.

        Returns:
            str: A title that encapsulates the week's themes and emotions.
        """
        recent_log: str = self.memory.summarize_recent(limit=20)

        prompt: str = (
            f"Based on the following user thoughts and Sage replies:\n\n{recent_log}\n\n"
            f"Invent a poetic, metaphorical title for this week — as if it were a chapter in a novel."
        )

        return generate_response(prompt, mode=self.mode, context=None)
