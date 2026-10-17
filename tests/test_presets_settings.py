"""Pure-Python tests that do not require OpenCV or PySide6."""

from __future__ import annotations

import os
import tempfile
import unittest

from neonframe.presets import PRESET_ORDER, get_preset
from neonframe.settings import DEFAULTS, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_defaults_keys(self):
        self.assertIn("overlay_enabled", DEFAULTS)
        self.assertIn("preset", DEFAULTS)

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "settings.json")
            save_settings(
                {
                    "confidence": 72,
                    "box_color": "#ff00aa",
                    "preset": "Master",
                    "detection_speed": 40,
                },
                path,
            )
            loaded = load_settings(path)
            self.assertEqual(loaded["confidence"], 72)
            self.assertEqual(loaded["box_color"], "#ff00aa")
            self.assertEqual(loaded["preset"], "Master")
            self.assertEqual(loaded["detection_speed"], 40)
            self.assertTrue(loaded["detection_enabled"])


class PresetTests(unittest.TestCase):
    def test_presets_exist(self):
        self.assertEqual(PRESET_ORDER, ("Novice", "Smart", "Master"))
        novice = get_preset("Novice")
        master = get_preset("Master")
        self.assertLess(novice.confidence, master.confidence)
        self.assertGreaterEqual(novice.sample_step, master.sample_step)

    def test_unknown_falls_back_to_smart(self):
        self.assertEqual(get_preset("Nope").name, "Smart")


if __name__ == "__main__":
    unittest.main()
