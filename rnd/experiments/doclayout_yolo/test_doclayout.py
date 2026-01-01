#!/usr/bin/env python3
"""
DocLayout-YOLO 테스트 스크립트
- 사전학습 모델 다운로드
- 다양한 도면 이미지에서 레이아웃 검출
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

# Hugging Face hub for model download
from huggingface_hub import hf_hub_download

# DocLayout-YOLO
from doclayout_yolo import YOLOv10

import cv2
import torch


def download_model(model_name: str = "DocLayout-YOLO-DocStructBench-onnx") -> str:
    """
    Hugging Face에서 DocLayout-YOLO 모델 다운로드

    Available models:
    - DocLayout-YOLO-DocStructBench: 기본 모델 (PT)
    - DocLayout-YOLO-DocStructBench-onnx: ONNX 버전
    - doclayout_yolo_docstructbench_imgsz1024: 1024px 학습 버전
    """
    print(f"[INFO] Downloading model: {model_name}")

    # 모델 저장 경로
    cache_dir = Path(__file__).parent / "models"
    cache_dir.mkdir(exist_ok=True)

    # Hugging Face에서 모델 다운로드
    try:
        model_path = hf_hub_download(
            repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
            filename="doclayout_yolo_docstructbench_imgsz1024.pt",
            cache_dir=str(cache_dir),
        )
        print(f"[INFO] Model downloaded to: {model_path}")
        return model_path
    except Exception as e:
        print(f"[ERROR] Failed to download model: {e}")
        # 대안: docstructbench 기본 모델 시도
        try:
            model_path = hf_hub_download(
                repo_id="juliozhao/DocLayout-YOLO-DocStructBench",
                filename="doclayout_yolo_docstructbench.pt",
                cache_dir=str(cache_dir),
            )
            print(f"[INFO] Fallback model downloaded to: {model_path}")
            return model_path
        except Exception as e2:
            print(f"[ERROR] Fallback also failed: {e2}")
            raise


def run_inference(model: YOLOv10, image_path: str, output_dir: Path, conf: float = 0.15) -> dict:
    """단일 이미지에 대한 추론 실행"""

    image_name = Path(image_path).stem
    print(f"\n[PROCESSING] {image_name}")

    # 이미지 존재 확인
    if not os.path.exists(image_path):
        print(f"[ERROR] Image not found: {image_path}")
        return {"error": "Image not found"}

    # 추론 시간 측정
    start_time = time.time()

    # 추론 실행
    results = model.predict(
        image_path,
        imgsz=1024,
        conf=conf,
        device="cuda:0" if torch.cuda.is_available() else "cpu",
    )

    inference_time = time.time() - start_time

    # 결과 처리
    detections = []
    if results and len(results) > 0:
        for det in results[0].boxes:
            cls_id = int(det.cls)
            cls_name = model.names[cls_id] if hasattr(model, 'names') else f"class_{cls_id}"
            confidence = float(det.conf)
            bbox = det.xyxy[0].tolist()

            detections.append({
                "class": cls_name,
                "confidence": round(confidence, 3),
                "bbox": [round(x, 1) for x in bbox],
            })

    # 결과 이미지 저장
    if results and len(results) > 0:
        annotated_frame = results[0].plot(pil=True, line_width=3, font_size=15)
        output_path = output_dir / f"{image_name}_result.jpg"
        cv2.imwrite(str(output_path), annotated_frame)
        print(f"[SAVED] {output_path}")

    # 통계 출력
    print(f"[RESULT] {len(detections)} objects detected in {inference_time:.2f}s")

    # 클래스별 카운트
    class_counts = {}
    for det in detections:
        cls = det["class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1

    if class_counts:
        print(f"[CLASSES] {class_counts}")

    return {
        "image": image_name,
        "inference_time": round(inference_time, 3),
        "detections": detections,
        "class_counts": class_counts,
    }


def main():
    """메인 테스트 실행"""

    print("=" * 60)
    print("DocLayout-YOLO 테스트")
    print("=" * 60)

    # GPU 상태 확인
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"[GPU] {gpu_name} ({gpu_mem:.1f}GB)")
    else:
        print("[GPU] CUDA not available, using CPU")

    # 1. 모델 다운로드
    print("\n" + "-" * 40)
    print("Step 1: 모델 다운로드")
    print("-" * 40)

    model_path = download_model()

    # 2. 모델 로드
    print("\n" + "-" * 40)
    print("Step 2: 모델 로드")
    print("-" * 40)

    model = YOLOv10(model_path)
    print(f"[INFO] Model loaded successfully")
    print(f"[INFO] Classes: {model.names}")

    # 3. 테스트 이미지 정의
    base_path = Path("/home/uproot/ax/poc")
    test_images = [
        # 기계 도면
        base_path / "web-ui/public/samples/sample2_interm_shaft.jpg",
        base_path / "web-ui/public/samples/sample3_s60me_shaft.jpg",
        # P&ID 도면
        base_path / "web-ui/public/samples/sample6_pid_diagram.png",
        base_path / "web-ui/public/samples/bwms_pid_sample.png",
        # 청사진
        base_path / "web-ui/public/samples/sample8_blueprint_31.jpg",
        base_path / "blueprint-ai-bom/test_drawings/img_00031.jpg",
    ]

    # 존재하는 이미지만 필터
    test_images = [img for img in test_images if img.exists()]

    print(f"\n[INFO] Testing {len(test_images)} images")

    # 4. 추론 실행
    print("\n" + "-" * 40)
    print("Step 3: 추론 실행")
    print("-" * 40)

    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    all_results = []
    for image_path in test_images:
        result = run_inference(model, str(image_path), output_dir)
        all_results.append(result)

    # 5. 요약 리포트
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    total_detections = sum(len(r.get("detections", [])) for r in all_results)
    avg_time = sum(r.get("inference_time", 0) for r in all_results) / len(all_results)

    print(f"총 이미지: {len(all_results)}")
    print(f"총 검출: {total_detections}")
    print(f"평균 추론 시간: {avg_time:.2f}초")

    # 전체 클래스 분포
    all_class_counts = {}
    for r in all_results:
        for cls, cnt in r.get("class_counts", {}).items():
            all_class_counts[cls] = all_class_counts.get(cls, 0) + cnt

    if all_class_counts:
        print(f"\n클래스별 검출 수:")
        for cls, cnt in sorted(all_class_counts.items(), key=lambda x: -x[1]):
            print(f"  - {cls}: {cnt}")

    print(f"\n결과 이미지 저장 위치: {output_dir}")
    print("\n" + "=" * 60)

    return all_results


if __name__ == "__main__":
    results = main()
