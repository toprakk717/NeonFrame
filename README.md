# NeonFrame

Windows desktop tool that detects visible people/characters in **your** screenshots, video recordings, or an **authorized** primary-monitor capture, then draws ESP-style 2D bounding boxes in a cyberpunk preview UI.

It does **not** inject into games, read game memory, bypass anti-cheat, or hide from security software.

## Features

- Dark cyberpunk GUI (neon red / purple / black)
- Master **OVERLAY ON/OFF** and **DETECTION** toggles
- **Novice / Smart / Master** presets (confidence, input size, sampling density)
- Adjustable confidence, detection speed, opacity, box/label colors
- Preview window with live hit count and activity log
- Sources: image/video files, or desktop capture via `mss`
- Settings saved under `%APPDATA%\NeonFrame\settings.json`
- Detector: **YOLOv8n** (COCO `person`) when available; OpenCV **HOG** fallback

## Download the Windows EXE (cloud build)

This environment cannot compile a Windows `.exe` on an Android tablet. The free cloud path is **GitHub Actions** (`windows-latest`).

### From an Android tablet (no PC)

1. Create a free GitHub account and an empty public or private repository named e.g. `NeonFrame`.
2. On GitHub → **Add file** → **Upload files**, upload everything in this folder (keep `.github/workflows/build.yml`).
3. Open **Actions** → enable workflows if prompted → run **Build Windows x64** (also runs on push to `main`).
4. When the run is **green**, open it → **Artifacts** → download **NeonFrame-Windows-x64**.
5. Unzip on a Windows x64 PC and launch `NeonFrame.exe`.

No Python install is required to run the packaged EXE. Windows SmartScreen may warn because the binary is unsigned.

> Do not invent download URLs. Only a successful Actions run produces a real artifact link. Until Actions finishes green, there is no finished EXE.

## Run from source (developer PC)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

First YOLO run downloads `yolov8n.pt` (needs network once). Offline builds that already include the weights work without download.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

```
main.py
neonframe/
  app.py          # PySide6 GUI
  worker.py       # background analysis thread
  detector.py     # YOLO + HOG + ESP boxes
  capture.py      # files + mss screen grab
  presets.py      # Novice / Smart / Master
  settings.py
  styles.py
tests/
.github/workflows/build.yml
```

## Limitations

- COCO “person” detection is not game-specific skin/character ID.
- Small, distant, stylized, or heavily occluded figures may be missed.
- Screen capture grabs the **desktop bitmap** you authorize — not an in-process game overlay hook.
- Packaged EXE is large because it bundles PySide6, OpenCV, and PyTorch/Ultralytics.
- GitHub free Actions minutes and artifact retention apply.

## Ethics / scope

Use only on media and displays you are allowed to analyze. Do not use this project to cheat in online games.
