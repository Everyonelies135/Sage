import hashlib
from typing import Optional, Dict
from utils.tools import client
from utils.logger import log_event

class PromptEngine:
    """
    Handles dynamic prompt template generation for Sage using a local LLM.
    Caches generated prompts for reuse based on user input/context signature.
    """
    MAX_PROMPT_LENGTH = 300

    def __init__(self) -> None:
        self.prompt_cache: Dict[str, str] = {}
        self._log_debug("Initialized prompt cache.")

    def _log_debug(self, message: str) -> None:
        log_event(f"[PromptEngine] {message}", level="debug")

    def _log_info(self, message: str) -> None:
        log_event(f"[PromptEngine] {message}", level="info")

    def _get_cache_key(self, user_input: str, context_summary: Optional[str] = None) -> str:
        base = (user_input or "") + "||" + (context_summary or "")
        cache_key = hashlib.sha256(base.encode("utf-8")).hexdigest()
        self._log_debug(f"Generated cache key: {cache_key}")
        return cache_key

    def _build_llm_messages(self, user_input: str, context_summary: Optional[str], mood: Optional[str], personality: Optional[str]):
        prompt = (
            "You are a professional prompt engineer for an AI personal assistant named Sage. "
            "Your task is to write a high-quality system prompt that will allow sage to be an expert on the current topic."
            "The output must be a single, clearly written prompt. "
            "Specify tone, role, or goals in the prompt itself. "
            "Do not include explanations, comments, or formatting—just output the raw prompt."
        )
        llm_instruction = (
            f"Generate a system prompt based on the following details. "
            f"User input: '{{user_input}}'. "
            f"Target mood: '{{mood}}'. "
            f"Assistant personality: '{{personality}}'. "
            f"reply with only a system prompt."
        )
        # Fill in the instruction with actual values for the LLM
        llm_instruction = llm_instruction.format(
            user_input=user_input or "",
            mood=mood or "",
            personality=personality or ""
        )
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": llm_instruction},
        ]

    def get_or_generate_prompt(
        self,
        user_input: str,
        context_summary: Optional[str] = None,
        mood: Optional[str] = None,
        personality: Optional[str] = None,
    ) -> str:
        self = self if isinstance(self, PromptEngine) else PromptEngine()
        cache_key = self._get_cache_key(user_input, context_summary)
        if cache_key in self.prompt_cache:
            self._log_debug(f"Cache hit for key: {cache_key}")
            self._log_info(f"Cached prompt template: {self.prompt_cache[cache_key]}")
            return self.prompt_cache[cache_key]
        self._log_debug(f"Cache miss. Generating new prompt for key: {cache_key}")
        messages = self._build_llm_messages(user_input, context_summary, mood, personality)
        self._log_info(f"LLM instruction: {messages}")
        response = client.chat.completions.create(
            model="local-model",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        prompt_template = response.choices[0].message.content.strip()
        self._log_info(f"Generated new prompt template: {prompt_template}")
        self.prompt_cache[cache_key] = prompt_template
        return prompt_template

    def format_prompt(
        self,
        user_input: str,
        context_summary: Optional[str] = None,
        mood: Optional[str] = None,
        personality: Optional[str] = None,
    ) -> str:
        self._log_debug(f"Formatting prompt for user input: {user_input[:40]}...")
        template = self.get_or_generate_prompt(user_input, context_summary, mood, personality)
        self._log_info(f"Using prompt template: {template}")
        # Use str.format for placeholder replacement
        filled = template.format(
            user_input=user_input or "",
            context=context_summary or "",
            mood=mood or "",
            personality=personality or ""
        )
        if len(filled) > self.MAX_PROMPT_LENGTH:
            filled = filled[:self.MAX_PROMPT_LENGTH].rstrip() + "..."
        self._log_info(f"Final formatted prompt: {filled}")
        self._log_debug(f"Final formatted prompt length: {len(filled)}")
        return filled
