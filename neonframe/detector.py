"""Person / visible-character detection for user-owned frames.

Backend order:
1. YOLOv8n ONNX via onnxruntime (preferred for packaged EXE)
2. Ultralytics YOLOv8 PyTorch weights (dev / first-run download)
3. OpenCV HOG people detector (offline fallback)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

Detection = tuple[int, int, int, int, float]  # x, y, w, h, score

_onnx_session = None
_yolo_model = None
_backend_failed: set[str] = set()
BACKEND_NAME = "none"


def reset_backend() -> None:
    global _onnx_session, _yolo_model, BACKEND_NAME, _backend_failed
    _onnx_session = None
    _yolo_model = None
    _backend_failed = set()
    BACKEND_NAME = "none"


def _search_roots() -> list[Path]:
    here = Path(__file__).resolve().parent
    roots = [Path.cwd(), here, here.parent]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.insert(0, Path(meipass))
    return roots


def _find_file(*names: str) -> Path | None:
    for root in _search_roots():
        for name in names:
            candidate = root / name
            if candidate.is_file():
                return candidate
    return None


def detect_people(
    image: np.ndarray | None,
    confidence: float = 0.5,
    imgsz: int = 640,
) -> list[Detection]:
    """Return bounding boxes for visible people in a BGR image."""
    if image is None or getattr(image, "size", 0) == 0:
        return []

    boxes = _detect_onnx(image, confidence, imgsz)
    if boxes is not None:
        return boxes

    boxes = _detect_ultralytics(image, confidence, imgsz)
    if boxes is not None:
        return boxes

    return _detect_hog(image, confidence)


def _detect_onnx(
    image: np.ndarray, confidence: float, imgsz: int
) -> list[Detection] | None:
    global _onnx_session, BACKEND_NAME
    if "onnx" in _backend_failed:
        return None
    try:
        import onnxruntime as ort
    except ImportError:
        _backend_failed.add("onnx")
        return None

    if _onnx_session is None:
        model_path = _find_file("yolov8n.onnx", "yolo11n.onnx")
        if model_path is None:
            _backend_failed.add("onnx")
            return None
        _onnx_session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"]
        )

    BACKEND_NAME = "yolov8n-onnx"
    session = _onnx_session
    input_name = session.get_inputs()[0].name
    blob, meta = _letterbox(image, imgsz)
    outputs = session.run(None, {input_name: blob})
    return _parse_yolo_onnx(outputs[0], meta, confidence, image.shape[:2])


def _letterbox(image: np.ndarray, imgsz: int):
    h, w = image.shape[:2]
    scale = min(imgsz / h, imgsz / w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((imgsz, imgsz, 3), 114, dtype=np.uint8)
    top = (imgsz - nh) // 2
    left = (imgsz - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    blob = canvas[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) / 255.0
    blob = np.expand_dims(blob, 0)
    meta = {"scale": scale, "left": left, "top": top, "imgsz": imgsz}
    return blob, meta


def _parse_yolo_onnx(
    output: np.ndarray,
    meta: dict,
    confidence: float,
    original_hw: tuple[int, int],
) -> list[Detection]:
    """Parse Ultralytics YOLO ONNX output [1, 84, N] or [1, N, 84]."""
    pred = np.squeeze(output)
    if pred.ndim != 2:
        return []
    if pred.shape[0] < pred.shape[1] and pred.shape[0] <= 100:
        # [84, N] → [N, 84]
        pred = pred.T

    boxes: list[Detection] = []
    oh, ow = original_hw
    scale = meta["scale"]
    left = meta["left"]
    top = meta["top"]

    for row in pred:
        if row.shape[0] < 6:
            continue
        # xywh + class scores
        scores = row[4:]
        class_id = int(np.argmax(scores))
        score = float(scores[class_id])
        if class_id != 0 or score < confidence:
            continue
        cx, cy, bw, bh = map(float, row[:4])
        x1 = (cx - bw / 2 - left) / scale
        y1 = (cy - bh / 2 - top) / scale
        x2 = (cx + bw / 2 - left) / scale
        y2 = (cy + bh / 2 - top) / scale
        x1 = int(max(0, min(ow - 1, x1)))
        y1 = int(max(0, min(oh - 1, y1)))
        x2 = int(max(0, min(ow - 1, x2)))
        y2 = int(max(0, min(oh - 1, y2)))
        if x2 <= x1 or y2 <= y1:
            continue
        boxes.append((x1, y1, x2 - x1, y2 - y1, score))

    return _nms(boxes, 0.45)


def _nms(boxes: list[Detection], iou_thresh: float) -> list[Detection]:
    if not boxes:
        return []
    arr = sorted(boxes, key=lambda b: b[4], reverse=True)
    keep: list[Detection] = []
    while arr:
        best = arr.pop(0)
        keep.append(best)
        arr = [b for b in arr if _iou(best, b) < iou_thresh]
    return keep


def _iou(a: Detection, b: Detection) -> float:
    ax1, ay1, aw, ah, _ = a
    bx1, by1, bw, bh, _ = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def _detect_ultralytics(
    image: np.ndarray, confidence: float, imgsz: int
) -> list[Detection] | None:
    global _yolo_model, BACKEND_NAME
    if "ultra" in _backend_failed:
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        _backend_failed.add("ultra")
        return None

    if _yolo_model is None:
        path = _find_file("yolov8n.pt", "yolo11n.pt")
        try:
            _yolo_model = YOLO(str(path) if path else "yolov8n.pt")
        except Exception:
            _backend_failed.add("ultra")
            return None

    BACKEND_NAME = "yolov8n"
    results = _yolo_model.predict(
        source=image,
        conf=float(confidence),
        imgsz=int(imgsz),
        classes=[0],
        verbose=False,
    )
    out: list[Detection] = []
    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            xyxy = box.xyxy[0].tolist()
            score = float(box.conf[0])
            x1, y1, x2, y2 = map(int, xyxy)
            out.append((x1, y1, max(1, x2 - x1), max(1, y2 - y1), score))
    return out


def _detect_hog(image: np.ndarray, confidence: float) -> list[Detection]:
    global BACKEND_NAME
    BACKEND_NAME = "hog"
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, weights = hog.detectMultiScale(
        image, winStride=(8, 8), padding=(8, 8), scale=1.05
    )
    threshold = float(confidence) * 2.0 - 1.0
    return [
        (int(x), int(y), int(w), int(h), float(score))
        for (x, y, w, h), score in zip(rects, weights.flatten())
        if float(score) >= threshold
    ]


def draw_detections(
    image: np.ndarray,
    detections: Sequence[Detection],
    color: tuple[int, int, int] = (106, 45, 255),
    opacity: float = 0.85,
    show_labels: bool = True,
    label_color: tuple[int, int, int] | None = None,
    style: str = "esp",
) -> np.ndarray:
    """Draw ESP-style corner boxes (or full rectangles) onto a copy of image."""
    result = image.copy()
    layer = result.copy()
    label_bgr = label_color or color
    thickness = 2
    for x, y, w, h, score in detections:
        if style == "esp":
            _draw_esp_box(layer, x, y, w, h, color, thickness)
        else:
            cv2.rectangle(layer, (x, y), (x + w, y + h), color, thickness)
        if show_labels:
            text = f"CHAR {score:.2f}"
            ty = max(18, y - 8)
            cv2.putText(
                layer,
                text,
                (x, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                label_bgr,
                2,
                cv2.LINE_AA,
            )
    alpha = min(1.0, max(0.0, float(opacity)))
    cv2.addWeighted(layer, alpha, result, 1.0 - alpha, 0, result)
    return result


def _draw_esp_box(
    image: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    length = max(8, min(w, h) // 4)
    x2, y2 = x + w, y + h
    cv2.line(image, (x, y), (x + length, y), color, thickness)
    cv2.line(image, (x, y), (x, y + length), color, thickness)
    cv2.line(image, (x2, y), (x2 - length, y), color, thickness)
    cv2.line(image, (x2, y), (x2, y + length), color, thickness)
    cv2.line(image, (x, y2), (x + length, y2), color, thickness)
    cv2.line(image, (x, y2), (x, y2 - length), color, thickness)
    cv2.line(image, (x2, y2), (x2 - length, y2), color, thickness)
    cv2.line(image, (x2, y2), (x2, y2 - length), color, thickness)
    cv2.rectangle(image, (x, y), (x2, y2), color, 1)
