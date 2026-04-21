from pathlib import Path
import wave

import numpy as np
import sounddevice as sd

from app.config import DEFAULT_SAMPLE_RATE
from app.utils.file_manager import FileManager


class AudioRecorder:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager

    def record(self, seconds: int = 5) -> Path:
        output_path = self.file_manager.next_audio_file()
        print(f"Recording audio for {seconds} seconds...")

        frames = sd.rec(
            int(seconds * DEFAULT_SAMPLE_RATE),
            samplerate=DEFAULT_SAMPLE_RATE,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        audio_array = np.asarray(frames).flatten()
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(DEFAULT_SAMPLE_RATE)
            wav_file.writeframes(audio_array.tobytes())

        return output_path
