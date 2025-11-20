#!/usr/bin/env python3
"""
YOLOv11 추론 스크립트
"""
import argparse
from pathlib import Path
from ultralytics import YOLO
import cv2
import json
import time

# 클래스 이름 매핑
CLASS_NAMES = {
    0: 'diameter_dim',
    1: 'linear_dim',
    2: 'radius_dim',
    3: 'angular_dim',
    4: 'chamfer_dim',
    5: 'tolerance_dim',
    6: 'reference_dim',
    7: 'flatness',
    8: 'cylindricity',
    9: 'position',
    10: 'perpendicularity',
    11: 'parallelism',
    12: 'surface_roughness',
    13: 'text_block'
}

def yolo_to_edocr_format(result, image_shape):
    """YOLO 결과를 eDOCr 호환 포맷으로 변환"""
    img_height, img_width = image_shape[:2]

    dimensions = []
    gdt = []
    surface_roughness = []
    text_blocks = []

    boxes = result.boxes

    for i, box in enumerate(boxes):
        # 클래스 ID와 신뢰도
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = CLASS_NAMES.get(cls_id, 'unknown')

        # 바운딩 박스 (xyxy 포맷)
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # 픽셀 좌표로 변환
        x = int(x1)
        y = int(y1)
        width = int(x2 - x1)
        height = int(y2 - y1)

        bbox = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }

        # 클래스별로 분류
        if cls_id <= 6:  # Dimensions (0-6)
            dimensions.append({
                'type': class_name,
                'value': '',  # OCR refinement 필요
                'unit': 'mm',
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id <= 11:  # GD&T symbols (7-11)
            gdt.append({
                'type': class_name,
                'value': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id == 12:  # Surface roughness
            surface_roughness.append({
                'value': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

        elif cls_id == 13:  # Text block
            text_blocks.append({
                'text': '',  # OCR refinement 필요
                'bbox': bbox,
                'confidence': confidence
            })

    return {
        'dimensions': dimensions,
        'gdt': gdt,
        'surface_roughness': surface_roughness,
        'text_blocks': text_blocks,
        'total_detections': len(boxes)
    }

def draw_detections(image, result):
    """이미지에 검출 결과 그리기"""
    annotated_img = image.copy()
    boxes = result.boxes

    # 색상 정의 (BGR)
    colors = {
        'dimension': (255, 100, 0),     # Blue for dimensions
        'gdt': (0, 255, 100),           # Green for GD&T
        'surface': (0, 165, 255),       # Orange for surface
        'text': (255, 255, 0)           # Cyan for text
    }

    for box in boxes:
        cls_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = CLASS_NAMES.get(cls_id, 'unknown')

        # 바운딩 박스
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        # 색상 선택
        if cls_id <= 6:
            color = colors['dimension']
        elif cls_id <= 11:
            color = colors['gdt']
        elif cls_id == 12:
            color = colors['surface']
        else:
            color = colors['text']

        # 박스 그리기
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)

        # 라벨 그리기
        label = f"{class_name} {confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )

        cv2.rectangle(
            annotated_img,
            (x1, y1 - label_h - 10),
            (x1 + label_w, y1),
            color,
            -1
        )

        cv2.putText(
            annotated_img,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )

    return annotated_img

def run_inference(
    model_path,
    source,
    output_dir='runs/inference',
    conf_threshold=0.25,
    iou_threshold=0.7,
    imgsz=1280,
    save_images=True,
    save_json=True,
    device='0'
):
    """YOLO 추론 실행"""

    print("=" * 70)
    print("🔍 YOLOv11 Inference")
    print("=" * 70)
    print(f"Model: {model_path}")
    print(f"Source: {source}")
    print(f"Confidence threshold: {conf_threshold}")
    print(f"Image size: {imgsz}")
    print("=" * 70)

    # 모델 로드
    model = YOLO(model_path)

    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 추론 실행
    start_time = time.time()

    results = model.predict(
        source=source,
        conf=conf_threshold,
        iou=iou_threshold,
        imgsz=imgsz,
        device=device,
        save=False,  # 우리가 직접 저장
        verbose=True
    )

    elapsed_time = time.time() - start_time

    # 결과 처리
    print(f"\n📊 Processing {len(results)} images...")

    all_results = []

    for i, result in enumerate(results):
        image_path = Path(result.path)
        image_name = image_path.stem

        # 이미지 로드
        image = cv2.imread(str(image_path))

        # eDOCr 포맷으로 변환
        detection_result = yolo_to_edocr_format(result, image.shape)

        detection_result['image_name'] = image_name
        detection_result['image_path'] = str(image_path)
        detection_result['model'] = str(model_path)
        detection_result['inference_time'] = elapsed_time / len(results)

        all_results.append(detection_result)

        # 통계 출력
        print(f"✅ {image_name}: {detection_result['total_detections']} detections")

        # 어노테이션된 이미지 저장
        if save_images:
            annotated_img = draw_detections(image, result)
            save_path = output_path / f"{image_name}_annotated.jpg"
            cv2.imwrite(str(save_path), annotated_img)

        # JSON 저장
        if save_json:
            json_path = output_path / f"{image_name}_result.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detection_result, f, indent=2, ensure_ascii=False)

    # 전체 통계
    total_detections = sum(r['total_detections'] for r in all_results)
    avg_time = elapsed_time / len(results)

    print("\n" + "=" * 70)
    print("✅ Inference complete!")
    print("=" * 70)
    print(f"📊 Statistics:")
    print(f"   - Total images: {len(results)}")
    print(f"   - Total detections: {total_detections}")
    print(f"   - Average detections/image: {total_detections / len(results):.1f}")
    print(f"   - Total time: {elapsed_time:.2f}s")
    print(f"   - Average time/image: {avg_time:.2f}s")
    print(f"   - FPS: {1/avg_time:.2f}")
    print(f"📁 Results saved to: {output_path}")

    # 전체 요약 저장
    summary = {
        'total_images': len(results),
        'total_detections': total_detections,
        'average_detections_per_image': total_detections / len(results),
        'total_time': elapsed_time,
        'average_time_per_image': avg_time,
        'fps': 1 / avg_time,
        'results': all_results
    }

    summary_path = output_path / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary

def main():
    parser = argparse.ArgumentParser(description='YOLOv11 Inference on engineering drawings')

    parser.add_argument('--model', type=str, required=True,
                        help='Path to trained model (best.pt)')
    parser.add_argument('--source', type=str, required=True,
                        help='Image file or directory')
    parser.add_argument('--output', type=str, default='runs/inference',
                        help='Output directory')
    parser.add_argument('--conf', type=float, default=0.25,
                        help='Confidence threshold')
    parser.add_argument('--iou', type=float, default=0.7,
                        help='NMS IoU threshold')
    parser.add_argument('--imgsz', type=int, default=1280,
                        help='Image size')
    parser.add_argument('--device', type=str, default='0',
                        help='CUDA device or cpu')
    parser.add_argument('--no-save-images', action='store_true',
                        help='Do not save annotated images')
    parser.add_argument('--no-save-json', action='store_true',
                        help='Do not save JSON results')

    args = parser.parse_args()

    run_inference(
        model_path=args.model,
        source=args.source,
        output_dir=args.output,
        conf_threshold=args.conf,
        iou_threshold=args.iou,
        imgsz=args.imgsz,
        save_images=not args.no_save_images,
        save_json=not args.no_save_json,
        device=args.device
    )

if __name__ == '__main__':
    main()
