from __future__ import annotations

import io
import time
from pathlib import Path

import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components

from app.banking.dummy_bank import DummyBankService
from app.config import APP_NAME, AUDIO_DIR, UPLOAD_DIR, VIDEO_DIR
from app.core.intent_router import IntentRouter
from app.models.intent_models import StructuredIntent, TransferDetails
from app.services.cheque_verifier import ChequeVerifier
from app.services.response_builder import ResponseBuilder
from app.utils.file_manager import FileManager


# Configure the Streamlit page.
st.set_page_config(
    page_title="Kentiq AI Voice Banking Assistant",
    layout="wide",
)


@st.cache_resource
def get_backend_services() -> dict[str, object]:
    """Create and cache backend service objects used by the UI."""
    file_manager = FileManager()
    file_manager.ensure_directories()

    return {
        "file_manager": file_manager,
        "router": IntentRouter(),
        "bank_service": DummyBankService(),
        "cheque_verifier": ChequeVerifier(),
        "responses": ResponseBuilder(),
    }


def init_session_state() -> None:
    """Initialize Streamlit session state values used across reruns."""
    st.session_state.setdefault("transcribed_text", "")
    st.session_state.setdefault("assistant_reply", "")
    st.session_state.setdefault("voice_audio_bytes", None)
    st.session_state.setdefault("audio_error", "")
    st.session_state.setdefault("latest_intent_name", "")
    st.session_state.setdefault("last_spoken_text", "")
    st.session_state.setdefault("voice_interaction_started", False)
    st.session_state.setdefault(
        "transfer_form",
        {
            "beneficiary_name": "",
            "bank_name": "",
            "account_number": "",
            "amount": 0.0,
        },
    )


def save_uploaded_file(uploaded_file, target_dir: Path, prefix: str) -> Path:
    """Save an uploaded Streamlit file to disk with a timestamped filename."""
    suffix = Path(uploaded_file.name).suffix or ".bin"
    target_path = target_dir / f"{prefix}_{int(time.time() * 1000)}{suffix}"
    target_path.write_bytes(uploaded_file.getbuffer())
    return target_path


def transcribe_audio(uploaded_audio) -> str:
    """Convert uploaded WAV audio into text with SpeechRecognition."""
    recognizer = sr.Recognizer()

    try:
        audio_stream = io.BytesIO(uploaded_audio.getvalue())
        with sr.AudioFile(audio_stream) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError as error:
        raise ValueError("Could not understand the recorded audio clearly.") from error
    except sr.RequestError as error:
        raise RuntimeError("Speech recognition service is unavailable.") from error
    except Exception as error:
        raise RuntimeError("Unable to read the recorded audio input.") from error


def build_voice_response_audio(text: str, save_to_file: bool = True) -> bytes | None:
    """Generate playable response audio bytes using pyttsx3 when possible."""
    if not text:
        return None

    st.session_state.audio_error = ""

    try:
        import pyttsx3
    except ImportError:
        st.session_state.audio_error = "pyttsx3 is not installed for server-side audio generation."
        return None

    if save_to_file:
        output_path = AUDIO_DIR / f"ui_response_{int(time.time() * 1000)}.wav"
    else:
        # Use a temporary path that won't be saved
        import tempfile
        output_path = Path(tempfile.mktemp(suffix=".wav"))

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()

        if output_path.exists():
            audio_bytes = output_path.read_bytes()
            # Clean up temporary file if not saving
            if not save_to_file:
                output_path.unlink()
            return audio_bytes
    except Exception as error:
        st.session_state.audio_error = f"Server-side audio generation failed: {error}"
        return None

    return None


def speak_text_in_browser(text: str) -> None:
    """Use the browser SpeechSynthesis API to speak assistant replies."""
    if not text:
        return

    safe_text = (
        text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )

    components.html(
        f"""
        <script>
        const utteranceText = `{safe_text}`;
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(utteranceText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
        </script>
        """,
        height=0,
    )


def prefill_transfer_form(details: TransferDetails) -> None:
    """Populate transfer form fields from the LLM extracted transfer details."""
    form = st.session_state.transfer_form

    if details.beneficiary_name:
        form["beneficiary_name"] = details.beneficiary_name
    if details.bank_name:
        form["bank_name"] = details.bank_name
    if details.account_number:
        form["account_number"] = details.account_number
    if details.amount is not None:
        form["amount"] = float(details.amount)


def build_assistant_reply(intent: StructuredIntent, services: dict[str, object]) -> str:
    """Create a natural reply for the UI based on the detected intent."""
    responses = services["responses"]
    bank_service = services["bank_service"]

    if intent.name == "balance":
        return bank_service.get_balance()

    if intent.name == "transfer":
        intro = responses.transfer_intro(intent)
        if any(
            [
                intent.transfer.beneficiary_name,
                intent.transfer.bank_name,
                intent.transfer.account_number,
                intent.transfer.amount is not None,
            ]
        ):
            return (
                f"{intro} I captured some transfer details from your voice input. "
                "Please review the form below and submit the transfer."
            )
        return f"{intro} Please complete the transfer form below."

    if intent.name == "cheque":
        return intent.assistant_reply or "Please use the cheque upload section below to validate your cheque."

    if intent.name == "kyc":
        return intent.assistant_reply or "Please upload your KYC audio and video files in the KYC section below."

    if intent.name == "help":
        return responses.help()

    if intent.name == "exit":
        return "Thank you for using Dubai Bank Bank voice assistant. Goodbye."

    return responses.unknown(intent.clarification_question)


def process_voice_request(uploaded_audio, services: dict[str, object]) -> None:
    """Handle end-to-end voice processing from audio to AI reply."""
    transcribed_text = transcribe_audio(uploaded_audio)
    intent = services["router"].detect(transcribed_text)
    reply_text = build_assistant_reply(intent, services)

    st.session_state.transcribed_text = transcribed_text
    st.session_state.assistant_reply = reply_text
    st.session_state.latest_intent_name = intent.name

    if intent.name == "transfer":
        prefill_transfer_form(intent.transfer)

    st.session_state.voice_audio_bytes = build_voice_response_audio(reply_text, save_to_file=False)


def validate_transfer_form(form_data: dict[str, object]) -> list[str]:
    """Validate transfer input before calling the backend transfer logic."""
    errors: list[str] = []

    beneficiary_name = str(form_data["beneficiary_name"]).strip()
    bank_name = str(form_data["bank_name"]).strip()
    account_number = str(form_data["account_number"]).strip()
    amount = form_data["amount"]

    if len(beneficiary_name) < 2:
        errors.append("Beneficiary name is required.")
    if len(bank_name) < 2:
        errors.append("Bank name is required.")
    if not account_number.isdigit() or not 6 <= len(account_number) <= 18:
        errors.append("Account number must be 6 to 18 digits.")
    if float(amount) <= 0:
        errors.append("Amount must be greater than zero.")

    return errors


def render_transfer_form(services: dict[str, object]) -> None:
    """Render a transfer form that works with LLM extracted slot values."""
    st.subheader("Transfer Details")
    st.caption("This form is auto-filled when the voice intent is a money transfer.")

    form_state = st.session_state.transfer_form

    with st.form("transfer_form"):
        beneficiary_name = st.text_input(
            "Beneficiary Name",
            value=form_state["beneficiary_name"],
        )
        bank_name = st.text_input(
            "Bank Name",
            value=form_state["bank_name"],
        )
        account_number = st.text_input(
            "Account Number",
            value=form_state["account_number"],
        )
        amount = st.number_input(
            "Amount",
            min_value=0.0,
            step=100.0,
            value=float(form_state["amount"]),
        )

        submit_transfer = st.form_submit_button("Submit Transfer")

    if submit_transfer:
        updated_form = {
            "beneficiary_name": beneficiary_name.strip(),
            "bank_name": bank_name.strip(),
            "account_number": account_number.strip(),
            "amount": amount,
        }
        st.session_state.transfer_form["beneficiary_name"] = updated_form["beneficiary_name"]
        st.session_state.transfer_form["bank_name"] = updated_form["bank_name"]
        st.session_state.transfer_form["account_number"] = updated_form["account_number"]
        st.session_state.transfer_form["amount"] = updated_form["amount"]

        errors = validate_transfer_form(updated_form)
        if errors:
            for error in errors:
                st.error(error)
            return

        receipt = services["bank_service"].transfer_money(
            beneficiary_name=updated_form["beneficiary_name"],
            bank_name=updated_form["bank_name"],
            account_number=updated_form["account_number"],
            amount=float(updated_form["amount"]),
        )

        success_message = services["responses"].transfer_success(receipt)
        balance_message = services["bank_service"].get_balance()
        full_message = f"{success_message} {balance_message}"
        st.session_state.assistant_reply = full_message
        st.session_state.voice_audio_bytes = build_voice_response_audio(full_message, save_to_file=False)
        st.success("Your transaction is complete!")
        speak_text_in_browser(full_message)
        st.session_state.last_spoken_text = full_message
        st.success(success_message)


def render_voice_section(services: dict[str, object]) -> None:
    """Render the record-and-submit voice interaction section."""
    st.header("Voice Interaction")

    if not st.session_state.voice_interaction_started:
        st.write("Click the button below to start your voice banking interaction.")
        if st.button("Start Voice Interaction", type="primary", use_container_width=True):
            st.session_state.voice_interaction_started = True
            st.rerun()
        return

    # Voice interaction has started - show welcome and recording interface
    welcome_message = services["responses"].welcome()
    st.success(welcome_message)
    speak_text_in_browser(welcome_message)

    st.write(
        "Record your request, submit it, and receive the assistant response in text and speech."
    )
    st.info("Click below to record from your microphone, then submit the recording.")

    recorded_audio = st.audio_input(
        "Record your voice request",
        sample_rate=16_000,
    )

    if recorded_audio is not None:
        st.audio(recorded_audio.getvalue(), format="audio/wav")

    if st.button("Submit Voice Request", type="primary", use_container_width=True):
        if recorded_audio is None:
            st.error("Please record your voice first.")
            return

        try:
            process_voice_request(recorded_audio, services)
        except Exception as error:
            st.error(f"Unable to process recorded audio: {error}")

    if st.session_state.transcribed_text:
        st.text_area(
            "Transcribed Text",
            value=st.session_state.transcribed_text,
            height=120,
            disabled=True,
        )

    if st.session_state.assistant_reply:
        st.success(st.session_state.assistant_reply)
        if st.session_state.assistant_reply != st.session_state.last_spoken_text:
            speak_text_in_browser(st.session_state.assistant_reply)
            st.session_state.last_spoken_text = st.session_state.assistant_reply

    if st.session_state.voice_audio_bytes:
        st.audio(st.session_state.voice_audio_bytes, format="audio/wav")
    elif st.session_state.assistant_reply:
        st.info("The assistant reply is being spoken through the browser voice engine.")

    if st.session_state.audio_error:
        st.warning(st.session_state.audio_error)

    if st.session_state.latest_intent_name == "transfer":
        render_transfer_form(services)


def render_cheque_section(services: dict[str, object]) -> None:
    """Render the cheque upload and validation section."""
    st.header("Cheque Verification")
    uploaded_image = st.file_uploader(
        "Upload a cheque image",
        type=["jpg", "jpeg", "png"],
        key="cheque_uploader",
    )

    if uploaded_image is not None:
        st.image(uploaded_image, caption="Uploaded cheque image", use_container_width=True)

    if st.button("Validate Cheque", use_container_width=True):
        if uploaded_image is None:
            st.error("Please upload a cheque image first.")
            return

        try:
            saved_path = save_uploaded_file(uploaded_image, UPLOAD_DIR, "cheque")
            result = services["cheque_verifier"].verify(saved_path)

            if result.is_valid:
                st.success(f"Valid cheque image. {result.message}")
                st.success("Your transaction is complete!")
                speak_text_in_browser("Your transaction is complete!")
            else:
                st.error(f"Invalid cheque image. {result.message}")
        except Exception as error:
            st.error(f"Cheque validation failed: {error}")


def render_kyc_section() -> None:
    """Render KYC audio and video upload widgets."""
    st.header("KYC Upload")
    st.write("Upload audio and video files for a simple KYC workflow.")

    audio_file = st.file_uploader(
        "Upload KYC audio",
        type=["wav"],
        key="kyc_audio_uploader",
    )
    video_file = st.file_uploader(
        "Upload KYC video",
        type=["mp4"],
        key="kyc_video_uploader",
    )

    if audio_file is not None:
        st.audio(audio_file.getvalue(), format="audio/wav")

    if video_file is not None:
        st.video(video_file)

    if st.button("Save KYC Files", use_container_width=True):
        if audio_file is None and video_file is None:
            st.error("Please upload at least one KYC file.")
            return

        try:
            saved_files: list[str] = []

            if audio_file is not None:
                audio_path = save_uploaded_file(audio_file, AUDIO_DIR, "kyc_audio")
                saved_files.append(str(audio_path))

            if video_file is not None:
                video_path = save_uploaded_file(video_file, VIDEO_DIR, "kyc_video")
                saved_files.append(str(video_path))

            st.success("KYC files saved successfully.")
            st.success("Your transaction is complete!")
            speak_text_in_browser("Your transaction is complete!")
            st.write("Saved files:")
            for saved_file in saved_files:
                st.write(f"- {saved_file}")
        except Exception as error:
            st.error(f"Failed to save KYC files: {error}")


def main() -> None:
    """Run the Streamlit banking assistant UI."""
    init_session_state()
    services = get_backend_services()

    st.title(APP_NAME)
    st.caption("Simple Streamlit UI for your Voice AI Banking Assistant backend.")

    render_voice_section(services)
    st.divider()
    render_cheque_section(services)
    st.divider()
    render_kyc_section()


if __name__ == "__main__":
    main()
