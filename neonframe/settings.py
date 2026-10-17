"""Persistent application settings."""

from __future__ import annotations

import json
import os
from copy import deepcopy

DEFAULTS: dict = {
    "overlay_enabled": True,
    "detection_enabled": True,
    "opacity": 85,
    "confidence": 50,
    "box_color": "#ff2d6a",
    "label_color": "#c084fc",
    "preset": "Smart",
    "detection_speed": 50,
    "show_labels": True,
    "source_mode": "file",
}


def settings_path() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    return os.path.join(base, "NeonFrame", "settings.json")


def load_settings(path: str | None = None) -> dict:
    try:
        with open(path or settings_path(), encoding="utf-8") as handle:
            data = json.load(handle)
        merged = deepcopy(DEFAULTS)
        for key, value in data.items():
            if key in DEFAULTS:
                merged[key] = value
        return merged
    except (OSError, ValueError, TypeError):
        return deepcopy(DEFAULTS)


def save_settings(values: dict, path: str | None = None) -> None:
    target = path or settings_path()
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    payload = {**DEFAULTS, **{k: v for k, v in values.items() if k in DEFAULTS}}
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
