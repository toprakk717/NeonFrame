"""Cyberpunk dark theme (neon red / purple / black)."""

STYLE = """
QWidget {
    background: #07060c;
    color: #efe9ff;
    font-family: 'Segoe UI', 'Trebuchet MS', sans-serif;
    font-size: 13px;
}
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #05040a, stop:0.5 #0c0714, stop:1 #090612);
}
QFrame#panel {
    background: rgba(18, 10, 28, 220);
    border: 1px solid #3a1a4f;
    border-radius: 14px;
}
QFrame#glow {
    background: #12091c;
    border: 1px solid #ff2d6a;
    border-radius: 14px;
}
QLabel#title {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 3px;
    color: #ff4d7d;
}
QLabel#subtitle {
    color: #9b7bb8;
    letter-spacing: 1px;
}
QLabel#muted { color: #7a6a8c; }
QLabel#statusOn { color: #39ff14; font-weight: 700; }
QLabel#statusOff { color: #ff2d6a; font-weight: 700; }
QLabel#statusIdle { color: #c084fc; font-weight: 700; }
QPushButton {
    background: #1a1026;
    border: 1px solid #4a2a62;
    border-radius: 10px;
    padding: 10px 14px;
    color: #efe9ff;
}
QPushButton:hover {
    border-color: #ff2d6a;
    color: #ff8fb0;
    background: #241433;
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff2d6a, stop:1 #a855f7);
    color: #14030a;
    font-weight: 800;
    border: 0;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff4d7d, stop:1 #c084fc);
}
QPushButton#danger {
    border-color: #ff2d6a;
    color: #ff8fb0;
}
QCheckBox { spacing: 10px; }
QCheckBox::indicator {
    width: 42px;
    height: 22px;
    border-radius: 11px;
    background: #2a2038;
    border: 1px solid #4a2a62;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff2d6a, stop:1 #a855f7);
    border: 0;
}
QSlider::groove:horizontal {
    height: 5px;
    background: #2a2038;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ff2d6a;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #a855f7;
    border-radius: 3px;
}
QProgressBar {
    border: 0;
    background: #1a1026;
    height: 8px;
    border-radius: 4px;
    text-align: center;
    color: #c084fc;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff2d6a, stop:1 #a855f7);
    border-radius: 4px;
}
QComboBox {
    padding: 8px 10px;
    background: #1a1026;
    border: 1px solid #4a2a62;
    border-radius: 8px;
}
QComboBox QAbstractItemView {
    background: #12091c;
    border: 1px solid #4a2a62;
    selection-background-color: #4a2a62;
}
QPlainTextEdit#log {
    background: #0a0710;
    border: 1px solid #2e1a40;
    border-radius: 8px;
    color: #b39dd0;
    font-family: Consolas, 'Courier New', monospace;
    font-size: 11px;
}
"""
