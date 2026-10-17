"""Authorized media sources: image/video files and optional desktop capture.

Screen capture uses the `mss` library to grab the user's own primary monitor.
This is ordinary desktop screenshot capture — not game injection, not memory
access, and not anti-cheat bypass.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    import numpy as np

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def is_video(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in VIDEO_EXTS


def load_image(path: str):
    import cv2

    return cv2.imread(path)


def iter_video_frames(path: str, sample_step: int = 1) -> Iterator[tuple]:
    """Yield (frame, index, total) from a video file."""
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return
    total = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    index = 0
    step = max(1, int(sample_step))
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            index += 1
            if index % step:
                continue
            yield frame, index, total
    finally:
        cap.release()


def grab_primary_monitor():
    """Capture the primary monitor as a BGR numpy array via mss."""
    import cv2
    import numpy as np

    try:
        import mss
    except ImportError as exc:
        raise RuntimeError(
            "Screen capture requires the 'mss' package. Install requirements.txt."
        ) from exc

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        frame = np.array(shot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
