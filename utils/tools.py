# utils/tools.py

from datetime import datetime, timedelta
import re
import textwrap
from openai import OpenAI
from typing import Optional, List

# Centralized client initialization for LM Studio
client = OpenAI(base_url="http://localhost:1234/v1", api_key="dummy", default_headers={"Authorization": ""})

# Format a datetime object as a friendly string
def format_time(dt: Optional[datetime] = None) -> str:
    """
    Return a friendly string representation of the current time or a given datetime.
    Args:
        dt: The datetime object to format. Defaults to the current time.
    Returns:
        A string representation of the datetime in a human-readable format.
    """
    if not dt:
        dt = datetime.now()
    return dt.strftime("%A, %B %d at %I:%M %p")

# Wrap text to a specified width for readability
def wrap_text(text: str, width: int = 80) -> str:
    """
    Wrap text to a specified width for readability.
    Args:
        text: The text to wrap.
        width: The maximum width of each line.
    Returns:
        The wrapped text.
    """
    return textwrap.fill(text, width=width)

# Extract the most frequent non-trivial words from a given text
def extract_keywords(text: str, max_words: int = 5) -> List[str]:
    """
    Extract the most frequent non-trivial words from a given text.
    Args:
        text: The input text to analyze.
        max_words: The maximum number of keywords to return.
    Returns:
        A list of extracted keywords.
    """
    words = re.findall(r"\b\w+\b", text.lower())
    stopwords = set(
        [
            "the",
            "and",
            "is",
            "in",
            "it",
            "to",
            "of",
            "for",
            "a",
            "on",
            "that",
            "this",
            "you",
            "with",
            "as",
            "i",
            "be",
            "was",
            "are",
            "but",
        ]
    )
    filtered = [w for w in words if w not in stopwords and len(w) > 2]
    freq = {}
    for word in filtered:
        freq[word] = freq.get(word, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_words]]

# Determine if the given text is likely a question
def detect_question(text: str) -> bool:
    """
    Determine if the given text is likely a question.
    Args:
        text: The input text to analyze.
    Returns:
        True if the text is likely a question, False otherwise.
    """
    return text.strip().endswith("?") or text.lower().startswith(
        ("how", "what", "why", "when", "where", "who")
    )

# Calculate a human-readable time difference from a given past datetime
def friendly_time_diff(past: datetime) -> str:
    """
    Calculate a human-readable time difference from a given past datetime.
    Args:
        past: The past datetime to compare against the current time.
    Returns:
        A string representing the time difference in a human-readable format.
    """
    now = datetime.now()
    diff = now - past
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        mins = int(diff.total_seconds() / 60)
        return f"{mins} min ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hr ago"
    else:
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
