"""
core/idea_garden.py

This module provides the `IdeaGarden` class for creative idea generation and reframing. It leverages Sage's capabilities to expand, reframe, and identify themes in user interactions.

Classes:
- `IdeaGarden`: A class for generating and reframing ideas, as well as mapping recurring themes.

Usage:
Use the `IdeaGarden` class to grow ideas, reframe mental blocks, and identify thematic clusters in recent interactions.
"""

from typing import Any
from core.brain import generate_response


class IdeaGarden:
    """
    A class for creative idea generation and reframing.

    Attributes:
        memory (Any): An instance of the Memory class for storing interactions.
        mode (str): The current mode of Sage (e.g., "buddy", "fixer").

    Methods:
        grow_idea(seed_idea: str) -> str: Expands a rough idea into structured, stylized directions.
        reframe_block(stuck_thought: str) -> str: Reframes mental blocks into new perspectives.
        map_weekly_themes() -> str: Identifies recurring themes or motifs in recent interactions.
    """

    def __init__(self, memory: Any, mode: str = "default") -> None:
        """
        Initializes the IdeaGarden instance.

        Args:
            memory (Any): An instance of the Memory class for storing interactions.
            mode (str): The current mode of Sage. Defaults to "default".
        """
        self.memory = memory
        self.mode = mode

    def grow_idea(self, seed_idea: str) -> str:
        """
        Expands a rough idea into structured, stylized directions.

        Args:
            seed_idea (str): The initial idea seed to expand.

        Returns:
            str: A structured response with possible directions for the idea.
        """
        prompt = (
            f"I have an idea seed: '{seed_idea}'.\n\n"
            f"You're Sage, my creative thought partner. Help me grow this into something structured, interesting, and reflective of my tone. "
            f"Break it down into 2–3 possible directions, suggest formats or metaphors if relevant, and offer a small push to take it further.\n"
        )
        context = self.memory.get_context()
        return generate_response(prompt, mode=self.mode, context=context)

    def reframe_block(self, stuck_thought: str) -> str:
        """
        Reframes mental blocks into new perspectives using metaphors, inversions, or challenges.

        Args:
            stuck_thought (str): The thought or idea the user is stuck on.

        Returns:
            str: A reframed perspective or suggestion.
        """
        prompt = (
            f"I'm stuck on this: '{stuck_thought}'.\n\n"
            f"Offer a lateral reframe. You can use metaphor, inversion, or challenge the framing. "
            f"Speak like Sage in '{self.mode}' mode — with calm insight and light weirdness."
        )
        context = self.memory.get_context()
        return generate_response(prompt, mode=self.mode, context=context)

    def map_weekly_themes(self) -> str:
        """
        Identifies recurring themes or motifs in recent interactions.

        Returns:
            str: A list of theme clusters or motifs with playful labels and notes.
        """
        summary = self.memory.summarize_recent(limit=15)
        prompt = (
            f"Here’s a chunk of recent conversations:\n\n{summary}\n\n"
            f"Based on this, what ideas, values, or tensions seem to be recurring? "
            f"List 2–4 subtle theme clusters or motifs, with playful labels and short notes."
        )
        return generate_response(prompt, mode=self.mode, context=None)
