"""OpenCV-backed tests. Skipped automatically when cv2 is unavailable."""

from __future__ import annotations

import unittest

try:
    import cv2  # noqa: F401
    import numpy as np

    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from neonframe.capture import is_image, is_video


@unittest.skipUnless(HAS_CV2, "OpenCV (cv2) not installed in this environment")
class DetectorTests(unittest.TestCase):
    def setUp(self):
        from neonframe.detector import reset_backend

        reset_backend()

    def test_empty_image(self):
        from neonframe.detector import detect_people

        self.assertEqual(detect_people(None), [])
        self.assertEqual(detect_people(np.zeros((0, 0, 3), dtype=np.uint8)), [])

    def test_draw_esp_changes_pixels(self):
        from neonframe.detector import draw_detections

        frame = np.zeros((80, 80, 3), dtype=np.uint8)
        out = draw_detections(frame, [(10, 10, 40, 50, 0.9)], style="esp")
        self.assertEqual(out.shape, frame.shape)
        self.assertFalse(np.array_equal(out, frame))

    def test_draw_rect_style(self):
        from neonframe.detector import draw_detections

        frame = np.zeros((40, 40, 3), dtype=np.uint8)
        out = draw_detections(frame, [(5, 5, 20, 25, 1.0)], style="box")
        self.assertFalse(np.array_equal(out, frame))

    def test_blank_frame_detection_runs(self):
        from neonframe.detector import detect_people

        frame = np.zeros((240, 160, 3), dtype=np.uint8)
        boxes = detect_people(frame, confidence=0.9, imgsz=320)
        self.assertIsInstance(boxes, list)


class CaptureHelperTests(unittest.TestCase):
    def test_extensions(self):
        self.assertTrue(is_image("a.PNG"))
        self.assertTrue(is_video("clip.mp4"))
        self.assertFalse(is_image("clip.mp4"))


if __name__ == "__main__":
    unittest.main()
