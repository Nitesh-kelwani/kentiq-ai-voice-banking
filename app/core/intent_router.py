from app.models.intent_models import StructuredIntent
from app.services.gemini_intent_service import GeminiIntentService


class IntentRouter:
    def __init__(self) -> None:
        self.llm_service = GeminiIntentService()

    def detect(self, user_text: str) -> StructuredIntent:
        if self.llm_service.available:
            try:
                return self.llm_service.detect_intent(user_text)
            except Exception as error:
                print(f"[Intent Fallback] Gemini intent detection failed: {error}")

        return self._fallback_detect(user_text)

    @staticmethod
    def _fallback_detect(user_text: str) -> StructuredIntent:
        text = user_text.lower().strip()

        if any(keyword in text for keyword in ("balance", "account balance", "check balance")):
            return StructuredIntent(
                name="balance",
                original_text=user_text,
                confidence=0.45,
                assistant_reply="Sure, I can help with your account balance.",
            )

        if any(keyword in text for keyword in ("transfer", "send money", "bank transfer")):
            return StructuredIntent(
                name="transfer",
                original_text=user_text,
                confidence=0.45,
                assistant_reply="Sure, I can help you send money.",
            )

        if any(keyword in text for keyword in ("cheque", "check cheque", "verify cheque")):
            return StructuredIntent(
                name="cheque",
                original_text=user_text,
                confidence=0.45,
                assistant_reply="Sure, I can verify your cheque image.",
            )

        if "kyc" in text or "know your customer" in text:
            return StructuredIntent(
                name="kyc",
                original_text=user_text,
                confidence=0.45,
                assistant_reply="Sure, I can start the KYC recording process.",
            )

        if any(keyword in text for keyword in ("help", "options", "what can you do")):
            return StructuredIntent(
                name="help",
                original_text=user_text,
                confidence=0.45,
            )

        if any(keyword in text for keyword in ("exit", "quit", "bye", "stop")):
            return StructuredIntent(
                name="exit",
                original_text=user_text,
                confidence=0.45,
            )

        return StructuredIntent(
            name="unknown",
            original_text=user_text,
            confidence=0.2,
            needs_clarification=True,
            clarification_question=(
                "I didn't fully catch that. Would you like to check your balance, "
                "transfer money, verify a cheque, or start KYC?"
            ),
        )
