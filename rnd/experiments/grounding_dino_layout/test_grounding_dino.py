#!/usr/bin/env python3
"""
Grounding DINO 제로샷 레이아웃 디텍션 — 기계도면 PoC

HuggingFace transformers의 GroundingDINO를 사용하여
학습 없이 텍스트 프롬프트만으로 기계도면의 영역을 검출한다.

테스트 대상:
- GT-1: TD0062037 (Thrust Bearing ASSY)
- GT-2: TD0062055 (Radial Bearing ASSY)
- 추가 샘플 3개
"""

import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

# ── 설정 ──────────────────────────────────────────────
MODEL_ID = "IDEA-Research/grounding-dino-base"
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DRAWINGS_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
OUTPUT_DIR = Path(__file__).parent / "results"

# 기계도면용 프롬프트 세트
PROMPT_SETS = {
    "layout_basic": "title block. drawing view. dimension text. table.",
    "layout_detailed": "title block. main drawing. cross section view. parts list table. notes area. border frame.",
    "engineering": "bearing drawing. dimension annotation. tolerance text. section view label. revision block.",
    "structural": "large circle. small circle. center line. arrow. text block. rectangular frame.",
}

# 테스트 도면 (GT + 샘플)
TEST_DRAWINGS = [
    "TD0062037",  # GT-1: Thrust Bearing ASSY
    "TD0062055",  # GT-2: Radial Bearing ASSY
    "TD0062039",  # k_priority 승격 도면
    "TD0060700",  # 비베어링 (CASING)
    "TD0060707",  # 비베어링 (LOCKING PIN)
]

# 신뢰도 임계값
CONFIDENCE_THRESHOLDS = [0.15, 0.25, 0.35]


def load_model():
    """Grounding DINO 모델 로드"""
    print(f"[INFO] Loading {MODEL_ID} on {DEVICE}")
    start = time.time()

    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(MODEL_ID).to(DEVICE)

    elapsed = time.time() - start
    print(f"[INFO] Model loaded in {elapsed:.1f}s")

    # GPU 메모리 확인
    if torch.cuda.is_available():
        mem = torch.cuda.memory_allocated() / 1024**3
        print(f"[GPU] Memory used: {mem:.2f} GB")

    return processor, model


def detect(processor, model, image: Image.Image, text_prompt: str, threshold: float = 0.25):
    """단일 이미지 + 프롬프트로 제로샷 검출"""
    inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(DEVICE)

    with torch.no_grad():
        outputs = model(**inputs)

    # 후처리
    results = processor.post_process_grounded_object_detection(
        outputs,
        inputs.input_ids,
        threshold=threshold,
        text_threshold=threshold,
        target_sizes=[image.size[::-1]],  # (height, width)
    )

    return results[0]  # 첫 번째 이미지 결과


def draw_results(image: Image.Image, result: dict, output_path: Path):
    """검출 결과를 이미지에 시각화"""
    img = np.array(image)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 클래스별 색상
    colors = [
        (0, 255, 0),    # 녹색
        (255, 0, 0),    # 파랑
        (0, 0, 255),    # 빨강
        (255, 255, 0),  # 시안
        (0, 255, 255),  # 노랑
        (255, 0, 255),  # 마젠타
        (128, 255, 0),  # 라임
        (255, 128, 0),  # 주황
    ]

    boxes = result["boxes"].cpu().numpy()
    scores = result["scores"].cpu().numpy()
    labels = result["labels"]

    # 라벨별 색상 매핑
    unique_labels = list(set(labels))
    label_color_map = {lbl: colors[i % len(colors)] for i, lbl in enumerate(unique_labels)}

    for box, score, label in zip(boxes, scores, labels):
        x1, y1, x2, y2 = map(int, box)
        color = label_color_map[label]

        # 바운딩 박스
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

        # 라벨 + 신뢰도
        text = f"{label} {score:.2f}"
        font_scale = max(0.6, min(img.shape[1] / 2000, 1.2))
        thickness = max(1, int(font_scale * 2))
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)

        cv2.rectangle(img, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(img, text, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, (255, 255, 255), thickness)

    cv2.imwrite(str(output_path), img)
    return str(output_path)


def test_single_drawing(processor, model, drawing_id: str, prompt_sets: dict, threshold: float):
    """단일 도면에 여러 프롬프트 세트 테스트"""
    image_path = DRAWINGS_DIR / f"{drawing_id}.png"
    if not image_path.exists():
        print(f"[SKIP] {drawing_id} — file not found")
        return None

    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    print(f"\n{'='*60}")
    print(f"[TEST] {drawing_id} ({w}x{h}px, threshold={threshold})")
    print(f"{'='*60}")

    results = {}
    for prompt_name, prompt_text in prompt_sets.items():
        start = time.time()
        result = detect(processor, model, image, prompt_text, threshold)
        elapsed = time.time() - start

        n_boxes = len(result["boxes"])
        labels = result["labels"]
        scores = result["scores"].cpu().numpy()

        print(f"\n  [{prompt_name}] {n_boxes} detections in {elapsed:.2f}s")
        print(f"  Prompt: \"{prompt_text}\"")

        # 라벨별 통계
        label_stats = {}
        for lbl, sc in zip(labels, scores):
            if lbl not in label_stats:
                label_stats[lbl] = []
            label_stats[lbl].append(float(sc))

        for lbl, scs in sorted(label_stats.items()):
            avg_sc = sum(scs) / len(scs)
            print(f"    - {lbl}: {len(scs)}개 (avg conf: {avg_sc:.3f})")

        # 시각화 저장
        out_dir = OUTPUT_DIR / drawing_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{prompt_name}_t{int(threshold*100)}.jpg"
        draw_results(image, result, out_path)

        results[prompt_name] = {
            "n_detections": n_boxes,
            "inference_time": round(elapsed, 3),
            "label_stats": {k: {"count": len(v), "avg_conf": round(sum(v)/len(v), 3)} for k, v in label_stats.items()},
        }

    return results


def main():
    print("=" * 60)
    print("Grounding DINO 제로샷 레이아웃 디텍션 — 기계도면 PoC")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 모델 로드
    processor, model = load_model()

    # 전체 결과
    all_results = {}

    # 각 도면 × 각 프롬프트 세트 × threshold=0.25 기본
    threshold = 0.25
    for drawing_id in TEST_DRAWINGS:
        result = test_single_drawing(processor, model, drawing_id, PROMPT_SETS, threshold)
        if result:
            all_results[drawing_id] = result

    # 결과 JSON 저장
    summary_path = OUTPUT_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {summary_path}")

    # ── 요약 리포트 ──
    print(f"\n{'='*60}")
    print("요약 리포트")
    print(f"{'='*60}")

    for drawing_id, prompt_results in all_results.items():
        print(f"\n{drawing_id}:")
        for prompt_name, stats in prompt_results.items():
            n = stats["n_detections"]
            t = stats["inference_time"]
            labels = ", ".join(f"{k}({v['count']})" for k, v in stats["label_stats"].items())
            print(f"  {prompt_name}: {n}개 ({t:.2f}s) — {labels}")

    print(f"\n결과 이미지: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
