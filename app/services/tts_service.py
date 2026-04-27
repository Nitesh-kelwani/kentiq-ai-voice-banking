import pyttsx3


class TextToSpeechService:
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 165)
        self.engine.setProperty("volume", 0.95)
        self._set_preferred_voice()

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()

    def _set_preferred_voice(self) -> None:
        # Use one preferred Windows voice consistently for a professional tone.
        voices = self.engine.getProperty("voices")
        preferred_keyword = "zira"

        for voice in voices:
            voice_text = f"{voice.id} {voice.name}".lower()
            if preferred_keyword in voice_text:
                self.engine.setProperty("voice", voice.id)
                return

        if voices:
            self.engine.setProperty("voice", voices[0].id)
