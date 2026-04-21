# Kentiq AI Voice Banking Assistant

A beginner-friendly, interview-ready Python project for a voice-enabled banking assistant. The assistant listens through the microphone, converts speech to text, uses Gemini to turn user speech into structured intent data, speaks responses back to the user, and performs dummy banking operations.

## Features

- Voice input using the microphone
- Speech-to-text using `speech_recognition`
- Text-to-speech using `pyttsx3`
- LLM-based intent detection with Gemini structured JSON output
- Fallback keyword intent routing if no Gemini API key is configured
- Dummy balance check
- Smarter money transfer flow with slot extraction and follow-up questions only for missing details
- Cheque image verification using basic OpenCV rules
- Voice KYC recording that saves audio and video locally
- Error handling for unclear speech, invalid input, and missing devices
- Uploaded cheque images are copied into `storage/uploads`

## Folder Structure

```text
Kentiq AI Voice Banking Assistant/
|-- app/
|   |-- banking/
|   |   |-- __init__.py
|   |   `-- dummy_bank.py
|   |-- core/
|   |   |-- __init__.py
|   |   |-- assistant.py
|   |   `-- intent_router.py
|   |-- models/
|   |   |-- __init__.py
|   |   `-- intent_models.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- audio_recorder.py
|   |   |-- cheque_verifier.py
|   |   |-- file_picker.py
|   |   |-- gemini_intent_service.py
|   |   |-- response_builder.py
|   |   |-- stt_service.py
|   |   |-- transfer_flow.py
|   |   |-- tts_service.py
|   |   `-- video_recorder.py
|   |-- utils/
|   |   |-- __init__.py
|   |   `-- file_manager.py
|   |-- __init__.py
|   `-- config.py
|-- storage/
|   |-- audio/
|   |-- uploads/
|   `-- video/
|-- .env
|-- main.py
|-- README.md
`-- requirements.txt
```

## Step-by-Step Flow

### 1. App starts

When you run `main.py`, the assistant loads all services and immediately speaks:

`Welcome to Kentiq AI Voice Bot from Dubai Bank Bank. How can I help you?`

### 2. User speaks

The assistant listens through the microphone and converts the voice input to text using Google speech recognition through the `speech_recognition` library.

### 3. Intent detection happens

The router first tries Gemini structured output. Gemini returns JSON with:

- `intent`
- `confidence`
- `needs_clarification`
- `clarification_question`
- `assistant_reply`
- `transfer_details`

If no Gemini API key is available, the app falls back to keyword routing.

### 4. Assistant performs the action

- For balance, it returns a dummy account balance.
- For transfer, it first reuses any details Gemini already extracted, then asks only for missing fields.
- For cheque, it asks the user to upload/select an image and checks if it looks like a cheque.
- For KYC, it records audio and video and stores them locally.

### 5. Assistant speaks the result

Every result is printed in the terminal and also spoken using text-to-speech.

## How To Run

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Set the Gemini API key

The project now loads environment variables automatically from `.env`.

Edit `.env` in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 4. Run the assistant

```powershell
python main.py
```

## Sample Commands

- "Check my balance"
- "Transfer money"
- "Transfer 500 dirhams to Sara at Emirates NBD account 12345678"
- "Verify cheque"
- "Start KYC"
- "Help"
- "Exit"

## Notes For Interview Explanation

- The project is modular, so each responsibility is separated into a small file.
- `core/assistant.py` controls the conversation flow.
- `core/intent_router.py` decides whether to use Gemini or fallback routing.
- `models/intent_models.py` defines the structured intent object used across the app.
- `banking/dummy_bank.py` isolates business logic from voice logic.
- `services/gemini_intent_service.py` calls Gemini and requests structured JSON output.
- `services/transfer_flow.py` manages slot-filling for transfers.
- `services/response_builder.py` keeps voice responses natural and reusable.
- `services/` contains reusable integrations like STT, TTS, camera, recorder, cheque verification, and LLM integration.
- `storage/` keeps generated files organized.

## Gemini Structured Intent Example

For a sentence like:

`Transfer 500 dirhams to Sara at Emirates NBD account 12345678`

Gemini can return a structure like:

```json
{
  "intent": "transfer",
  "confidence": 0.97,
  "needs_clarification": false,
  "clarification_question": "",
  "assistant_reply": "Sure, I can help with that transfer.",
  "transfer_details": {
    "beneficiary_name": "Sara",
    "bank_name": "Emirates NBD",
    "account_number": "12345678",
    "amount": 500,
    "confirmation": null
  }
}
```

## Optional LangChain Upgrade

If you want to use LangChain later, a good next step is wrapping the Gemini intent extractor as a tool and adding memory for longer conversations.

## Basic Improvements You Can Add Later

- Real authentication
- Database storage
- OCR for cheque fields
- Streamlit or Flask frontend
- Real bank API integration
- Face verification during KYC
- Transaction history support
