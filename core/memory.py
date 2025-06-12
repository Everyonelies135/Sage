"""
core/memory.py

This module provides a class and utility functions for managing Sage's memory. The memory stores user interactions and provides context for generating responses.

Classes:
- `Memory`: Manages the memory of user interactions, including logging, retrieving, summarizing, and clearing memory.

Functions:
- `read_json_file(file_path: Path) -> Dict`: Reads a JSON file and returns its contents.
- `write_json_file(file_path: Path, data: Dict) -> None`: Writes data to a JSON file.

Usage:
Use the `Memory` class to log interactions and retrieve context for Sage's responses.
"""

# core/memory.py

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from utils.logger import log_event
from utils.tools import client
from sentence_transformers import SentenceTransformer, util
import numpy as np

MEMORY_FILE = Path("data/memory.json")
LONG_TERM_MEMORY_FILE = Path("data/long_term_memory.json")
MAX_HISTORY = 50  # messages to retain in context
LONG_TERM_MAX = 500
HIGH_IMPORTANCE_THRESHOLD = 4
LOW_IMPORTANCE_THRESHOLD = 2


# Abstract file I/O logic for memory into a utility function.
def read_json_file(file_path: Path) -> Dict:
    """
    Reads a JSON file and returns its contents.

    Args:
        file_path (Path): The path to the JSON file.

    Returns:
        Dict: The contents of the JSON file.
    """
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_json_file(file_path: Path, data: Dict) -> None:
    """
    Writes data to a JSON file.

    Args:
        file_path (Path): The path to the JSON file.
        data (Dict): The data to write to the file.
    """
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def read_long_term_memory() -> Dict:
    """
    Reads the long-term memory file and returns its contents.

    Returns:
        Dict: The contents of the long-term memory file.
    """
    if LONG_TERM_MEMORY_FILE.exists():
        with LONG_TERM_MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"log": []}


def write_long_term_memory(data: Dict) -> None:
    """
    Writes data to the long-term memory file.

    Args:
        data (Dict): The data to write to the file.
    """
    with LONG_TERM_MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def classify_mood_and_topic(message: str) -> Dict:
    """
    Use the LLM to classify the mood and topic of a message, and return a color for the mood.

    Args:
        message (str): The message to classify.

    Returns:
        Dict: {"mood": ..., "topic": ..., "color": ...}
    """
    from utils.tools import client
    import json as _json
    import re
    prompt = (
        "Classify the following message for mood (e.g., happy, sad, curious, frustrated, neutral), "
        "topic (e.g., work, relationships, self, ideas, health, other), and suggest a CSS color (hex or rgb) that best represents the mood. "
        'Respond in JSON: {"mood": ..., "topic": ..., "color": ...}.\n\nMessage: '
        + message
    )
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "You are a helpful classifier."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=80,
        )
        content = response.choices[0].message.content
        # Try to extract JSON substring
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != -1:
            json_str = content[start:end]
            try:
                return _json.loads(json_str)
            except Exception:
                # Fallback: try to extract with regex
                mood = re.search(r'"?mood"?\s*[:=]\s*"?([\w\- ]+)"?', json_str, re.I)
                topic = re.search(r'"?topic"?\s*[:=]\s*"?([\w\- ]+)"?', json_str, re.I)
                color = re.search(r'"?color"?\s*[:=]\s*"?([#\w\(\), ]+)"?', json_str, re.I)
                result = {}
                if mood:
                    result["mood"] = mood.group(1).strip()
                if topic:
                    result["topic"] = topic.group(1).strip()
                if color:
                    result["color"] = color.group(1).strip()
                if result:
                    return result
    except Exception as e:
        log_event(f"Mood/topic/color classification error: {e}", level="warning")
    return {}


def classify_importance(message: str) -> int:
    """
    Use the LLM to classify the importance of a message (1-5).

    Args:
        message (str): The message to classify.

    Returns:
        int: An integer (default 1 if uncertain).
    """
    prompt = (
        "On a scale of 1 to 5, how important is the following message for understanding the user's life, goals, or emotional state? "
        "Respond with a single integer (1=not important, 5=very important).\n\nMessage: "
        + message
    )
    try:
        response = client.chat.completions.create(
            model="local-model",
            messages=[
                {"role": "system", "content": "You are a helpful classifier."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=5,
        )
        content = response.choices[0].message.content.strip()
        for c in content:
            if c in "12345":
                return int(c)
    except Exception as e:
        log_event(f"Importance classification error: {e}", level="warning")
    return 1


class Memory:
    """
    Manages the memory of user interactions, including logging, retrieving, summarizing, and clearing memory.

    Attributes:
        memory (Dict): A dictionary containing the memory log.

    Methods:
        log_interaction(role: str, message: str, tags: Optional[List[str]] = None, metadata: Optional[Dict] = None, importance: Optional[int] = None, context_snapshot: Optional[List] = None) -> None: Logs an interaction in memory.
        get_context() -> List[tuple]: Retrieves the context as a list of (role, message) tuples.
        get_last_user_message() -> Optional[str]: Retrieves the last user message from memory.
        summarize_recent(limit: int) -> str: Summarizes the most recent interactions.
        search_memory(query: Optional[str] = None, tag: Optional[str] = None, role: Optional[str] = None) -> List[Dict]: Searches memory log for entries matching query, tag, or role.
        clear_memory() -> None: Clears the memory log.
    """

    _embedding_model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._embedding_model is None:
            cls._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._embedding_model

    def _get_message_embedding(self, message: str):
        model = self.get_embedding_model()
        return model.encode(message, convert_to_numpy=True)

    def _ensure_embeddings(self):
        """
        Ensure all memory entries have an embedding. Adds 'embedding' field if missing.
        """
        updated = False
        for entry in self.memory["log"]:
            if "embedding" not in entry and entry.get("message"):
                entry["embedding"] = self._get_message_embedding(entry["message"]).tolist()
                updated = True
        if updated:
            self._save_memory()

    def semantic_search(self, query: str, top_k: int = 5):
        """
        Fetch the most similar memories to the query using semantic similarity.
        Returns a list of (score, entry) tuples.
        """
        self._ensure_embeddings()
        model = self.get_embedding_model()
        query_emb = model.encode(query, convert_to_numpy=True)
        scored = []
        for entry in self.memory["log"]:
            emb = entry.get("embedding")
            if emb is not None:
                score = util.cos_sim(query_emb, np.array(emb))[0][0]
                scored.append((float(score), entry))
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[:top_k]

    def __init__(self) -> None:
        """
        Initializes the Memory instance and loads memory from the file.
        """
        self.memory: Dict[str, List[Dict]] = {"log": []}
        self._load_memory()

    def _load_memory(self) -> None:
        """
        Loads memory from the memory file. If no file exists, starts with an empty memory.
        """
        self.memory = read_json_file(MEMORY_FILE)
        if self.memory:
            log_event("Memory loaded from file.", level="debug")
        else:
            log_event("No existing memory file found. Starting fresh.", level="debug")

    def _save_memory(self) -> None:
        """
        Saves the current memory to the memory file.
        """
        write_json_file(MEMORY_FILE, self.memory)
        log_event("Memory saved to disk.")

    def log_interaction(
        self,
        role: str,
        message: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        importance: Optional[int] = None,
        context_snapshot: Optional[List] = None,
    ) -> None:
        """
        Logs an interaction in memory and trims the log to the maximum history size.

        Args:
            role (str): The role of the interaction (e.g., "user", "sage").
            message (str): The message content of the interaction.
            tags (Optional[List[str]], optional): Tags for the interaction (e.g., ["joke", "casual"]).
            metadata (Optional[Dict], optional): Additional metadata (e.g., mood, topic).
            importance (Optional[int], optional): Importance score (1-5). Defaults to 1.
            context_snapshot (Optional[List], optional): Full context to save for important memories.
        """
        # Auto-classify mood/topic for user and sage messages
        auto_meta = classify_mood_and_topic(message)
        if auto_meta:
            if not metadata:
                metadata = {}
            metadata.update(auto_meta)
            if "mood" in auto_meta:
                if not tags:
                    tags = []
                tags.append(auto_meta["mood"])
            if "topic" in auto_meta:
                if not tags:
                    tags = []
                tags.append(auto_meta["topic"])
        # Auto-classify importance if not provided
        if importance is None:
            importance = classify_importance(message)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message.strip(),
            "importance": importance,
        }
        if tags:
            entry["tags"] = tags
        if metadata:
            entry["metadata"] = metadata
        # If importance is high, store extra context snapshot
        if importance >= HIGH_IMPORTANCE_THRESHOLD and context_snapshot:
            entry["context_snapshot"] = context_snapshot
        # Add embedding for the message
        entry["embedding"] = self._get_message_embedding(message).tolist()
        self.memory["log"].append(entry)
        # Automatically trim memory if over MAX_HISTORY
        if len(self.memory["log"]) > MAX_HISTORY:
            self.trim_memory()
        else:
            self._save_memory()
        log_event(
            f"Interaction logged: {role} — '{message[:60]}...' (importance={importance})"
        )

    def promote_memory(self, idx: int, new_importance: int = 5) -> None:
        """
        Promote a memory entry to higher importance by index.

        Args:
            idx (int): The index of the memory entry to promote.
            new_importance (int, optional): The new importance level. Defaults to 5.
        """
        if 0 <= idx < len(self.memory["log"]):
            self.memory["log"][idx]["importance"] = new_importance
            log_event(f"Memory at idx {idx} promoted to importance {new_importance}.")
            self._save_memory()

    def demote_memory(self, idx: int, new_importance: int = 1) -> None:
        """
        Demote a memory entry to lower importance by index.

        Args:
            idx (int): The index of the memory entry to demote.
            new_importance (int, optional): The new importance level. Defaults to 1.
        """
        if 0 <= idx < len(self.memory["log"]):
            self.memory["log"][idx]["importance"] = new_importance
            log_event(f"Memory at idx {idx} demoted to importance {new_importance}.")
            self._save_memory()

    def move_high_importance_to_long_term(self) -> None:
        """
        Move high-importance (>= HIGH_IMPORTANCE_THRESHOLD) entries from short-term to long-term memory file.
        """
        long_term = read_long_term_memory()
        high = [e for e in self.memory["log"] if e.get("importance", 1) >= HIGH_IMPORTANCE_THRESHOLD]
        # Remove from short-term
        self.memory["log"] = [
            e for e in self.memory["log"] if e.get("importance", 1) < HIGH_IMPORTANCE_THRESHOLD
        ]
        # Add to long-term, avoid duplicates
        for entry in high:
            if entry not in long_term["log"]:
                long_term["log"].append(entry)
        # Trim long-term if needed
        if len(long_term["log"]) > LONG_TERM_MAX:
            long_term["log"] = long_term["log"][-LONG_TERM_MAX:]
        write_long_term_memory(long_term)
        self._save_memory()
        log_event(f"Moved {len(high)} high-importance entries to long-term memory.")

    def get_long_term_context(self, limit: int = 20) -> List[tuple]:
        """
        Retrieve the most recent entries from long-term memory.

        Args:
            limit (int, optional): The number of entries to retrieve. Defaults to 20.

        Returns:
            List[tuple]: A list of (role, message) tuples from long-term memory.
        """
        long_term = read_long_term_memory()
        return [(e["role"], e["message"]) for e in long_term["log"][-limit:]]

    def trim_memory(self) -> None:
        """
        Advanced memory management: keep all high-importance (>= HIGH_IMPORTANCE_THRESHOLD) entries,
        but summarize or remove low-importance (<= LOW_IMPORTANCE_THRESHOLD) entries if over MAX_HISTORY.
        """
        # Separate entries by importance
        high = [e for e in self.memory["log"] if e.get("importance", 1) >= HIGH_IMPORTANCE_THRESHOLD]
        medium = [e for e in self.memory["log"] if LOW_IMPORTANCE_THRESHOLD < e.get("importance", 1) < HIGH_IMPORTANCE_THRESHOLD]
        low = [e for e in self.memory["log"] if e.get("importance", 1) <= LOW_IMPORTANCE_THRESHOLD]

        # Step 1: Prioritize keeping high and medium importance entries
        keep = high + medium

        # Step 2: If the combined high and medium entries exceed MAX_HISTORY, trim the oldest medium entries
        if len(keep) > MAX_HISTORY:
            num_high = len(high)
            num_medium_to_keep = max(0, MAX_HISTORY - num_high)  # Ensure non-negative
            keep = high + medium[-num_medium_to_keep:]  # Keep newest medium entries

        # Step 3: If, after trimming medium, we are still over MAX_HISTORY (only high importance left), trim the oldest high entries
        # This should be rare, only happening if MAX_HISTORY is smaller than the number of high importance items.
        if len(keep) > MAX_HISTORY:
            keep = keep[-MAX_HISTORY:]  # Keep the newest high importance entries

        # Step 4: Optionally, summarize the low-importance entries that are being removed
        if low:
            summary_text = "\n".join(
                f"{e['role'].capitalize()}: {e['message']}" for e in low
            )
            from core.brain import generate_response  # Keep import local to avoid circular dependency issues at module level

            summary = generate_response(
                f"Summarize these less important memories in 2-3 sentences for future context.\n\n{summary_text}",
                mode="default",
                context=None,
            )
            # Insert the summary at the beginning of the kept memories
            keep.insert(
                0,
                {
                    "role": "system",
                    "message": f"Summary of less important memories: {summary}",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 1,  # Summary itself has low importance
                },
            )

        # Step 5: Update the memory log with the trimmed and potentially summarized list
        self.memory["log"] = keep
        self._save_memory()  # Save the trimmed short-term memory

        # Step 6: Move any remaining high-importance entries (if any were trimmed in step 3, they won't be moved here)
        self.move_high_importance_to_long_term()  # Move remaining high-importance entries to long-term storage

        log_event(f"Memory trimmed. Now {len(self.memory['log'])} entries remain.")

    def get_context(self) -> List[tuple]:
        """
        Retrieves the context as a list of (role, message) tuples.

        Returns:
            List[tuple]: A list of tuples containing the role and message of each interaction.
        """
        return [(entry["role"], entry["message"]) for entry in self.memory["log"]]

    def get_last_user_message(self) -> Optional[str]:
        """
        Retrieves the last user message from memory.

        Returns:
            Optional[str]: The last user message, or None if no user message exists.
        """
        for entry in reversed(self.memory["log"]):
            if entry["role"] == "user":
                return entry["message"]
        return None

    def search_memory(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        role: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search memory log for entries matching query, tag, or role.

        Args:
            query (Optional[str], optional): Text to search for in messages.
            tag (Optional[str], optional): Tag to filter by.
            role (Optional[str], optional): Role to filter by (e.g., 'user', 'sage').

        Returns:
            List[Dict]: Matching memory entries.
        """
        results = []
        for entry in self.memory["log"]:
            if query and query.lower() not in entry["message"].lower():
                continue
            if tag and ("tags" not in entry or tag not in entry["tags"]):
                continue
            if role and entry["role"] != role:
                continue
            results.append(entry)
        return results

    def summarize_recent(self, limit: int = 10) -> str:
        """
        Summarizes the most recent interactions.

        Args:
            limit (int): The number of recent interactions to include in the summary.

        Returns:
            str: A summary of the most recent interactions.
        """
        summary = "\n".join(
            f"{entry['role'].capitalize()}: {entry['message']}"
            + (f" [tags: {', '.join(entry['tags'])}]" if "tags" in entry else "")
            for entry in self.memory["log"][-limit:]
        )
        log_event(f"Recent memory summarized (last {limit} entries).", level="debug")
        return summary

    def summarize_long_term(self, min_entries: int = 20) -> str:
        """
        Summarizes the long-term memory by condensing all entries into a high-level summary.

        Args:
            min_entries (int): Minimum number of entries before summarizing.

        Returns:
            str: A long-term summary of memory, or a message if not enough data.
        """
        long_term = read_long_term_memory()
        if len(long_term["log"]) < min_entries:
            return "Not enough long-term memory entries for a summary."
        summary_text = "\n".join(
            f"{entry['role'].capitalize()}: {entry['message']}"
            for entry in long_term["log"][-min_entries:]
        )
        # Use Sage itself to summarize
        from core.brain import generate_response

        prompt = f"Summarize the following long-term memory log into a high-level overview of key topics, emotional trends, and recurring themes.\n\n{summary_text}\n\nSummary:"
        return generate_response(prompt, mode="default", context=None)

    def clear_memory(self) -> None:
        """
        Clears the memory log and saves the empty memory to the file.
        """
        self.memory = {"log": []}
        self._save_memory()
        log_event("Memory cleared by user.")
