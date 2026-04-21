from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ChequeVerificationResult:
    is_valid: bool
    message: str


class ChequeVerifier:
    def verify(self, image_path: Path) -> ChequeVerificationResult:
        image = cv2.imread(str(image_path))
        if image is None:
            return ChequeVerificationResult(
                is_valid=False,
                message="Unable to read the selected image file.",
            )

        image_height, image_width = image.shape[:2]
        image_area = float(image_height * image_width)
        image_aspect_ratio = image_width / float(image_height or 1)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        _, threshold = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )
        closed = cv2.morphologyEx(
            threshold,
            cv2.MORPH_CLOSE,
            np.ones((7, 7), np.uint8),
            iterations=2,
        )
        edges = cv2.Canny(closed, 50, 150)

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        best_candidate = None
        best_score = -1.0

        for contour in contours:
            contour_area = cv2.contourArea(contour)
            if contour_area <= 0:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            bounding_area = float(width * height)
            if bounding_area <= 0:
                continue

            aspect_ratio = width / float(height or 1)
            area_ratio = contour_area / image_area
            fill_ratio = contour_area / bounding_area

            score = 0.0
            if 1.5 <= aspect_ratio <= 4.2:
                score += 2.0
            if 0.05 <= area_ratio <= 0.95:
                score += 2.0
            if fill_ratio >= 0.45:
                score += 1.0

            if score > best_score:
                best_score = score
                best_candidate = {
                    "aspect_ratio": aspect_ratio,
                    "area_ratio": area_ratio,
                    "fill_ratio": fill_ratio,
                }

        if best_candidate and best_score >= 4.0:
            return ChequeVerificationResult(
                is_valid=True,
                message=(
                    "The image contains a large document-like region with a typical cheque shape."
                ),
            )

        if 1.6 <= image_aspect_ratio <= 4.2 and image_area >= 60_000:
            return ChequeVerificationResult(
                is_valid=True,
                message=(
                    "The full image itself has a typical cheque-like shape, so it was accepted."
                ),
            )

        if best_candidate:
            return ChequeVerificationResult(
                is_valid=False,
                message=(
                    "A document region was found, but its size or shape does not look enough like a cheque."
                ),
            )

        return ChequeVerificationResult(
            is_valid=False,
            message="No document-like cheque region could be detected in the image.",
        )
