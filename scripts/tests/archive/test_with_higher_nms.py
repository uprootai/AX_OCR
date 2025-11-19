#!/usr/bin/env python3
"""
NMS 임계값을 높여서 테스트
"""
import sys
sys.path.insert(0, '/home/uproot/ax/poc')
from improved_yolo_detection import ImprovedYOLODetector
import json

detector = ImprovedYOLODetector()

image_path = "/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg"

print("="*70)
print("NMS 임계값 테스트")
print("="*70)

# 원본 검출
result = detector.detect(image_path, conf=0.25, iou=0.8, imgsz=1280)  # IOU 0.8로 증가
original = result.get('detections', [])

# 필터링
filtered = detector.filter_text_blocks(original, min_confidence=0.65)  # 신뢰도도 0.65로 증가

# 중복 제거 (더 엄격하게)
final = detector.remove_duplicates(filtered, iou_threshold=0.3)  # 0.3으로 엄격하게

print(f"원본 검출: {len(original)}개")
print(f"필터링 후: {len(filtered)}개")
print(f"최종: {len(final)}개")
print()

# 클래스별 카운트
final_classes = {}
for det in final:
    cls = det.get('class_name', 'unknown')
    if cls not in final_classes:
        final_classes[cls] = []
    final_classes[cls].append(det)

print("최종 검출:")
for cls, dets in sorted(final_classes.items(), key=lambda x: -len(x[1])):
    avg_conf = sum(d.get('confidence', 0) for d in dets) / len(dets) * 100
    print(f"  {cls:20s}: {len(dets):2d}개 (평균: {avg_conf:5.1f}%)")

# Ground Truth 매칭
matches = detector.analyze_ground_truth_matching(final)
detected_count = len(matches["GD&T"]) + len(matches["치수"])
accuracy = (detected_count / 9) * 100

print(f"\nGround Truth 매칭: {detected_count}/9 = {accuracy:.1f}%")

