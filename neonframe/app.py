"""NeonFrame main window — cyberpunk GUI wired to the detection pipeline."""

from __future__ import annotations

import os
from datetime import datetime

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from neonframe.detector import BACKEND_NAME
from neonframe.presets import PRESET_ORDER, get_preset
from neonframe.settings import load_settings, save_settings
from neonframe.styles import STYLE
from neonframe.worker import AnalysisWorker


def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    q = QColor(hex_color)
    return q.blue(), q.green(), q.red()


class NeonFrameApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NeonFrame — Character Detection Overlay")
        self.resize(1280, 820)
        self.setMinimumSize(980, 640)

        self.settings = load_settings()
        self.media_path = ""
        self.worker: AnalysisWorker | None = None
        self.last_frame = None
        self.source_mode = self.settings.get("source_mode", "file")

        self._build_ui()
        self._apply_settings_to_ui()
        self._wire_persistence()
        self._log("NeonFrame ready. Load media or use authorized screen capture.")
        self._log("No injection, memory scanning, or anti-cheat interaction.")

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        # Header
        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel("NEONFRAME")
        title.setObjectName("title")
        subtitle = QLabel("CHARACTER DETECTION  ·  LOCAL PREVIEW OVERLAY")
        subtitle.setObjectName("subtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch()

        self.overlay_toggle = QCheckBox("OVERLAY ON/OFF")
        self.detect_toggle = QCheckBox("DETECTION")
        header.addWidget(self.overlay_toggle)
        header.addWidget(self.detect_toggle)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(16)
        outer.addLayout(body, 1)

        # Preview panel
        preview = QFrame()
        preview.setObjectName("glow")
        pv = QVBoxLayout(preview)
        pv.setContentsMargins(14, 14, 14, 14)

        top = QHBoxLayout()
        self.file_label = QLabel("NO SOURCE")
        self.file_label.setObjectName("muted")
        self.status_label = QLabel("● IDLE")
        self.status_label.setObjectName("statusIdle")
        self.backend_label = QLabel("backend: —")
        self.backend_label.setObjectName("muted")
        top.addWidget(self.file_label)
        top.addStretch()
        top.addWidget(self.backend_label)
        top.addWidget(self.status_label)
        pv.addLayout(top)

        self.preview = QLabel(
            "OPEN A SCREENSHOT / RECORDING\nor use AUTHORIZED SCREEN CAPTURE\n\n"
            "ESP-style boxes appear when detection is ON"
        )
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(560, 420)
        self.preview.setStyleSheet(
            "color:#6b5a80;background:#050308;border-radius:10px;"
        )
        pv.addWidget(self.preview, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        pv.addWidget(self.progress)

        controls = QHBoxLayout()
        self.open_btn = QPushButton("＋  Open media")
        self.open_btn.clicked.connect(self.open_media)
        self.screen_btn = QPushButton("🖥  Screen capture")
        self.screen_btn.clicked.connect(self.use_screen)
        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.clicked.connect(self.stop)
        self.export_btn = QPushButton("↓  Export")
        self.export_btn.clicked.connect(self.export_frame)
        self.min_btn = QPushButton("Minimize")
        self.min_btn.clicked.connect(self.showMinimized)
        for btn in (
            self.open_btn,
            self.screen_btn,
            self.start_btn,
            self.stop_btn,
            self.export_btn,
            self.min_btn,
        ):
            controls.addWidget(btn)
        pv.addLayout(controls)
        body.addWidget(preview, 1)

        # Settings panel
        side = QFrame()
        side.setObjectName("panel")
        side.setFixedWidth(300)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(16, 16, 16, 16)
        sl.setSpacing(10)

        heading = QLabel("CONFIGURATION")
        heading.setStyleSheet("font-weight:800;color:#ff2d6a;letter-spacing:2px;")
        sl.addWidget(heading)

        sl.addWidget(self._muted("Detection preset"))
        self.preset = QComboBox()
        self.preset.addItems(list(PRESET_ORDER))
        self.preset.currentTextChanged.connect(self._on_preset)
        sl.addWidget(self.preset)
        self.preset_desc = QLabel("")
        self.preset_desc.setObjectName("muted")
        self.preset_desc.setWordWrap(True)
        sl.addWidget(self.preset_desc)

        sl.addWidget(self._muted("Confidence threshold"))
        self.conf = QSlider(Qt.Horizontal)
        self.conf.setRange(10, 90)
        sl.addWidget(self.conf)
        self.conf_val = QLabel()
        sl.addWidget(self.conf_val)
        self.conf.valueChanged.connect(lambda v: self.conf_val.setText(f"{v}%"))

        sl.addWidget(self._muted("Detection speed"))
        self.speed = QSlider(Qt.Horizontal)
        self.speed.setRange(0, 100)
        sl.addWidget(self.speed)
        self.speed_val = QLabel()
        sl.addWidget(self.speed_val)
        self.speed.valueChanged.connect(self._on_speed)

        sl.addWidget(self._muted("Overlay opacity"))
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(20, 100)
        sl.addWidget(self.opacity)
        self.opacity_val = QLabel()
        sl.addWidget(self.opacity_val)
        self.opacity.valueChanged.connect(lambda v: self.opacity_val.setText(f"{v}%"))

        sl.addWidget(self._muted("Box color"))
        self.box_color_btn = QPushButton("Choose box color")
        self.box_color_btn.clicked.connect(lambda: self._pick_color("box_color"))
        sl.addWidget(self.box_color_btn)

        sl.addWidget(self._muted("Label color"))
        self.label_color_btn = QPushButton("Choose label color")
        self.label_color_btn.clicked.connect(lambda: self._pick_color("label_color"))
        sl.addWidget(self.label_color_btn)

        self.show_labels = QCheckBox("Show confidence labels")
        sl.addWidget(self.show_labels)

        self.hit_label = QLabel("Hits: 0")
        self.hit_label.setStyleSheet("color:#c084fc;font-weight:700;")
        sl.addWidget(self.hit_label)

        sl.addStretch()
        note = QLabel(
            "Analyzes files you choose or your own desktop via mss. "
            "Does not inject into games or access process memory."
        )
        note.setWordWrap(True)
        note.setObjectName("muted")
        sl.addWidget(note)
        body.addWidget(side)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(110)
        outer.addWidget(self.log_view)

    def _muted(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("muted")
        return label

    def _apply_settings_to_ui(self) -> None:
        s = self.settings
        self.overlay_toggle.setChecked(bool(s["overlay_enabled"]))
        self.detect_toggle.setChecked(bool(s["detection_enabled"]))
        self.conf.setValue(int(s["confidence"]))
        self.opacity.setValue(int(s["opacity"]))
        self.speed.setValue(int(s.get("detection_speed", 50)))
        self.show_labels.setChecked(bool(s.get("show_labels", True)))
        preset_name = s.get("preset", "Smart")
        if preset_name in PRESET_ORDER:
            self.preset.setCurrentText(preset_name)
        self._refresh_color_buttons()
        self._on_preset(self.preset.currentText(), apply_values=False)
        self._on_speed(self.speed.value())
        self.conf_val.setText(f"{self.conf.value()}%")
        self.opacity_val.setText(f"{self.opacity.value()}%")
        self._update_toggle_status()

    def _wire_persistence(self) -> None:
        self.overlay_toggle.stateChanged.connect(self._persist)
        self.detect_toggle.stateChanged.connect(self._persist)
        self.conf.valueChanged.connect(self._persist)
        self.opacity.valueChanged.connect(self._persist)
        self.speed.valueChanged.connect(self._persist)
        self.show_labels.stateChanged.connect(self._persist)
        self.preset.currentTextChanged.connect(self._persist)
        self.overlay_toggle.stateChanged.connect(self._update_toggle_status)
        self.detect_toggle.stateChanged.connect(self._update_toggle_status)

    def _update_toggle_status(self) -> None:
        on = self.overlay_toggle.isChecked() and self.detect_toggle.isChecked()
        if on:
            self.status_label.setText("● DETECTION ARMED")
            self.status_label.setStyleSheet("color:#39ff14;font-weight:700;")
        elif self.overlay_toggle.isChecked():
            self.status_label.setText("● OVERLAY ONLY")
            self.status_label.setStyleSheet("color:#c084fc;font-weight:700;")
        else:
            self.status_label.setText("● OFF")
            self.status_label.setStyleSheet("color:#ff2d6a;font-weight:700;")

    def _on_preset(self, name: str, apply_values: bool = True) -> None:
        preset = get_preset(name)
        self.preset_desc.setText(preset.description)
        if apply_values:
            self.conf.setValue(int(preset.confidence * 100))
            # Map sample_step to speed slider (higher speed = skip more)
            # Novice step4 → lower speed value wait - actually "detection speed"
            # higher = faster = more skipping
            speed_map = {4: 80, 2: 50, 1: 20}
            self.speed.setValue(speed_map.get(preset.sample_step, 50))

    def _on_speed(self, value: int) -> None:
        step = self._sample_step_from_speed(value)
        self.speed_val.setText(f"{value}% · sample every {step} frame(s)")

    @staticmethod
    def _sample_step_from_speed(value: int) -> int:
        # 0 = densest (every frame), 100 = sparsest
        if value >= 75:
            return 6
        if value >= 50:
            return 3
        if value >= 25:
            return 2
        return 1

    def _refresh_color_buttons(self) -> None:
        box = self.settings["box_color"]
        lab = self.settings["label_color"]
        self.box_color_btn.setStyleSheet(f"color:{box};border-color:{box};")
        self.label_color_btn.setStyleSheet(f"color:{lab};border-color:{lab};")

    def _pick_color(self, key: str) -> None:
        current = QColor(self.settings[key])
        chosen = QColorDialog.getColor(current, self, "Pick color")
        if chosen.isValid():
            self.settings[key] = chosen.name()
            self._refresh_color_buttons()
            self._persist()

    def _persist(self, *_args) -> None:
        self.settings.update(
            overlay_enabled=self.overlay_toggle.isChecked(),
            detection_enabled=self.detect_toggle.isChecked(),
            opacity=self.opacity.value(),
            confidence=self.conf.value(),
            detection_speed=self.speed.value(),
            show_labels=self.show_labels.isChecked(),
            preset=self.preset.currentText(),
            source_mode=self.source_mode,
        )
        save_settings(self.settings)

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{stamp}] {message}")

    def open_media(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open screenshot or recording",
            "",
            "Media (*.png *.jpg *.jpeg *.bmp *.webp *.mp4 *.avi *.mov *.mkv *.webm)",
        )
        if path:
            self.media_path = path
            self.source_mode = "file"
            self.file_label.setText(os.path.basename(path))
            self._log(f"Loaded file: {path}")
            self._persist()

    def use_screen(self) -> None:
        self.source_mode = "screen"
        self.file_label.setText("PRIMARY MONITOR (authorized capture)")
        self._log("Source set to authorized primary-monitor capture (mss).")
        self._persist()

    def start(self) -> None:
        if self.source_mode == "file" and not self.media_path:
            self.open_media()
            if not self.media_path:
                return

        self.stop()
        detection_on = (
            self.overlay_toggle.isChecked() and self.detect_toggle.isChecked()
        )
        preset = get_preset(self.preset.currentText())
        # Confidence slider overrides preset default when user moves it
        confidence = self.conf.value() / 100.0
        sample_step = self._sample_step_from_speed(self.speed.value())

        self.status_label.setText("● PROCESSING")
        self.status_label.setObjectName("statusIdle")
        self._log(
            f"Start · mode={self.source_mode} · conf={confidence:.2f} · "
            f"imgsz={preset.imgsz} · step={sample_step} · detection={detection_on}"
        )

        self.worker = AnalysisWorker(
            mode=self.source_mode,
            path=self.media_path,
            detection_on=detection_on,
            confidence=confidence,
            imgsz=preset.imgsz,
            sample_step=sample_step,
            color=_hex_to_bgr(self.settings["box_color"]),
            label_color=_hex_to_bgr(self.settings["label_color"]),
            opacity=self.opacity.value() / 100.0,
            show_labels=self.show_labels.isChecked(),
            screen_frames=90,
        )
        self.worker.frame_ready.connect(self._on_frame)
        self.worker.finished_msg.connect(self._on_finished)
        self.worker.log.connect(self._log)
        self.worker.start()

    def stop(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
            self._log("Stop requested")

    def _on_frame(self, frame, current: int, total: int, count: int) -> None:
        self.last_frame = frame
        self.hit_label.setText(f"Hits: {count}")
        self.backend_label.setText(f"backend: {BACKEND_NAME}")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg).scaled(
            self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview.setPixmap(pixmap)
        self.progress.setValue(int(current * 100 / max(1, total)))

    def _on_finished(self, message: str) -> None:
        self.status_label.setText(f"● {message.upper()}")
        self.progress.setValue(100)
        self.backend_label.setText(f"backend: {BACKEND_NAME}")
        self._log(message)
        self._update_toggle_status()

    def export_frame(self) -> None:
        if self.last_frame is None:
            self._log("Nothing to export yet")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export annotated frame", "NeonFrame-export.png", "PNG (*.png)"
        )
        if path:
            cv2.imwrite(path, self.last_frame)
            self._log(f"Exported: {path}")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop()
        self._persist()
        event.accept()


def create_app():
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = NeonFrameApp()
    window.show()
    return app, window
