"""Ground Truth Router - GT 라벨 관리 API 엔드포인트

GT 라벨 조회, 업로드, 삭제, 검출 결과와의 비교 기능 제공
"""

import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ground-truth", tags=["Ground Truth"])

# 기본 경로 설정
BASE_DIR = Path(__file__).parent.parent

# Reference GT (read-only, from test_drawings)
GT_LABELS_DIR = BASE_DIR / "test_drawings" / "labels"
GT_CLASSES_FILE = BASE_DIR / "test_drawings" / "classes.txt"

# Uploaded GT (writable, for user uploads)
GT_UPLOAD_DIR = BASE_DIR / "uploads" / "gt_labels"


# ==================== Helper Functions ====================

def load_gt_classes() -> list[str]:
    """GT 클래스 목록 로드"""
    if not GT_CLASSES_FILE.exists():
        return []
    with open(GT_CLASSES_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_yolo_label(label_file: Path, img_width: int, img_height: int, classes: list[str]) -> list[dict]:
    """YOLO 형식 라벨 파싱 (normalized -> absolute coords)"""
    if not label_file.exists():
        return []

    labels = []
    with open(label_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 5:
                continue

            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])

                # Convert normalized coords to absolute
                x1 = int((x_center - width / 2) * img_width)
                y1 = int((y_center - height / 2) * img_height)
                x2 = int((x_center + width / 2) * img_width)
                y2 = int((y_center + height / 2) * img_height)

                # Get class name
                class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"

                labels.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                })
            except (ValueError, IndexError):
                continue

    return labels


def find_gt_label_file(base_name: str) -> Path | None:
    """GT 라벨 파일 찾기 (업로드된 파일 우선, 없으면 레퍼런스 파일)"""
    # 업로드된 GT 먼저 확인
    uploaded_file = GT_UPLOAD_DIR / f"{base_name}.txt"
    if uploaded_file.exists():
        return uploaded_file
    # 레퍼런스 GT 확인
    reference_file = GT_LABELS_DIR / f"{base_name}.txt"
    if reference_file.exists():
        return reference_file
    return None


def load_gt_classes_for_file(label_file: Path) -> list[str]:
    """라벨 파일에 해당하는 클래스 목록 로드"""
    # 업로드된 GT인 경우 uploads의 classes.txt 사용
    if label_file.parent == GT_UPLOAD_DIR:
        classes_file = GT_UPLOAD_DIR / "classes.txt"
        if classes_file.exists():
            with open(classes_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
    # 레퍼런스 GT classes
    return load_gt_classes()


# ==================== Endpoints ====================

@router.get("/{filename}")
async def get_ground_truth(filename: str, img_width: int = 1000, img_height: int = 1000):
    """이미지 파일명에 해당하는 Ground Truth 라벨 조회

    Args:
        filename: 이미지 파일명 (예: img_00031.jpg)
        img_width: 이미지 너비 (절대 좌표 변환용)
        img_height: 이미지 높이 (절대 좌표 변환용)
    """
    # Remove extension and find label file
    base_name = Path(filename).stem
    label_file = find_gt_label_file(base_name)

    if not label_file:
        return {
            "filename": filename,
            "has_ground_truth": False,
            "labels": [],
            "count": 0,
            "message": f"GT 라벨 파일을 찾을 수 없습니다: {base_name}.txt"
        }

    classes = load_gt_classes_for_file(label_file)
    labels = parse_yolo_label(label_file, img_width, img_height, classes)

    return {
        "filename": filename,
        "has_ground_truth": True,
        "labels": labels,
        "count": len(labels),
        "classes": classes,
        "label_file": str(label_file.name)
    }


@router.get("")
async def list_available_ground_truth():
    """사용 가능한 GT 라벨 목록 조회 (업로드된 파일 + 레퍼런스 파일)"""
    label_files = []
    seen_names = set()

    # 업로드된 GT 먼저 (우선순위 높음)
    if GT_UPLOAD_DIR.exists():
        for f in GT_UPLOAD_DIR.iterdir():
            if f.is_file() and f.suffix == ".txt" and f.name != "classes.txt":
                label_files.append({
                    "filename": f.stem,
                    "label_file": f.name,
                    "size": f.stat().st_size,
                    "source": "uploaded"
                })
                seen_names.add(f.stem)

    # 레퍼런스 GT (업로드된 파일이 없는 경우만)
    if GT_LABELS_DIR.exists():
        for f in GT_LABELS_DIR.iterdir():
            if f.is_file() and f.suffix == ".txt" and f.name != "classes.txt" and not f.name.startswith("README"):
                if f.stem not in seen_names:
                    label_files.append({
                        "filename": f.stem,
                        "label_file": f.name,
                        "size": f.stat().st_size,
                        "source": "reference"
                    })

    classes = load_gt_classes()

    return {
        "labels": sorted(label_files, key=lambda x: x["filename"]),
        "count": len(label_files),
        "classes": classes,
        "classes_count": len(classes)
    }


@router.post("/upload")
async def upload_ground_truth(
    file: UploadFile = File(...),
    filename: str = None,
    img_width: int = 1000,
    img_height: int = 1000
):
    """GT 라벨 파일 업로드

    지원 형식:
    - JSON: [{"class_name": "...", "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 100}}, ...]
    - TXT (YOLO 형식): class_id x_center y_center width height (per line)
    - XML (Pascal VOC 형식)

    Args:
        file: 업로드할 GT 파일
        filename: 저장할 파일명 (없으면 원본 파일명 사용)
        img_width: 이미지 너비 (좌표 변환용)
        img_height: 이미지 높이 (좌표 변환용)
    """
    import json
    import xml.etree.ElementTree as ET

    # 파일명 결정
    original_name = Path(file.filename).stem
    target_name = filename if filename else original_name
    target_name = Path(target_name).stem  # 확장자 제거

    # GT 업로드 디렉토리 생성 (writable)
    GT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    content_str = content.decode('utf-8')

    labels = []
    classes = load_gt_classes()

    try:
        # JSON 형식
        if file.filename.endswith('.json'):
            data = json.loads(content_str)
            if isinstance(data, list):
                for item in data:
                    class_name = item.get('class_name', item.get('label', 'unknown'))
                    bbox = item.get('bbox', item.get('bndbox', {}))

                    # class_id 찾기 또는 추가
                    if class_name in classes:
                        class_id = classes.index(class_name)
                    else:
                        classes.append(class_name)
                        class_id = len(classes) - 1

                    # bbox를 YOLO 형식으로 변환 (x_center, y_center, width, height - normalized)
                    x1 = bbox.get('x1', bbox.get('xmin', 0))
                    y1 = bbox.get('y1', bbox.get('ymin', 0))
                    x2 = bbox.get('x2', bbox.get('xmax', 0))
                    y2 = bbox.get('y2', bbox.get('ymax', 0))

                    x_center = ((x1 + x2) / 2) / img_width
                    y_center = ((y1 + y2) / 2) / img_height
                    w = (x2 - x1) / img_width
                    h = (y2 - y1) / img_height

                    labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        # XML (Pascal VOC) 형식
        elif file.filename.endswith('.xml'):
            root = ET.fromstring(content_str)
            for obj in root.findall('object'):
                class_name = obj.find('name').text
                bndbox = obj.find('bndbox')

                if class_name in classes:
                    class_id = classes.index(class_name)
                else:
                    classes.append(class_name)
                    class_id = len(classes) - 1

                x1 = float(bndbox.find('xmin').text)
                y1 = float(bndbox.find('ymin').text)
                x2 = float(bndbox.find('xmax').text)
                y2 = float(bndbox.find('ymax').text)

                x_center = ((x1 + x2) / 2) / img_width
                y_center = ((y1 + y2) / 2) / img_height
                w = (x2 - x1) / img_width
                h = (y2 - y1) / img_height

                labels.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

        # TXT (YOLO) 형식 - 그대로 저장
        elif file.filename.endswith('.txt'):
            labels = [line.strip() for line in content_str.split('\n') if line.strip()]

        else:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 형식: {file.filename}")

        # YOLO 형식으로 저장 (uploads 디렉토리에 저장)
        label_file = GT_UPLOAD_DIR / f"{target_name}.txt"
        with open(label_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(labels))

        # 클래스 파일 저장 (uploads 디렉토리에)
        classes_file = GT_UPLOAD_DIR / "classes.txt"
        with open(classes_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(classes))

        return {
            "success": True,
            "filename": target_name,
            "label_file": str(label_file.name),
            "label_count": len(labels),
            "message": f"GT 라벨 {len(labels)}개가 저장되었습니다."
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 파싱 오류: {str(e)}")
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"XML 파싱 오류: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GT 업로드 실패: {str(e)}")


@router.delete("/{filename}")
async def delete_ground_truth(filename: str):
    """업로드된 GT 라벨 삭제 (레퍼런스 파일은 삭제 불가)

    Args:
        filename: 삭제할 GT 파일명 (확장자 제외)

    Returns:
        삭제 결과
    """
    base_name = Path(filename).stem

    # 업로드된 GT 파일만 삭제 가능
    uploaded_file = GT_UPLOAD_DIR / f"{base_name}.txt"

    if not uploaded_file.exists():
        # 레퍼런스 파일인지 확인
        reference_file = GT_LABELS_DIR / f"{base_name}.txt"
        if reference_file.exists():
            raise HTTPException(
                status_code=403,
                detail="레퍼런스 GT 파일은 삭제할 수 없습니다. 업로드된 파일만 삭제 가능합니다."
            )
        raise HTTPException(status_code=404, detail=f"GT 파일을 찾을 수 없습니다: {base_name}.txt")

    try:
        uploaded_file.unlink()
        logger.info(f"GT 파일 삭제: {uploaded_file}")

        return {
            "success": True,
            "filename": base_name,
            "message": f"GT 파일 '{base_name}.txt'가 삭제되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GT 삭제 실패: {str(e)}")


@router.post("/compare")
async def compare_with_ground_truth(
    filename: str,
    detections: list[dict],
    img_width: int = 1000,
    img_height: int = 1000,
    iou_threshold: float = 0.3,
    model_type: str = None,
    class_agnostic: bool = False
):
    """검출 결과와 Ground Truth 비교 (TP/FP/FN 계산)

    Args:
        filename: 이미지 파일명
        detections: 검출 결과 리스트 [{class_name, bbox: {x1,y1,x2,y2}}]
        img_width: 이미지 너비
        img_height: 이미지 높이
        iou_threshold: IoU 임계값 (기본 0.3)
        model_type: 모델 타입 (bom_detector 등) - 해당 클래스 파일 사용
        class_agnostic: True면 클래스 무관하게 위치(IoU)만으로 매칭
    """
    # Load GT (업로드된 파일 우선)
    base_name = Path(filename).stem
    label_file = find_gt_label_file(base_name)

    if not label_file:
        return {
            "error": "GT 라벨 파일을 찾을 수 없습니다",
            "has_ground_truth": False,
            "filename": filename,
            "searched_label": f"{base_name}.txt"
        }

    # 모델 타입에 따른 클래스 파일 선택
    if model_type:
        # 업로드된 GT 디렉토리 먼저 확인
        model_classes_file = GT_UPLOAD_DIR / f"classes_{model_type}.txt"
        if not model_classes_file.exists():
            model_classes_file = GT_LABELS_DIR / f"classes_{model_type}.txt"
        if model_classes_file.exists():
            with open(model_classes_file, "r", encoding="utf-8") as f:
                classes = [line.strip() for line in f if line.strip()]
        else:
            classes = load_gt_classes_for_file(label_file)
    else:
        classes = load_gt_classes_for_file(label_file)

    gt_labels = parse_yolo_label(label_file, img_width, img_height, classes)

    # Debug logging
    logger.debug(f"GT Compare: class_agnostic={class_agnostic}, model_type={model_type}")
    logger.debug(f"  filename={filename}, gt_count={len(gt_labels)}, det_count={len(detections)}")

    def calculate_iou(box1: dict, box2: dict) -> float:
        """IoU 계산"""
        x1 = max(box1["x1"], box2["x1"])
        y1 = max(box1["y1"], box2["y1"])
        x2 = min(box1["x2"], box2["x2"])
        y2 = min(box1["y2"], box2["y2"])

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
        area2 = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    # Match detections with GT
    matched_gt = set()
    matched_det = set()
    tp_matches = []

    for i, det in enumerate(detections):
        det_bbox = det.get("bbox", {})
        det_class = det.get("class_name", "")

        best_iou = 0
        best_gt_idx = -1

        for j, gt in enumerate(gt_labels):
            if j in matched_gt:
                continue

            iou = calculate_iou(det_bbox, gt["bbox"])
            gt_class = gt.get("class_name", "")

            # class_agnostic 모드: 위치(IoU)만으로 매칭 (클래스 무시)
            # 일반 모드: 클래스 매칭 + IoU threshold 조건
            if class_agnostic:
                # 위치만 확인
                if iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_gt_idx = j
                    if iou > 0.5:
                        logger.debug(f"  Match found: det[{i}] <-> gt[{j}], IoU={iou:.3f}")
            else:
                # 클래스도 일치해야 함
                if det_class == gt_class and iou > best_iou and iou >= iou_threshold:
                    best_iou = iou
                    best_gt_idx = j

        if best_gt_idx >= 0:
            matched_gt.add(best_gt_idx)
            matched_det.add(i)
            tp_matches.append({
                "detection_idx": i,
                "gt_idx": best_gt_idx,
                "iou": best_iou,
                "det_class": det_class,
                "gt_class": gt_labels[best_gt_idx]["class_name"],
                "gt_bbox": gt_labels[best_gt_idx]["bbox"],  # GT bbox for frontend cropping
                "class_match": det_class == gt_labels[best_gt_idx]["class_name"]
            })

    # Calculate metrics
    tp = len(tp_matches)
    fp = len(detections) - tp
    fn = len(gt_labels) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # FP details (detections that didn't match any GT)
    fp_detections = [detections[i] for i in range(len(detections)) if i not in matched_det]

    # FN details (GT that weren't detected)
    fn_labels = [gt_labels[i] for i in range(len(gt_labels)) if i not in matched_gt]

    return {
        "filename": filename,
        "has_ground_truth": True,
        "metrics": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "iou_threshold": iou_threshold
        },
        "gt_count": len(gt_labels),
        "detection_count": len(detections),
        "tp_matches": tp_matches,
        "fp_detections": fp_detections,
        "fn_labels": fn_labels
    }
