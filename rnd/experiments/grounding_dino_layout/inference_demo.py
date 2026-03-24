#!/usr/bin/env python3
"""
Phase 2 Step 3: 학습된 YOLO v11s 모델로 GT-1/GT-2 도면 추론 시각화
"""

from pathlib import Path
from ultralytics import YOLO

DRAWINGS_DIR = Path("/home/uproot/ax/poc/blueprint-ai-bom/data/dse_batch_test/converted_pngs")
RUNS_DIR = Path(__file__).parent / "runs"
OUTPUT_DIR = Path(__file__).parent / "results" / "yolo_inference"

# best 모델 찾기
best_candidates = sorted(RUNS_DIR.glob("layout_v1*/weights/best.pt"))
BEST_MODEL = str(best_candidates[-1]) if best_candidates else None

TEST_DRAWINGS = ["TD0062037", "TD0062055", "TD0062039", "TD0060700", "TD0060707"]


def main():
    print(f"[MODEL] {BEST_MODEL}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(BEST_MODEL)

    for drawing_id in TEST_DRAWINGS:
        img_path = DRAWINGS_DIR / f"{drawing_id}.png"
        if not img_path.exists():
            continue

        results = model.predict(
            str(img_path),
            imgsz=640,
            conf=0.3,
            device="0",
            verbose=False,
        )

        # 시각화 저장
        annotated = results[0].plot(pil=False, line_width=3, font_size=18)
        import cv2
        out_path = OUTPUT_DIR / f"{drawing_id}_layout.jpg"
        cv2.imwrite(str(out_path), annotated)

        # 검출 요약
        boxes = results[0].boxes
        n = len(boxes)
        cls_names = [model.names[int(c)] for c in boxes.cls]
        confs = [f"{float(c):.2f}" for c in boxes.conf]
        print(f"  {drawing_id}: {n} detections")
        for name, conf in zip(cls_names, confs):
            print(f"    - {name} ({conf})")

    print(f"\n결과: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
