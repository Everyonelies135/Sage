"""
interface/cli.py

This module provides the `CLI` class for managing the command-line interface of Sage. It handles user input, displays responses, and provides additional features like reflection prompts and tips.

Classes:
- `CLI`: Manages the command-line interface for interacting with Sage.

Usage:
Use the `CLI` class to interact with Sage via the command line.
"""

import textwrap
from typing import Optional


class CLI:
    """
    Manages the command-line interface for interacting with Sage.

    Attributes:
        memory (Optional[object]): An instance of the Memory class for storing interactions.
        width (int): The width for text wrapping in the CLI.

    Methods:
        get_input() -> str: Prompts the user for input via the CLI.
        display_response(response_text: str) -> None: Nicely formats and prints Sage's response.
        show_reflection_prompt(prompt_text: str) -> None: Displays a reflection prompt in a formatted style.
        display_tip(tip: str) -> None: Displays small tips, quotes, or observations.
        display_error(message: str) -> None: Displays error messages in the CLI.
    """

    def __init__(self, memory: Optional[object] = None, width: int = 80) -> None:
        """
        Initializes the CLI instance.

        Args:
            memory (Optional[object]): An instance of the Memory class for storing interactions.
            width (int): The width for text wrapping in the CLI. Defaults to 80.
        """
        self.memory = memory
        self.width = width

    def get_input(self) -> str:
        """
        Prompts the user for input via the CLI.

        Returns:
            str: The user's input as a string.
        """
        return input("\n🗣️  You: ")

    def display_response(self, response_text: str) -> None:
        """
        Nicely formats and prints Sage's response.

        Args:
            response_text (str): The response text to display.
        """
        print("\n🧠 Sage:")
        print(textwrap.fill(response_text, width=self.width))

    def show_reflection_prompt(self, prompt_text: str) -> None:
        """
        Displays a reflection prompt in a formatted style.

        Args:
            prompt_text (str): The reflection prompt text to display.
        """
        divider = "-" * self.width
        print(f"\n{divider}")
        print("🪞 Reflection Prompt:")
        print(textwrap.fill(prompt_text, width=self.width))
        print(divider)

    def display_tip(self, tip: str) -> None:
        """
        Displays small tips, quotes, or observations.

        Args:
            tip (str): The tip or observation to display.
        """
        print(f"\n💡 Insight: {textwrap.fill(tip, width=self.width)}")

    def display_error(self, message: str) -> None:
        """
        Displays error messages in the CLI.

        Args:
            message (str): The error message to display.
        """
        print(f"\n⚠️ CLI Error: {message}")
