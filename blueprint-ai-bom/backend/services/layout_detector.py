"""기계도면 레이아웃 디텍션 서비스

YOLO v11s 모델로 도면의 영역을 검출한다.
- 비베어링 필터: circle_feature 없으면 비베어링 판정
- 영역 제외: notes/table bbox 내 OCR 결과 필터링
- title_block OCR: 부품명 자동 추출

모델: rnd/experiments/grounding_dino_layout/runs/layout_v12/weights/best.pt
클래스: title_block, main_view, section_view, table, notes, circle_feature
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 모델 싱글턴
_model = None
def _find_model_path() -> str:
    """best.pt 경로 탐색 — 환경변수 > 프로젝트 루트 기준"""
    if os.environ.get("LAYOUT_MODEL_PATH"):
        return os.environ["LAYOUT_MODEL_PATH"]
    # blueprint-ai-bom/backend/services/ → poc/rnd/...
    poc_root = Path(__file__).resolve().parents[3]
    candidates = sorted(poc_root.glob("rnd/experiments/grounding_dino_layout/runs/layout_v1*/weights/best.pt"))
    return str(candidates[-1]) if candidates else ""

_MODEL_PATH = _find_model_path()


def _get_model():
    """YOLO 모델 싱글턴 로드"""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(_MODEL_PATH):
        logger.warning(f"Layout model not found: {_MODEL_PATH}")
        return None

    try:
        from ultralytics import YOLO
        _model = YOLO(_MODEL_PATH)
        logger.info(f"Layout model loaded: {_MODEL_PATH}")
        return _model
    except Exception as e:
        logger.warning(f"Layout model load failed: {e}")
        return None


def detect_layout(image_path: str, conf: float = 0.4) -> Optional[Dict]:
    """도면 레이아웃 검출

    Returns:
        {
            "regions": {"title_block": [...], "circle_feature": [...], ...},
            "is_bearing": True/False,
            "exclude_bboxes": [(x1,y1,x2,y2), ...],  # notes+table 영역
        }
        또는 모델 없으면 None
    """
    model = _get_model()
    if model is None:
        return None

    try:
        results = model.predict(str(image_path), imgsz=640, conf=conf, device="0", verbose=False)
    except Exception:
        # GPU 실패 시 CPU 폴백
        try:
            results = model.predict(str(image_path), imgsz=640, conf=conf, device="cpu", verbose=False)
        except Exception as e:
            logger.warning(f"Layout detection failed: {e}")
            return None

    boxes = results[0].boxes
    regions: Dict[str, List[dict]] = {}

    for box, cls_id, score in zip(
        boxes.xyxy.cpu().numpy(),
        boxes.cls.cpu().numpy(),
        boxes.conf.cpu().numpy(),
    ):
        cls_name = model.names[int(cls_id)]
        if cls_name not in regions:
            regions[cls_name] = []
        regions[cls_name].append({
            "bbox": [int(x) for x in box],  # [x1, y1, x2, y2]
            "confidence": float(score),
        })

    # 비베어링 판정: circle_feature 없으면
    has_circles = len(regions.get("circle_feature", [])) > 0
    is_bearing = has_circles

    # 제외 영역: notes + table의 bbox 수집
    exclude_bboxes = []
    for cls in ("notes", "table"):
        for det in regions.get(cls, []):
            exclude_bboxes.append(tuple(det["bbox"]))

    layout = {
        "regions": regions,
        "is_bearing": is_bearing,
        "exclude_bboxes": exclude_bboxes,
    }

    logger.info(
        f"Layout: bearing={is_bearing}, "
        f"circles={len(regions.get('circle_feature', []))}, "
        f"exclude_zones={len(exclude_bboxes)}"
    )
    return layout


def is_in_exclude_zone(bbox: dict, exclude_bboxes: List[Tuple], overlap_threshold: float = 0.5) -> bool:
    """OCR 결과 bbox가 제외 영역 안에 있는지 판정

    Args:
        bbox: {"x1": ..., "y1": ..., "x2": ..., "y2": ...}
        exclude_bboxes: [(x1,y1,x2,y2), ...]
        overlap_threshold: 겹침 비율 임계값

    Returns:
        True이면 제외 대상
    """
    if not exclude_bboxes or not bbox:
        return False

    bx1 = bbox.get("x1", 0)
    by1 = bbox.get("y1", 0)
    bx2 = bbox.get("x2", 0)
    by2 = bbox.get("y2", 0)
    b_area = max(1, (bx2 - bx1) * (by2 - by1))

    for ex1, ey1, ex2, ey2 in exclude_bboxes:
        # 교집합
        ix1 = max(bx1, ex1)
        iy1 = max(by1, ey1)
        ix2 = min(bx2, ex2)
        iy2 = min(by2, ey2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)

        if inter / b_area >= overlap_threshold:
            return True

    return False
