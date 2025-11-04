#!/usr/bin/env python3
"""
YOLOv11 프로토타입 테스트 스크립트
"""
import time
from ultralytics import YOLO
import torch

print("=" * 70)
print("🚀 YOLOv11 Prototype Test")
print("=" * 70)

# 환경 정보
print(f"Python: OK")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
print("=" * 70)

# 모델 로드
print("\n📥 Loading YOLOv11n model...")
start_time = time.time()
model = YOLO('yolo11n.pt')
load_time = time.time() - start_time
print(f"✅ Model loaded in {load_time:.2f}s")

# 모델 정보
print(f"\n📊 Model Info:")
print(f"   - Model: YOLOv11n (nano)")
print(f"   - Parameters: ~2.6M")
print(f"   - Task: Object Detection")
print(f"   - Classes: 80 (COCO dataset)")

# 테스트 추론
print(f"\n🔍 Running test inference...")
test_url = "https://ultralytics.com/images/bus.jpg"
print(f"   - Source: {test_url}")

start_time = time.time()
results = model.predict(
    source=test_url,
    save=True,
    conf=0.25,
    verbose=False
)
inference_time = time.time() - start_time

# 결과 분석
result = results[0]
boxes = result.boxes
num_detections = len(boxes)

print(f"\n✅ Inference complete!")
print(f"   - Processing time: {inference_time:.2f}s")
print(f"   - Detections: {num_detections} objects")

if num_detections > 0:
    print(f"\n📦 Detected objects:")
    for i, box in enumerate(boxes[:10]):  # 최대 10개만 출력
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        cls_name = model.names[cls_id]
        print(f"   {i+1}. {cls_name}: {conf:.2f}")

print(f"\n📁 Results saved to: {result.save_dir}")

print("\n" + "=" * 70)
print("✅ Prototype Test Complete!")
print("=" * 70)
print("\n📌 Next Steps:")
print("   1. Test with engineering drawing images")
print("   2. Prepare custom dataset (100+ images)")
print("   3. Fine-tune model with transfer learning")
print("   4. Deploy API server")
print("\n🎯 Expected Performance:")
print("   - Current (pretrained): General object detection")
print("   - After fine-tuning: F1 70-85% on engineering drawings")
print("=" * 70)
