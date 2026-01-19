"""
BBox 유틸리티 모듈

다양한 bbox 형식 간 변환 및 연산을 위한 공통 유틸리티.
모든 API 서비스 및 벤치마크에서 일관되게 사용할 수 있습니다.

지원 형식:
- XYWH: {x, y, width, height} - YOLO API 표준 형식
- XYXY: {xmin, ymin, xmax, ymax} - COCO/PID2Graph 형식
- List: [x1, y1, x2, y2] 또는 [x, y, w, h]
"""
from typing import Dict, List, Tuple, Union, Optional
from dataclasses import dataclass


# Type aliases
BBoxXYWH = Dict[str, Union[int, float]]  # {x, y, width, height}
BBoxXYXY = Dict[str, Union[int, float]]  # {xmin, ymin, xmax, ymax}
BBoxList = List[Union[int, float]]       # [x1, y1, x2, y2] or [x, y, w, h]


@dataclass
class BBox:
    """
    통합 BBox 클래스

    내부적으로 xyxy 형식으로 저장하고, 필요에 따라 변환합니다.
    """
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @classmethod
    def from_xywh(cls, x: float, y: float, width: float, height: float) -> "BBox":
        """XYWH 형식에서 생성"""
        return cls(
            xmin=x,
            ymin=y,
            xmax=x + width,
            ymax=y + height
        )

    @classmethod
    def from_xyxy(cls, xmin: float, ymin: float, xmax: float, ymax: float) -> "BBox":
        """XYXY 형식에서 생성"""
        return cls(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    @classmethod
    def from_dict(cls, bbox_dict: Dict, format: str = "auto") -> "BBox":
        """
        딕셔너리에서 생성

        Args:
            bbox_dict: bbox 딕셔너리
            format: "xywh", "xyxy", 또는 "auto" (자동 감지)
        """
        if format == "auto":
            # 자동 감지: width/height 키가 있으면 xywh, xmin/xmax가 있으면 xyxy
            if "width" in bbox_dict or "w" in bbox_dict:
                format = "xywh"
            elif "xmin" in bbox_dict or "x1" in bbox_dict:
                format = "xyxy"
            else:
                format = "xywh"  # 기본값

        if format == "xywh":
            x = bbox_dict.get("x", bbox_dict.get("x1", 0))
            y = bbox_dict.get("y", bbox_dict.get("y1", 0))
            w = bbox_dict.get("width", bbox_dict.get("w", 0))
            h = bbox_dict.get("height", bbox_dict.get("h", 0))
            return cls.from_xywh(x, y, w, h)
        else:  # xyxy
            xmin = bbox_dict.get("xmin", bbox_dict.get("x1", 0))
            ymin = bbox_dict.get("ymin", bbox_dict.get("y1", 0))
            xmax = bbox_dict.get("xmax", bbox_dict.get("x2", 0))
            ymax = bbox_dict.get("ymax", bbox_dict.get("y2", 0))
            return cls.from_xyxy(xmin, ymin, xmax, ymax)

    def to_xywh(self) -> BBoxXYWH:
        """XYWH 딕셔너리로 변환"""
        return {
            "x": self.xmin,
            "y": self.ymin,
            "width": self.xmax - self.xmin,
            "height": self.ymax - self.ymin
        }

    def to_xyxy(self) -> BBoxXYXY:
        """XYXY 딕셔너리로 변환"""
        return {
            "xmin": self.xmin,
            "ymin": self.ymin,
            "xmax": self.xmax,
            "ymax": self.ymax
        }

    def to_list_xywh(self) -> BBoxList:
        """[x, y, width, height] 리스트로 변환"""
        return [self.xmin, self.ymin, self.xmax - self.xmin, self.ymax - self.ymin]

    def to_list_xyxy(self) -> BBoxList:
        """[xmin, ymin, xmax, ymax] 리스트로 변환"""
        return [self.xmin, self.ymin, self.xmax, self.ymax]

    @property
    def width(self) -> float:
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        return self.ymax - self.ymin

    @property
    def area(self) -> float:
        return max(0, self.width) * max(0, self.height)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2)

    def iou(self, other: "BBox") -> float:
        """다른 BBox와의 IoU 계산"""
        return calculate_iou_bbox(self, other)

    def __repr__(self) -> str:
        return f"BBox(xmin={self.xmin:.1f}, ymin={self.ymin:.1f}, xmax={self.xmax:.1f}, ymax={self.ymax:.1f})"


# ============================================================================
# 변환 함수들
# ============================================================================

def xywh_to_xyxy(bbox: BBoxXYWH) -> BBoxXYXY:
    """
    XYWH 형식을 XYXY 형식으로 변환

    Args:
        bbox: {x, y, width, height} 형식

    Returns:
        {xmin, ymin, xmax, ymax} 형식
    """
    x = bbox.get("x", bbox.get("x1", 0))
    y = bbox.get("y", bbox.get("y1", 0))
    w = bbox.get("width", bbox.get("w", 0))
    h = bbox.get("height", bbox.get("h", 0))

    return {
        "xmin": x,
        "ymin": y,
        "xmax": x + w,
        "ymax": y + h
    }


def xyxy_to_xywh(bbox: BBoxXYXY) -> BBoxXYWH:
    """
    XYXY 형식을 XYWH 형식으로 변환

    Args:
        bbox: {xmin, ymin, xmax, ymax} 형식

    Returns:
        {x, y, width, height} 형식
    """
    xmin = bbox.get("xmin", bbox.get("x1", 0))
    ymin = bbox.get("ymin", bbox.get("y1", 0))
    xmax = bbox.get("xmax", bbox.get("x2", 0))
    ymax = bbox.get("ymax", bbox.get("y2", 0))

    return {
        "x": xmin,
        "y": ymin,
        "width": xmax - xmin,
        "height": ymax - ymin
    }


def normalize_bbox(bbox: Dict, target_format: str = "xyxy") -> Dict:
    """
    bbox를 지정된 형식으로 정규화

    Args:
        bbox: 임의의 bbox 딕셔너리
        target_format: "xyxy" 또는 "xywh"

    Returns:
        정규화된 bbox 딕셔너리
    """
    # 현재 형식 감지
    is_xywh = "width" in bbox or "w" in bbox

    if target_format == "xyxy":
        if is_xywh:
            return xywh_to_xyxy(bbox)
        else:
            return {
                "xmin": bbox.get("xmin", bbox.get("x1", 0)),
                "ymin": bbox.get("ymin", bbox.get("y1", 0)),
                "xmax": bbox.get("xmax", bbox.get("x2", 0)),
                "ymax": bbox.get("ymax", bbox.get("y2", 0))
            }
    else:  # xywh
        if not is_xywh:
            return xyxy_to_xywh(bbox)
        else:
            return {
                "x": bbox.get("x", bbox.get("x1", 0)),
                "y": bbox.get("y", bbox.get("y1", 0)),
                "width": bbox.get("width", bbox.get("w", 0)),
                "height": bbox.get("height", bbox.get("h", 0))
            }


# ============================================================================
# IoU 및 매칭 함수들
# ============================================================================

def calculate_iou(box1: Dict, box2: Dict) -> float:
    """
    두 bbox 간의 IoU 계산 (형식 자동 감지)

    Args:
        box1: 첫 번째 bbox (xywh 또는 xyxy)
        box2: 두 번째 bbox (xywh 또는 xyxy)

    Returns:
        IoU 값 (0-1)
    """
    # 둘 다 xyxy로 정규화
    b1 = normalize_bbox(box1, "xyxy")
    b2 = normalize_bbox(box2, "xyxy")

    # 교집합 계산
    x1 = max(b1["xmin"], b2["xmin"])
    y1 = max(b1["ymin"], b2["ymin"])
    x2 = min(b1["xmax"], b2["xmax"])
    y2 = min(b1["ymax"], b2["ymax"])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)

    # 각 박스의 면적
    area1 = (b1["xmax"] - b1["xmin"]) * (b1["ymax"] - b1["ymin"])
    area2 = (b2["xmax"] - b2["xmin"]) * (b2["ymax"] - b2["ymin"])

    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def calculate_iou_bbox(box1: BBox, box2: BBox) -> float:
    """
    두 BBox 객체 간의 IoU 계산

    Args:
        box1: 첫 번째 BBox
        box2: 두 번째 BBox

    Returns:
        IoU 값 (0-1)
    """
    x1 = max(box1.xmin, box2.xmin)
    y1 = max(box1.ymin, box2.ymin)
    x2 = min(box1.xmax, box2.xmax)
    y2 = min(box1.ymax, box2.ymax)

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    union = box1.area + box2.area - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def match_boxes(
    pred_boxes: List[Dict],
    gt_boxes: List[Dict],
    iou_threshold: float = 0.5,
    class_agnostic: bool = True
) -> Tuple[int, int, int, List[Tuple[int, int, float]]]:
    """
    예측 박스와 GT 박스 매칭

    Args:
        pred_boxes: 예측 박스 리스트 (각 박스는 {"bbox": {...}, "label": ...} 형식)
        gt_boxes: GT 박스 리스트 (각 박스는 {"bbox": {...}, "label": ...} 형식)
        iou_threshold: IoU 임계값
        class_agnostic: True면 클래스 무시, False면 클래스도 매칭

    Returns:
        (tp, fp, fn, matches): TP, FP, FN 개수와 매칭 리스트 [(pred_idx, gt_idx, iou), ...]
    """
    matched_gt = set()
    matches = []
    tp = 0

    for pred_idx, pred in enumerate(pred_boxes):
        pred_bbox = pred.get("bbox", pred)
        pred_label = pred.get("label", pred.get("class_name", ""))

        best_iou = 0
        best_gt_idx = -1

        for gt_idx, gt in enumerate(gt_boxes):
            if gt_idx in matched_gt:
                continue

            gt_bbox = gt.get("bbox", gt)
            gt_label = gt.get("label", gt.get("class_name", ""))

            # 클래스 체크 (class_agnostic이 False일 때만)
            if not class_agnostic and pred_label != gt_label:
                continue

            iou = calculate_iou(pred_bbox, gt_bbox)

            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        if best_iou >= iou_threshold and best_gt_idx >= 0:
            tp += 1
            matched_gt.add(best_gt_idx)
            matches.append((pred_idx, best_gt_idx, best_iou))

    fp = len(pred_boxes) - tp
    fn = len(gt_boxes) - len(matched_gt)

    return tp, fp, fn, matches


def calculate_metrics(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """
    Precision, Recall, F1 계산

    Args:
        tp: True Positives
        fp: False Positives
        fn: False Negatives

    Returns:
        (precision, recall, f1)
    """
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1


# ============================================================================
# YOLO 응답 변환 헬퍼
# ============================================================================

def convert_yolo_detections(detections: List[Dict], target_format: str = "xyxy") -> List[Dict]:
    """
    YOLO API 응답의 detection 리스트를 지정된 bbox 형식으로 변환

    Args:
        detections: YOLO API 응답의 detections 리스트
        target_format: "xyxy" 또는 "xywh"

    Returns:
        bbox가 변환된 detection 리스트
    """
    result = []
    for det in detections:
        converted = det.copy()
        if "bbox" in det:
            converted["bbox"] = normalize_bbox(det["bbox"], target_format)
        result.append(converted)
    return result
