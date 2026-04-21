from __future__ import annotations

import json
from typing import Any

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models.intent_models import StructuredIntent


class GeminiIntentService:
    def __init__(self) -> None:
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.client = None
        self.available = False
        self.unavailable_reason = ""

        if not self.api_key:
            self.unavailable_reason = "GEMINI_API_KEY is not set."
            return

        try:
            from google import genai

            self.client = genai.Client(api_key=self.api_key)
            self.available = True
        except ImportError:
            self.unavailable_reason = "google-genai is not installed."
        except Exception as error:
            self.unavailable_reason = str(error)

    def detect_intent(self, user_text: str) -> StructuredIntent:
        if not self.available or self.client is None:
            raise RuntimeError(self.unavailable_reason or "Gemini client is not available.")

        prompt = self._build_prompt(user_text)
        last_error: Exception | None = None

        for model_name in self._candidate_models():
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": 0.1,
                        "response_mime_type": "application/json",
                        "response_json_schema": self._response_schema(),
                    },
                )
                payload = self._parse_response_text(response.text)
                return StructuredIntent.from_dict(payload, original_text=user_text)
            except Exception as error:
                last_error = error
                if not self._is_retryable_model_error(error):
                    raise RuntimeError(f"Gemini intent detection failed: {error}") from error

        raise RuntimeError(
            f"Gemini intent detection failed for all candidate models. Last error: {last_error}"
        ) from last_error

    def _candidate_models(self) -> list[str]:
        models = [
            self.model,
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
        ]
        unique_models: list[str] = []
        for model_name in models:
            if model_name and model_name not in unique_models:
                unique_models.append(model_name)
        return unique_models

    @staticmethod
    def _is_retryable_model_error(error: Exception) -> bool:
        error_text = str(error).lower()
        return (
            "503" in error_text
            or "unavailable" in error_text
            or "high demand" in error_text
            or "overloaded" in error_text
        )

    @staticmethod
    def _build_prompt(user_text: str) -> str:
        return f"""
You are an intent extraction system for a voice banking assistant.

Classify the user's request into exactly one of these intents:
- balance
- transfer
- cheque
- kyc
- help
- exit
- unknown

Extract transfer fields only if they are clearly mentioned.
If the request is incomplete or vague, set needs_clarification to true and ask one short follow-up question.
Make assistant_reply natural, short, and suitable for a voice bot.
Do not invent values that the user did not say.

User speech:
{user_text}
""".strip()

    @staticmethod
    def _response_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["balance", "transfer", "cheque", "kyc", "help", "exit", "unknown"],
                },
                "confidence": {"type": "number"},
                "needs_clarification": {"type": "boolean"},
                "clarification_question": {"type": ["string", "null"]},
                "assistant_reply": {"type": ["string", "null"]},
                "transfer_details": {
                    "type": "object",
                    "properties": {
                        "beneficiary_name": {"type": ["string", "null"]},
                        "bank_name": {"type": ["string", "null"]},
                        "account_number": {"type": ["string", "null"]},
                        "amount": {"type": ["number", "null"]},
                        "confirmation": {"type": ["boolean", "null"]},
                    },
                    "required": [
                        "beneficiary_name",
                        "bank_name",
                        "account_number",
                        "amount",
                        "confirmation",
                    ],
                    "additionalProperties": False,
                },
            },
            "required": [
                "intent",
                "confidence",
                "needs_clarification",
                "clarification_question",
                "assistant_reply",
                "transfer_details",
            ],
            "additionalProperties": False,
        }

    @staticmethod
    def _parse_response_text(response_text: str) -> dict[str, Any]:
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as error:
            raise RuntimeError("Gemini returned invalid JSON for intent detection.") from error
