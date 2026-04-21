import pyttsx3


class TextToSpeechService:
    def __init__(self) -> None:
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 165)

    def speak(self, text: str) -> None:
        self.engine.say(text)
        self.engine.runAndWait()
