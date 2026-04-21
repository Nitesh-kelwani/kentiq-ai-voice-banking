from datetime import datetime
from pathlib import Path
import shutil

from app.config import AUDIO_DIR, UPLOAD_DIR, VIDEO_DIR


class FileManager:
    def ensure_directories(self) -> None:
        for directory in (AUDIO_DIR, VIDEO_DIR, UPLOAD_DIR):
            directory.mkdir(parents=True, exist_ok=True)

    def next_audio_file(self) -> Path:
        return AUDIO_DIR / f"kyc_audio_{self._timestamp()}.wav"

    def next_video_file(self) -> Path:
        return VIDEO_DIR / f"kyc_video_{self._timestamp()}.avi"

    def copy_upload(self, source_file: Path) -> Path:
        target_file = UPLOAD_DIR / f"{self._timestamp()}_{source_file.name}"
        shutil.copy2(source_file, target_file)
        return target_file

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
