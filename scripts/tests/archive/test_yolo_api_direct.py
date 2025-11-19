#!/usr/bin/env python3
"""
YOLO API 직접 테스트 - 웹 UI와 동일한 방식으로
"""
import requests
import json
from pathlib import Path

# Test image
image_path = "/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg"

print("Testing YOLO API with direct request...")
print(f"Image: {Path(image_path).name}")
print()

try:
    with open(image_path, 'rb') as f:
        files = {'file': (Path(image_path).name, f, 'image/jpeg')}
        data = {
            'conf': 0.25,
            'iou': 0.7,
            'imgsz': 1280,
            'visualize': True
        }
        
        response = requests.post(
            'http://localhost:5005/api/v1/detect',
            files=files,
            data=data,
            timeout=60
        )
        
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Success!")
        print(f"Processing time: {result.get('processing_time', 'N/A'):.3f}s")
        print(f"Total detections: {len(result.get('detections', []))}")
        print()
        
        # Analyze detections
        detections = result.get('detections', [])
        
        # Group by class
        class_groups = {}
        for det in detections:
            cls = det.get('class', 'unknown')
            if cls not in class_groups:
                class_groups[cls] = []
            class_groups[cls].append(det)
        
        print("Detections by class:")
        for cls, dets in sorted(class_groups.items(), key=lambda x: -len(x[1])):
            avg_conf = sum(d.get('confidence', 0) for d in dets) / len(dets)
            print(f"  {cls}: {len(dets)} ({avg_conf:.1f}% avg confidence)")
        
        print()
        print("Top 10 detections:")
        sorted_dets = sorted(detections, key=lambda x: x.get('confidence', 0), reverse=True)
        for i, det in enumerate(sorted_dets[:10], 1):
            print(f"  {i}. {det.get('class', 'unknown')}: {det.get('confidence', 0):.1f}% "
                  f"at [{det.get('x', 0):.0f}, {det.get('y', 0):.0f}] "
                  f"{det.get('w', 0):.0f}x{det.get('h', 0):.0f}")
        
        # Save full result
        with open('/tmp/yolo_detailed_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        print()
        print("Full result saved to /tmp/yolo_detailed_result.json")
        
    else:
        print(f"❌ Failed: HTTP {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
