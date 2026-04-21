from pathlib import Path
import time

import cv2

from app.utils.file_manager import FileManager


class VideoRecorder:
    def __init__(self, file_manager: FileManager) -> None:
        self.file_manager = file_manager

    def record(self, seconds: int = 8) -> Path | None:
        output_path = self.file_manager.next_video_file()
        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            print("Webcam is not available.")
            return None

        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"XVID"),
            20.0,
            (width, height),
        )

        print(f"Recording video for {seconds} seconds. Press Q to stop early.")
        start_time = time.time()

        while time.time() - start_time < seconds:
            success, frame = camera.read()
            if not success:
                break

            writer.write(frame)
            cv2.imshow("KYC Recording", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        camera.release()
        writer.release()
        cv2.destroyAllWindows()
        return output_path
