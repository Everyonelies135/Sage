"""
core/brain.py

This module contains the core logic for generating responses.

Functions:
- `generate_response(user_input: str, context: Optional[List[Tuple[str, str]]] = None) -> str`: Generates a response based on user input and context.

Dependencies:
- `SYSTEM_PROMPTS` for predefined system prompts.

Usage:
These functions are used by the main application to process user input and generate appropriate responses.
"""

# core/brain.py

from typing import Optional, List, Tuple
from core.prompt_engine import PromptEngine  # Import PromptEngine
from config import SYSTEM_PROMPTS, PERSONALITY_PROFILE
from utils.logger import log_event
from utils.tools import client


def _get_personality_summary() -> str:
    """
    Returns a string summary of Sage's overarching personality traits, quirks, and tone.

    Returns:
        str: A summary of personality traits, quirks, and tone.
    """
    if not PERSONALITY_PROFILE:
        return ""
    traits = ", ".join(PERSONALITY_PROFILE.get("core_traits", []))  # Join core traits
    quirks = ", ".join(PERSONALITY_PROFILE.get("quirks", []))      # Join quirks
    tone = PERSONALITY_PROFILE.get("tone", "")                       # Get tone
    summary = f"Core traits: {traits}. Quirks: {quirks}. Tone: {tone}"
    return summary.strip()


def _get_last_user_mood(context: Optional[List[Tuple[str, str]]]) -> Optional[str]:
    """
    Extracts the mood tag from the last user message in context, if available.

    Args:
        context (Optional[List[Tuple[str, str]]]): A list of previous interactions for context.

    Returns:
        Optional[str]: The mood tag of the last user message, if available.
    """
    if not context:
        return None
    from core.memory import Memory

    memory = Memory()
    # Iterate backwards through context to find the last user message
    for role, message in reversed(context):
        if role == "user":
            # Search memory for this message to get tags/metadata
            matches = memory.search_memory(query=message, role="user")
            if (
                matches
                and "metadata" in matches[-1]
                and "mood" in matches[-1]["metadata"]
            ):
                return matches[-1]["metadata"]["mood"]
    return None


def _get_last_user_topic(context: Optional[List[Tuple[str, str]]]) -> Optional[str]:
    """
    Extracts the topic tag from the last user message in context, if available.

    Args:
        context (Optional[List[Tuple[str, str]]]): A list of previous interactions for context.

    Returns:
        Optional[str]: The topic tag of the last user message, if available.
    """
    if not context:
        return None
    from core.memory import Memory

    memory = Memory()
    for role, message in reversed(context):
        if role == "user":
            matches = memory.search_memory(query=message, role="user")
            if (
                matches
                and "metadata" in matches[-1]
                and "topic" in matches[-1]["metadata"]
            ):
                return matches[-1]["metadata"]["topic"]
    return None


def generate_response(
    user_input: str,
    context: Optional[List[Tuple[str, str]]] = None,
    prompt_engine: Optional[PromptEngine] = None,  # Add prompt_engine parameter
) -> str:
    """
    Generates a response based on user input and context.

    Args:
        user_input (str): The user's input string.
        context (Optional[List[Tuple[str, str]]], optional): A list of previous interactions for context. Each interaction is a tuple of (role, message).
        prompt_engine (Optional[PromptEngine], optional): An instance of PromptEngine to generate prompts.

    Returns:
        str: The generated response from Sage.

    Raises:
        RuntimeError: If there is an error during response generation.
    """
    from config import (
        SYSTEM_PROMPTS,
    )  # Keep this if you still use SYSTEM_PROMPTS as fallback

    log_event(
        f"[GENERATION] 🔍 Starting response generation. User Input: {user_input[:50]}..."
    )

    # Step 1: Retrieve and summarize context for the LLM
    context_summary = None
    if context:
        log_event(f"[CONTEXT] 📚 Analyzing context for relevance. Context length: {len(context)}")
        from utils.tools import extract_keywords
        keywords = extract_keywords(user_input, max_words=5)
        log_event(f"[CONTEXT] Extracted keywords from user input: {keywords}", level="debug")
        # Collect unique relevant messages (case-insensitive, no duplicates)
        seen = set()
        relevant_messages = []
        for role, message in reversed(context[-20:]):  # Look further back for more context
            msg_text = message.strip().lower()
            if any(kw in msg_text for kw in keywords) and msg_text not in seen:
                relevant_messages.append(f"{role.capitalize()}: {message.strip()}")
                seen.add(msg_text)
            if len(relevant_messages) >= 8:
                break
        relevant_messages = list(reversed(relevant_messages))  # Restore chronological order
        log_event(f"[CONTEXT] Relevant messages for summarization: {relevant_messages}", level="debug")
        if relevant_messages:
            try:
                # Use a system message to set summarizer role, and a user message with the content
                system_msg = "You are a helpful assistant that summarizes conversations. Always respond with a concise summary of 2-3 full sentences, not just a phrase."
                user_msg = (
                    "Summarize the following conversation context in 2-3 sentences, focusing on the main topics and any important details.\n\n"
                    + "\n".join(relevant_messages)
                )
                log_event(f"[CONTEXT] LLM summarization prompt: {user_msg}", level="debug")
                
                try:
                    # Add timeout to prevent hanging
                    import requests.exceptions
                    summary_response = client.chat.completions.create(
                        model="local-model",
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg}
                        ],
                        temperature=0.3,
                        max_tokens=120,
                        timeout=5,  # Add timeout
                    )
                    context_summary = summary_response.choices[0].message.content.strip()
                    log_event(f"[CONTEXT] Context summary generated for user input.", level="info")
                    log_event(f"[CONTEXT] {context_summary}", level="info")
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    # Fallback to a simpler approach if LLM is unavailable
                    log_event(f"[CONTEXT] LLM connection error: {e}. Using fallback summarization.", level="warning")
                    context_summary = " ".join(relevant_messages)[:400].rsplit(".", 1)[0] + "."
            except Exception as e:
                context_summary = " ".join(relevant_messages)[:400].rsplit(".", 1)[0] + "."
                log_event(f"[CONTEXT] LLM summarization failed, fallback to joined messages. Error: {e}", level="warning")
        else:
            # Fallback: summarize last 4 messages (user/sage only) if no relevant found
            fallback_msgs = [f"{role.capitalize()}: {msg.strip()}" for role, msg in context[-8:] if role in ("user", "sage")]
            fallback_msgs = fallback_msgs[-4:]
            log_event(f"[CONTEXT] Fallback messages for summarization: {fallback_msgs}", level="debug")
            if fallback_msgs:
                try:
                    system_msg = "You are a helpful assistant that summarizes conversations. Always respond with a concise summary of 1-2 full sentences, not just a phrase."
                    user_msg = (
                        "Summarize the following recent conversation in 1-2 sentences for context:\n\n"
                        + "\n".join(fallback_msgs)
                    )
                    log_event(f"[CONTEXT] Fallback LLM summarization prompt: {user_msg}", level="debug")
                    
                    try:
                        # Add timeout to prevent hanging
                        import requests.exceptions
                        summary_response = client.chat.completions.create(
                            model="local-model",
                            messages=[
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": user_msg}
                            ],
                            temperature=0.3,
                            max_tokens=80,
                            timeout=5,  # Add timeout
                        )
                        context_summary = summary_response.choices[0].message.content.strip()
                        log_event(f"[CONTEXT] Fallback context summary generated.", level="info")
                        log_event(f"[CONTEXT] {context_summary}", level="info")
                    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                        # Fallback to a simpler approach if LLM is unavailable
                        log_event(f"[CONTEXT] LLM connection error: {e}. Using simple fallback.", level="warning")
                        context_summary = " ".join(fallback_msgs)[:200].rsplit(".", 1)[0] + "."
                except Exception as e:
                    context_summary = " ".join(fallback_msgs)[:200].rsplit(".", 1)[0] + "."
                    log_event(f"[CONTEXT] Fallback LLM summarization failed. Error: {e}", level="warning")
            else:
                context_summary = ""
                log_event(f"[CONTEXT] No relevant or fallback context found for user input.", level="info")

    # Step 2: Extract mood, topic, and personality for prompt adaptation
    user_mood = _get_last_user_mood(context)
    user_topic = _get_last_user_topic(context)
    personality_summary = _get_personality_summary()

    # Step 3: Generate the prompt using PromptEngine if available
    if prompt_engine:
        log_event("[PROMPT_ENGINE] ⚙️ Using PromptEngine to generate prompt.")
        # Use the prompt engine to format the prompt with all relevant details
        formatted_prompt = prompt_engine.format_prompt(
            user_input=user_input,
            context_summary=context_summary,
            mood=user_mood,
            personality=personality_summary,  # Pass personality summary
        )
        # Use the formatted prompt directly as the system message
        messages = [
            {"role": "system", "content": formatted_prompt},
            {"role": "user", "content": user_input},
        ]
    else:
        # Fallback to original logic if prompt_engine is not provided
        log_event("[PROMPT_ENGINE] ⚠️ PromptEngine not provided, using default logic.")
        system_prompt = SYSTEM_PROMPTS["default"]
        if personality_summary:
            system_prompt = (
                f"{system_prompt}\n\nSage's overarching personality: {personality_summary}"
            )
        # Add mood/topic adjustments to the system prompt
        mood_sensitive = user_mood in ["sad", "frustrated", "angry", "anxious", "upset"]
        if mood_sensitive:
            system_prompt += "\n\nThe user seems to be in a difficult mood (e.g., sad or frustrated). Respond with extra empathy, warmth, and encouragement."
        if user_topic == "work":
            system_prompt += (
                "\n\nThe topic is work. Be practical, focused, and offer actionable advice."
            )
        elif user_topic == "relationships":
            system_prompt += "\n\nThe topic is relationships. Be especially compassionate, understanding, and supportive."
        elif user_topic == "health":
            system_prompt += (
                "\n\nThe topic is health. Be gentle, reassuring, and encourage self-care."
            )
        # Build the messages list for the LLM
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            for role, message in context[-6:]:
                # Map 'sage' role to 'assistant' for LLM compatibility
                if role == "sage":
                    role = "assistant"
                messages.append({"role": role, "content": message})
        messages.append({"role": "user", "content": user_input})

    log_event(
        f"[MESSAGES] 📤 Messages prepared for API call. Total messages: {len(messages)}"
    )

    # Step 4: Generate response using the LLM
    try:
        import requests.exceptions
        
        # Try to get a response from LLM with timeout
        try:
            response = client.chat.completions.create(
                model="local-model",
                messages=messages,  # Use the messages list generated above
                temperature=0.7,
                max_tokens=500,
                timeout=10,  # Add timeout
            )
            log_event("[API] ✅ Response successfully generated.")

            # Post-process: Remove generic follow-up if present
            generated_response = response.choices[0].message.content.strip()
            if "What else is on your mind" in generated_response:
                generated_response = generated_response.split("What else is on your mind")[
                    0
                ].strip()

            return generated_response
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            # Handle connection errors gracefully
            log_event(f"[ERROR] ⚠️ LM Studio connection error: {e}", level="warning")
            
            # Return a friendly error message that lets the user know the LLM is unavailable
            return "I'm sorry, I'm having trouble connecting to my language processing service right now. Is LM Studio running on your computer? I need it to generate thoughtful responses. In the meantime, I'm still listening and will try again with your next question."

    except Exception as e:
        log_event(f"[ERROR] ❌ Response generation error: {e}", level="error")
        # Return a friendly error message instead of raising an exception
        return f"I apologize, but I encountered an issue while processing your request. Let's try again with a different question or phrase."
