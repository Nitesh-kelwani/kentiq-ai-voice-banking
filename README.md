# Kentiq AI Voice Banking Assistant

A beginner-friendly, interview-ready Python project for a voice-enabled banking assistant. The assistant listens through the microphone, converts speech to text, uses Gemini to turn user speech into structured intent data, speaks responses back to the user, and performs dummy banking operations.

## Features

- **Voice input** using the microphone
- **Speech-to-text** using `speech_recognition`
- **Text-to-speech** using `pyttsx3`
- **LLM-based intent detection** with Gemini structured JSON output
- **Fallback keyword intent routing** if no Gemini API key is configured
- **Dummy balance check** (starts at AED 50,000.00)
- **Smart money transfer flow** with slot extraction and follow-up questions only for missing details
- **Balance deduction** after successful transfers
- **Cheque image verification** using basic OpenCV rules
- **Voice KYC recording** that saves audio and video locally
- **Web interface** using Streamlit for easy interaction
- **Conversation flow** with "Do you want anything else?" prompts
- **Immediate audio feedback** for all transactions
- **Error handling** for unclear speech, invalid input, and missing devices
- **File organization** with uploaded cheque images copied into `storage/uploads`

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
|   |   `-- uploads/
|   |-- uploads/
|   `-- video/
|-- .env
|-- main.py
|-- streamlit_app.py
|-- README.md
`-- requirements.txt
```

## Step-by-Step Flow

### 1. App starts

When you run `main.py`, the assistant loads all services and immediately speaks:

`Welcome to Kentiq AI Voice Bot from Dubai Bank. How can I help you?`

For the web interface (`streamlit_app.py`), click "Start Voice Interaction" to begin.

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

- For balance, it returns the current account balance (AED 50,000.00 initially).
- For transfer, it first reuses any details Gemini already extracted, then asks only for missing fields. After successful transfer, the amount is deducted from the balance.
- For cheque, it asks the user to upload/select an image and checks if it looks like a cheque.
- For KYC, it records audio and video and stores them locally.

### 5. Transaction completion

After each successful transaction, the assistant speaks "Your transaction is complete!" and asks "Do you want anything else?"

### 6. Assistant speaks the result

Every result is printed in the terminal/web interface and also spoken using text-to-speech.

## How To Run

### Option 1: Command-Line Interface

#### 1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
```

#### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

#### 3. Set the Gemini API key

The project now loads environment variables automatically from `.env`.

Edit `.env` in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

#### 4. Run the assistant

```powershell
python main.py
```

### Option 2: Web Interface (Streamlit)

#### 1. Follow steps 1-3 above for virtual environment and API key

#### 2. Run the web app

```powershell
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

The web interface provides:
- Voice interaction with immediate audio feedback
- Transfer form with auto-filled fields from voice input
- Cheque verification upload
- KYC file upload
- Visual feedback for all transactions

## Sample Conversation Flow

```
Bot: Welcome to Kentiq AI Voice Bot from Dubai Bank. How can I help you?
User: check balance
Bot: Hello Naman Roy, your available balance is AED 50,000.00.
Bot: Do you want anything else?
User: transfer 500 to John
Bot: Of course. I can help you with a money transfer.
[Transfer flow collects missing details...]
Bot: Your transfer is complete. AED 500.00 has been sent to John. Your reference number is TXN123456.
Bot: Hello Naman Roy, your available balance is AED 49,500.00.
Bot: Do you want anything else?
User: no
Bot: Thank you, goodbye.
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

- **Modular Architecture**: Each responsibility is separated into focused files
- **Core Logic**: `core/assistant.py` controls conversation flow with "Do you want anything else?" prompts
- **Intent Processing**: `core/intent_router.py` decides between Gemini LLM or fallback keyword routing
- **Data Models**: `models/intent_models.py` defines structured intent objects used across the app
- **Business Logic**: `banking/dummy_bank.py` isolates banking operations with balance deduction after transfers
- **LLM Integration**: `services/gemini_intent_service.py` calls Gemini with structured JSON output requests
- **Transfer Flow**: `services/transfer_flow.py` manages intelligent slot-filling for transfers
- **Response Management**: `services/response_builder.py` keeps voice responses natural and reusable
- **Web Interface**: `streamlit_app.py` provides user-friendly web UI with immediate audio feedback
- **Service Layer**: `services/` contains reusable integrations (STT, TTS, camera, recorder, cheque verification, LLM)
- **File Management**: `storage/` keeps generated files organized with proper cleanup
- **Conversation UX**: Natural flow with transaction completion confirmations and follow-up prompts

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
