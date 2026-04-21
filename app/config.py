import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = "Kentiq AI Voice Banking Assistant"
WELCOME_MESSAGE = (
    "Welcome to Kentiq AI Voice Bot from Dubai Bank. How can I help you?"
)
UNKNOWN_COMMAND_MESSAGE = (
    "I can help with balance, transfer, cheque verification, and KYC. "
    "Please try again."
)

STORAGE_DIR = BASE_DIR / "storage"
AUDIO_DIR = STORAGE_DIR / "audio"
VIDEO_DIR = STORAGE_DIR / "video"
UPLOAD_DIR = STORAGE_DIR / "uploads"

DEFAULT_AUDIO_SECONDS = 5
DEFAULT_VIDEO_SECONDS = 8
DEFAULT_SAMPLE_RATE = 44_100

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
