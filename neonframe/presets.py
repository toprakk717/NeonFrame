"""Detection presets: Novice / Smart / Master."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectionPreset:
    name: str
    confidence: float
    imgsz: int
    sample_step: int
    description: str


PRESETS: dict[str, DetectionPreset] = {
    "Novice": DetectionPreset(
        name="Novice",
        confidence=0.35,
        imgsz=416,
        sample_step=4,
        description="Faster scan, lower confidence bar — more candidates.",
    ),
    "Smart": DetectionPreset(
        name="Smart",
        confidence=0.50,
        imgsz=640,
        sample_step=2,
        description="Balanced accuracy and speed for typical footage.",
    ),
    "Master": DetectionPreset(
        name="Master",
        confidence=0.65,
        imgsz=800,
        sample_step=1,
        description="Stricter confidence, denser sampling — slower.",
    ),
}

PRESET_ORDER = ("Novice", "Smart", "Master")


def get_preset(name: str) -> DetectionPreset:
    return PRESETS.get(name, PRESETS["Smart"])
