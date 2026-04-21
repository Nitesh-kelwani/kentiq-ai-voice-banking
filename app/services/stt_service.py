import speech_recognition as sr
import numpy as np
import sounddevice as sd


class SpeechToTextService:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.sample_rate = 16_000
        self.sample_width = 2

    def listen(self) -> str:
        try:
            device_info = sd.query_devices(kind="input")
        except Exception as error:
            raise RuntimeError(
                "Microphone is not available. Check your input audio device."
            ) from error

        if not device_info:
            raise RuntimeError("No input microphone device was detected.")

        print("Listening...")
        try:
            frames = sd.rec(
                int(6 * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
        except Exception as error:
            raise RuntimeError(
                "Microphone recording failed. Check microphone permissions and device settings."
            ) from error

        audio_array = np.asarray(frames).flatten()
        if not np.any(audio_array):
            raise ValueError("I did not hear anything. Please speak a little louder.")

        audio = sr.AudioData(
            audio_array.tobytes(),
            self.sample_rate,
            self.sample_width,
        )

        try:
            text = self.recognizer.recognize_google(audio)
            print(f"User: {text}")
            return text
        except sr.UnknownValueError as error:
            raise ValueError("I could not understand your speech clearly.") from error
        except sr.RequestError as error:
            raise RuntimeError(
                "Speech recognition service is unavailable. Check your internet connection."
            ) from error
