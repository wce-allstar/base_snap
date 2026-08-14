"""Shared LLM plumbing for agents: a thin Gemini wrapper and JSON parsing.

Agents stay framework-agnostic: they only know the LLMClient interface
(one method: `generate`) plus their input/output JSON contracts.
"""

import json
import os
import time

DEFAULT_MODEL = "gemini-3.5-flash"
MAX_RETRIES = 6


def parse_json_response(text):
    """Strip markdown fences if present and parse JSON. Raises ValueError."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise ValueError(f"Agent returned invalid JSON: {text[:500]}")


class LLMClient:
    """Minimal wrapper around the google-genai client, with 429 retry/backoff."""

    def __init__(self, api_key=None, model=None):
        if not api_key:
            raise ValueError("Gemini API key is required")
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self.model = model or os.environ.get("EVAL_MODEL") or DEFAULT_MODEL

    def _ask(self, contents, config):
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=self.model, contents=contents, config=config
                )
                return response.text or ""
            except Exception as e:
                last_error = e
                message = str(e)
                if "429" not in message and "RESOURCE_EXHAUSTED" not in message:
                    raise
                delay = 10 * (attempt + 1)
                time.sleep(delay)
        raise last_error

    def generate(self, prompt):
        """Single text prompt -> text response."""
        from google.genai import types
        config = types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=300_000),
        )
        return self._ask(prompt, config)

    def generate_with_file(self, prompt, file_path, mime_type):
        """Text prompt + file bytes (PDF or image) -> text response."""
        from google.genai import types

        with open(file_path, 'rb') as f:
            file_data = f.read()

        part = types.Part.from_bytes(data=file_data, mime_type=mime_type)
        config = types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=300_000),
        )
        return self._ask([prompt, part], config)

    def generate_json(self, prompt, schema_hint):
        """Ask for strict JSON and return a dict."""
        return parse_json_response(self.generate(prompt + f"\n\n{schema_hint}"))