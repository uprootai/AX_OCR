#!/usr/bin/env python3
"""
Phase 2 Step 1: 87개 전체 도면에 Grounding DINO 배치 실행 → YOLO 형식 pre-label 생성

출력:
  dataset/
    images/train/  (도면 심볼릭 링크)
    labels/train/  (YOLO 형식 .txt)
    data.yaml      (YOLO 학습 설정)
"""

import json
import shutil
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

# ── 설정 ──────────────────────────────────────────────
MODEL_ID = "IDEA-Research/grounding-dino-base"
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DRAWINGS_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUTPUT_DIR = Path(__file__).parent / "dataset"
THRESHOLD = 0.20  # 낮은 임계값으로 최대한 많은 pre-label 확보

# 커스텀 클래스 정의 (6개)
CLASSES = [
    "title_block",    # 0: 타이틀 블록 (우하단)
    "main_view",      # 1: 메인 도면 영역
    "section_view",   # 2: 단면도
    "table",          # 3: 테이블 (부품목록, 토크표 등)
    "notes",          # 4: 노트/사양 영역
    "circle_feature", # 5: 원형 구조 (베어링 외경 등)
]

# Grounding DINO 라벨 → 커스텀 클래스 매핑
LABEL_MAP = {
    # title_block (0)
    "title block": 0,
    "title": 0,
    # main_view (1)
    "main drawing": 1,
    "drawing view": 1,
    "view": 1,
    "drawing": 1,
    "bearing drawing": 1,
    # section_view (2)
    "cross section view": 2,
    "cross section": 2,
    "section view": 2,
    "cross view": 2,
    # table (3)
    "table": 3,
    "parts list table": 3,
    "list table": 3,
    "parts list": 3,
    "parts": 3,
    # notes (4)
    "notes area": 4,
    "notes": 4,
    "text block": 4,
    "revision block": 4,
    # circle_feature (5)
    "large circle": 5,
    "small circle": 5,
}

# 최적 프롬프트 조합 (Phase 1 결과 기반)
PROMPTS = [
    "title block. main drawing. cross section view. parts list table. notes area.",
    "large circle. small circle.",
]


def load_model():
    """모델 로드"""
    print(f"[INFO] Loading {MODEL_ID}")
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID).to(DEVICE)
    if torch.cuda.is_available():
        print(f"[GPU] {torch.cuda.get_device_name(0)}, mem: {torch.cuda.memory_allocated()/1024**3:.1f}GB")
    return processor, model


def detect(processor, model, image, text_prompt, threshold):
    """제로샷 검출"""
    inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = model(**inputs)
    results = processor.post_process_grounded_object_detection(
        outputs, inputs.input_ids,
        threshold=threshold, text_threshold=threshold,
        target_sizes=[image.size[::-1]],
    )
    return results[0]


def xyxy_to_yolo(box, img_w, img_h):
    """xyxy → YOLO 형식 (cx, cy, w, h) 정규화"""
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2.0 / img_w
    cy = (y1 + y2) / 2.0 / img_h
    w = (x2 - x1) / img_w
    h = (y2 - y1) / img_h
    return cx, cy, w, h


def map_label(raw_label: str) -> int | None:
    """Grounding DINO 라벨 → 커스텀 클래스 ID"""
    raw = raw_label.strip().lower()
    # 정확 매치
    if raw in LABEL_MAP:
        return LABEL_MAP[raw]
    # 부분 매치
    for key, cls_id in LABEL_MAP.items():
        if key in raw or raw in key:
            return cls_id
    return None


def process_drawing(processor, model, image_path: Path, threshold: float):
    """단일 도면 처리 → YOLO 어노테이션 라인 리스트"""
    image = Image.open(image_path).convert("RGB")
    w, h = image.size

    all_detections = []

    for prompt in PROMPTS:
        result = detect(processor, model, image, prompt, threshold)

        for box, score, label in zip(
            result["boxes"].cpu().numpy(),
            result["scores"].cpu().numpy(),
            result["labels"],
        ):
            cls_id = map_label(label)
            if cls_id is None:
                continue

            cx, cy, bw, bh = xyxy_to_yolo(box, w, h)

            # 너무 작거나 큰 박스 필터링
            if bw * bh < 0.001:  # 0.1% 미만
                continue
            if bw > 0.98 and bh > 0.98:  # 거의 전체 이미지
                continue

            all_detections.append({
                "cls_id": cls_id,
                "cx": cx, "cy": cy, "bw": bw, "bh": bh,
                "score": float(score),
                "label": label,
            })

    # 같은 클래스 내 IoU 높은 중복 제거 (NMS 간이 버전)
    filtered = nms_per_class(all_detections, iou_threshold=0.5)
    return filtered


def iou_yolo(a, b):
    """YOLO 형식 (cx,cy,w,h) 정규화 좌표의 IoU"""
    ax1 = a["cx"] - a["bw"] / 2
    ay1 = a["cy"] - a["bh"] / 2
    ax2 = a["cx"] + a["bw"] / 2
    ay2 = a["cy"] + a["bh"] / 2
    bx1 = b["cx"] - b["bw"] / 2
    by1 = b["cy"] - b["bh"] / 2
    bx2 = b["cx"] + b["bw"] / 2
    by2 = b["cy"] + b["bh"] / 2

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = a["bw"] * a["bh"]
    area_b = b["bw"] * b["bh"]
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0


def nms_per_class(detections, iou_threshold=0.5):
    """클래스별 NMS"""
    from collections import defaultdict
    by_class = defaultdict(list)
    for d in detections:
        by_class[d["cls_id"]].append(d)

    result = []
    for cls_id, dets in by_class.items():
        dets.sort(key=lambda x: x["score"], reverse=True)
        kept = []
        for d in dets:
            if not any(iou_yolo(d, k) > iou_threshold for k in kept):
                kept.append(d)
        result.extend(kept)
    return result


def main():
    print("=" * 60)
    print("Phase 2: 87개 도면 배치 pre-label 생성")
    print("=" * 60)

    # 디렉토리 구조 생성
    img_dir = OUTPUT_DIR / "images" / "train"
    lbl_dir = OUTPUT_DIR / "labels" / "train"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    # 모델 로드
    processor, model = load_model()

    # 도면 목록
    drawings = sorted(DRAWINGS_DIR.glob("*.png"))
    print(f"[INFO] {len(drawings)} drawings found")

    stats = {"total": 0, "with_labels": 0, "total_boxes": 0, "class_counts": {c: 0 for c in CLASSES}}

    start_all = time.time()
    for i, img_path in enumerate(drawings):
        drawing_id = img_path.stem
        stats["total"] += 1

        # 검출
        detections = process_drawing(processor, model, img_path, THRESHOLD)

        # YOLO 라벨 파일 저장
        label_path = lbl_dir / f"{drawing_id}.txt"
        lines = []
        for d in detections:
            lines.append(f"{d['cls_id']} {d['cx']:.6f} {d['cy']:.6f} {d['bw']:.6f} {d['bh']:.6f}")
            stats["class_counts"][CLASSES[d["cls_id"]]] += 1

        with open(label_path, "w") as f:
            f.write("\n".join(lines))

        # 이미지 심볼릭 링크
        link_path = img_dir / img_path.name
        if not link_path.exists():
            link_path.symlink_to(img_path)

        n = len(lines)
        stats["total_boxes"] += n
        if n > 0:
            stats["with_labels"] += 1

        if (i + 1) % 10 == 0 or i == 0:
            elapsed = time.time() - start_all
            per_img = elapsed / (i + 1)
            eta = per_img * (len(drawings) - i - 1)
            print(f"  [{i+1}/{len(drawings)}] {drawing_id}: {n} labels ({elapsed:.0f}s, ETA {eta:.0f}s)")

    total_time = time.time() - start_all

    # data.yaml 생성
    yaml_content = f"""# Engineering Drawing Layout Detection — YOLO Dataset
# Auto-generated from Grounding DINO pre-labels
# {stats['total']} images, {stats['total_boxes']} pre-labels

path: {OUTPUT_DIR.resolve()}
train: images/train
val: images/train  # 초기 실험: train=val (pre-label이므로)

nc: {len(CLASSES)}
names: {CLASSES}
"""
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    # 요약
    print(f"\n{'='*60}")
    print(f"완료: {total_time:.1f}s ({total_time/stats['total']:.1f}s/도면)")
    print(f"{'='*60}")
    print(f"  총 도면: {stats['total']}")
    print(f"  라벨 있는 도면: {stats['with_labels']}")
    print(f"  총 바운딩 박스: {stats['total_boxes']}")
    print(f"  도면당 평균: {stats['total_boxes']/stats['total']:.1f}개")
    print(f"\n  클래스별 분포:")
    for cls, cnt in stats["class_counts"].items():
        print(f"    {cls}: {cnt}")
    print(f"\n  데이터셋: {OUTPUT_DIR}")
    print(f"  data.yaml: {yaml_path}")

    # 통계 저장
    with open(OUTPUT_DIR / "prelabel_stats.json", "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
