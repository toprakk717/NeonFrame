"""Background processing thread for media and screen capture."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from neonframe.capture import grab_primary_monitor, is_image, iter_video_frames, load_image
from neonframe.detector import detect_people, draw_detections


class AnalysisWorker(QThread):
    frame_ready = Signal(object, int, int, int)  # image, current, total, count
    finished_msg = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        *,
        mode: str,
        path: str = "",
        detection_on: bool = True,
        confidence: float = 0.5,
        imgsz: int = 640,
        sample_step: int = 2,
        color: tuple[int, int, int] = (106, 45, 255),
        label_color: tuple[int, int, int] = (252, 132, 192),
        opacity: float = 0.85,
        show_labels: bool = True,
        screen_frames: int = 60,
        parent=None,
    ):
        super().__init__(parent)
        self.mode = mode
        self.path = path
        self.detection_on = detection_on
        self.confidence = confidence
        self.imgsz = imgsz
        self.sample_step = sample_step
        self.color = color
        self.label_color = label_color
        self.opacity = opacity
        self.show_labels = show_labels
        self.screen_frames = screen_frames
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            if self.mode == "screen":
                self._run_screen()
            elif self.mode == "file" and self.path:
                if is_image(self.path):
                    self._run_image()
                else:
                    self._run_video()
            else:
                self.finished_msg.emit("No media source selected")
        except Exception as exc:  # noqa: BLE001 — surface to UI log
            self.log.emit(f"ERROR: {exc}")
            self.finished_msg.emit(f"Failed · {exc}")

    def _annotate(self, image):
        if not self.detection_on:
            return image, 0
        boxes = detect_people(image, self.confidence, self.imgsz)
        annotated = draw_detections(
            image,
            boxes,
            color=self.color,
            opacity=self.opacity,
            show_labels=self.show_labels,
            label_color=self.label_color,
            style="esp",
        )
        return annotated, len(boxes)

    def _run_image(self) -> None:
        self.log.emit(f"Loading image: {self.path}")
        image = load_image(self.path)
        if image is None:
            self.finished_msg.emit("Could not open image")
            return
        annotated, count = self._annotate(image)
        self.frame_ready.emit(annotated, 1, 1, count)
        self.finished_msg.emit(f"Complete · {count} detection(s)")

    def _run_video(self) -> None:
        self.log.emit(f"Loading video: {self.path}")
        sampled = 0
        last_count = 0
        for frame, index, total in iter_video_frames(self.path, self.sample_step):
            if self._stop:
                break
            annotated, last_count = self._annotate(frame)
            sampled += 1
            self.frame_ready.emit(annotated, index, total, last_count)
        if self._stop:
            self.finished_msg.emit("Stopped")
        else:
            self.finished_msg.emit(f"Complete · {sampled} frame(s) · last {last_count} hit(s)")

    def _run_screen(self) -> None:
        self.log.emit("Authorized desktop capture started (primary monitor)")
        total = max(1, int(self.screen_frames))
        last_count = 0
        for i in range(1, total + 1):
            if self._stop:
                break
            frame = grab_primary_monitor()
            if frame is None:
                self.finished_msg.emit("Screen capture failed")
                return
            if self.sample_step > 1 and i % self.sample_step:
                continue
            annotated, last_count = self._annotate(frame)
            self.frame_ready.emit(annotated, i, total, last_count)
            self.msleep(40)
        if self._stop:
            self.finished_msg.emit("Stopped")
        else:
            self.finished_msg.emit(f"Screen session complete · last {last_count} hit(s)")
