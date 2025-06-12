"""
core/classification.py

This module provides functions for classifying user input for Sage.

Functions:
- `detect_classification_lm(user_input: str) -> str`: Detects the classification for Sage to operate in based on user input.

Dependencies:
- LM Studio for local language model inference.
- `log_event` for logging events.
- `client` for interacting with the language model.

Usage:
This function is used to classify user input to guide Sage's behavior.
"""

# core/classification.py

from typing import Optional
from utils.logger import log_event
from utils.tools import client


def detect_classification_lm(user_input: str) -> str:
    """
    Detects the classification for Sage to operate in based on user input.

    Args:
        user_input (str): The user's input string.

    Returns:
        str: The detected classification. Returns "default" if an error occurs or the result is unexpected.
    """
    system_prompt = (
        "You are a helpful AI classifier for an assistant named Sage. "
        "Classify the user's input appropriately."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Classify this input:\n\n"
                f"Input:\n{user_input}\n\n"
                f"Return only the classification."
            ),
        },
    ]

    try:
        log_event("🧠 Inferring Sage classification via LM Studio")
        response = client.chat.completions.create(
            model="local-model", messages=messages, temperature=0, max_tokens=20
        )
        result = response.choices[0].message.content.strip().lower()
        return result
    except Exception as e:
        log_event(f"⚠️ Classification detection error: {e}", level="error")
        return "default"
