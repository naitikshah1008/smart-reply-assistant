import json
import os
from typing import Dict

import requests
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT

load_dotenv()


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.api_url = os.getenv("LLM_API_URL", "").strip()
        self.model = os.getenv("LLM_MODEL", "").strip()

        if not self.api_key:
            raise LLMError("Missing LLM_API_KEY in .env")
        if not self.api_url:
            raise LLMError("Missing LLM_API_URL in .env")
        if not self.model:
            raise LLMError("Missing LLM_MODEL in .env")

    def generate_replies(self, incoming_message: str) -> Dict[str, str]:
        if not incoming_message.strip():
            raise LLMError("Incoming message is empty.")

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Write three reply options for this Hinge message:\n\n"
                        f"{incoming_message.strip()}"
                    ),
                },
            ],
            "temperature": 0.9,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"API request failed: {exc}") from exc

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise LLMError("Could not parse model response.") from exc

        required_keys = ["playful", "casual", "flirty_light"]
        for key in required_keys:
            if key not in parsed or not isinstance(parsed[key], str):
                raise LLMError(f"Missing or invalid key in response: {key}")

        return parsed