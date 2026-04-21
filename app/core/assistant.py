from __future__ import annotations

from pathlib import Path
import re
from typing import Callable, Optional

from app.banking.dummy_bank import DummyBankService
from app.config import DEFAULT_AUDIO_SECONDS, DEFAULT_VIDEO_SECONDS
from app.core.intent_router import IntentRouter
from app.models.intent_models import StructuredIntent, TransferDetails
from app.services.audio_recorder import AudioRecorder
from app.services.cheque_verifier import ChequeVerifier
from app.services.file_picker import FilePickerService
from app.services.response_builder import ResponseBuilder
from app.services.stt_service import SpeechToTextService
from app.services.transfer_flow import TransferFlow
from app.services.tts_service import TextToSpeechService
from app.services.video_recorder import VideoRecorder
from app.utils.file_manager import FileManager


class VoiceBankingAssistant:
    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.file_manager.ensure_directories()

        self.tts = TextToSpeechService()
        self.stt = SpeechToTextService()
        self.router = IntentRouter()
        self.responses = ResponseBuilder()
        self.bank_service = DummyBankService()
        self.file_picker = FilePickerService()
        self.cheque_verifier = ChequeVerifier()
        self.audio_recorder = AudioRecorder(self.file_manager)
        self.video_recorder = VideoRecorder(self.file_manager)

    def run(self) -> None:
        self._say(self.responses.welcome())

        while True:
            user_text = self._capture_input(
                "Please speak your banking request.",
                retries=2,
            )
            if not user_text:
                continue

            intent = self.router.detect(user_text)

            if intent.needs_clarification and intent.name == "unknown":
                self._say(self.responses.unknown(intent.clarification_question))
                continue

            if intent.name == "balance":
                self.handle_balance(intent)
            elif intent.name == "transfer":
                self.handle_transfer(intent)
            elif intent.name == "cheque":
                self.handle_cheque_verification()
            elif intent.name == "kyc":
                self.handle_kyc()
            elif intent.name == "help":
                self.handle_help()
            elif intent.name == "exit":
                self._say("Thank you for using Dubai Bank Bank voice assistant. Goodbye.")
                break
            else:
                self._say(self.responses.unknown(intent.clarification_question))

    def handle_balance(self, intent: StructuredIntent | None = None) -> None:
        if intent and intent.assistant_reply:
            self._say(intent.assistant_reply)
        self._say(self.bank_service.get_balance())

    def handle_transfer(self, intent: StructuredIntent) -> None:
        transfer_flow = TransferFlow(intent.transfer)
        self._say(self.responses.transfer_intro(intent))

        while not transfer_flow.is_complete():
            missing_field = transfer_flow.next_missing_field()
            if missing_field == "beneficiary_name":
                beneficiary_name = self._ask_field(
                    self.responses.ask_for_beneficiary(),
                    validator=lambda value: len(value) >= 2,
                    validation_message="Please tell me a valid beneficiary name.",
                )
                if not beneficiary_name:
                    self._say(self.responses.transfer_failed())
                    return
                transfer_flow.details.beneficiary_name = beneficiary_name

            elif missing_field == "bank_name":
                bank_name = self._ask_field(
                    self.responses.ask_for_bank(transfer_flow.details.beneficiary_name),
                    validator=lambda value: len(value) >= 2,
                    validation_message="Please tell me a valid bank name.",
                )
                if not bank_name:
                    self._say(self.responses.transfer_failed())
                    return
                transfer_flow.details.bank_name = bank_name

            elif missing_field == "account_number":
                account_number = self._ask_field(
                    self.responses.ask_for_account_number(transfer_flow.details.beneficiary_name),
                    validator=lambda value: value.isdigit() and 6 <= len(value) <= 18,
                    validation_message="Account number should be 6 to 18 digits.",
                    normalizer=self._only_digits,
                )
                if not account_number:
                    self._say(self.responses.transfer_failed())
                    return
                transfer_flow.details.account_number = account_number

            elif missing_field == "amount":
                amount_text = self._ask_field(
                    self.responses.ask_for_amount(transfer_flow.details.beneficiary_name),
                    validator=self._is_valid_amount,
                    validation_message="Please tell me a valid amount such as 250 or 250.50.",
                )
                if not amount_text:
                    self._say(self.responses.transfer_failed())
                    return
                transfer_flow.details.amount = float(self._extract_amount(amount_text))

        confirmation = self._ask_confirmation(transfer_flow.details)
        if not confirmation:
            self._say(self.responses.transfer_cancelled())
            return

        receipt = self.bank_service.transfer_money(
            beneficiary_name=transfer_flow.details.beneficiary_name or "",
            bank_name=transfer_flow.details.bank_name or "",
            account_number=transfer_flow.details.account_number or "",
            amount=transfer_flow.details.amount or 0.0,
        )

        self._say(self.responses.transfer_success(receipt))

    def handle_cheque_verification(self) -> None:
        self._say(self.responses.cheque_prompt())
        image_path = self.file_picker.pick_image_file()

        if not image_path:
            self._say("Cheque verification cancelled because no image was selected.")
            return

        stored_image_path = self.file_manager.copy_upload(Path(image_path))
        result = self.cheque_verifier.verify(stored_image_path)

        if result.is_valid:
            self._say(
                "The uploaded image looks like a cheque. "
                f"Reason: {result.message}"
            )
        else:
            self._say(
                "The uploaded image does not look like a cheque. "
                f"Reason: {result.message}"
            )

    def handle_kyc(self) -> None:
        self._say(self.responses.kyc_intro())

        try:
            audio_path = self.audio_recorder.record(seconds=DEFAULT_AUDIO_SECONDS)
            self._say(f"Audio recording saved ")
        except Exception as error:
            self._say(f"Audio recording failed. Details: {error}")
            return

        try:
            video_path = self.video_recorder.record(seconds=DEFAULT_VIDEO_SECONDS)
        except Exception as error:
            self._say(f"Video recording failed. Details: {error}")
            return

        if video_path:
            self._say(f"Video recording saved.")
            self._say("KYC recording completed successfully.")
        else:
            self._say(
                "Audio recording is saved, but video recording could not be completed."
            )

    def handle_help(self) -> None:
        self._say(self.responses.help())

    def _ask_field(
        self,
        prompt: str,
        validator: Callable[[str], bool],
        validation_message: str,
        normalizer: Optional[Callable[[str], str]] = None,
    ) -> Optional[str]:
        for _ in range(3):
            response = self._capture_input(prompt, retries=2)
            if not response:
                continue

            cleaned_response = normalizer(response) if normalizer else response.strip()
            if validator(cleaned_response):
                return cleaned_response

            self._say(validation_message)

        self._say("I could not collect that information. Returning to the main menu.")
        return None

    def _capture_input(self, prompt: str, retries: int = 2) -> str:
        self._say(prompt)

        for attempt in range(retries + 1):
            try:
                return self.stt.listen()
            except ValueError as error:
                self._say(str(error))
            except RuntimeError as error:
                print(f"[Microphone Fallback] {error}")
                typed_text = input("Type your request instead: ").strip()
                return typed_text

            if attempt < retries:
                self._say("Please try again.")

        self._say("I am still having trouble understanding you.")
        return ""

    def _say(self, message: str) -> None:
        print(f"Assistant: {message}")
        self.tts.speak(message)

    def _ask_confirmation(self, details: TransferDetails) -> bool:
        confirmation = self._ask_field(
            self.responses.transfer_confirmation(details),
            validator=lambda value: value.lower() in {"yes", "no"},
            validation_message="Please say yes or no.",
            normalizer=lambda value: value.lower().strip(),
        )
        return confirmation == "yes"

    @staticmethod
    def _only_digits(value: str) -> str:
        return re.sub(r"\D", "", value)

    @staticmethod
    def _extract_amount(value: str) -> str:
        match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
        return match.group() if match else "0"

    def _is_valid_amount(self, value: str) -> bool:
        amount_text = self._extract_amount(value)
        try:
            return float(amount_text) > 0
        except ValueError:
            return False
