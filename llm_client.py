import json
import re
from typing import Dict

import requests

from prompts import SYSTEM_PROMPT


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self) -> None:
        self.api_url = "http://localhost:11434/api/generate"
        self.model = "llama3"

    def generate_replies(self, incoming_message: str) -> Dict[str, str]:
        if not incoming_message.strip():
            raise LLMError("Incoming message is empty.")

        prompt = f"""{SYSTEM_PROMPT}

Incoming message:
{incoming_message.strip()}

Return only JSON in exactly this format:
{{
  "playful": "...",
  "casual": "...",
  "flirty_light": "..."
}}

Do not add any explanation before or after the JSON.
"""

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        data = response.json()
        raw_text = data.get("response", "").strip()

        if not raw_text:
            raise LLMError("Ollama returned an empty response.")

        parsed = self._parse_response(raw_text)

        required_keys = ["playful", "casual", "flirty_light"]
        for key in required_keys:
            if key not in parsed or not isinstance(parsed[key], str):
                raise LLMError(f"Missing or invalid key in response: {key}")

        return parsed

    def _parse_response(self, raw_text: str) -> Dict[str, str]:
        # First try normal JSON parsing
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # Try extracting the JSON-looking part
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = raw_text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Fallback: regex extract fields manually
        extracted = {}
        patterns = {
            "playful": r'"playful"\s*:\s*"(.+?)"',
            "casual": r'"casual"\s*:\s*"(.+?)"',
            "flirty_light": r'"flirty_light"\s*:\s*"(.+?)"',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, raw_text, re.DOTALL)
            if match:
                extracted[key] = match.group(1).strip()

        if len(extracted) == 3:
            return extracted

        raise LLMError(f"Model did not return valid JSON.\n\nRaw response:\n{raw_text}")