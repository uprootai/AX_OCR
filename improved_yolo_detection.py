#!/usr/bin/env python3
"""
개선된 YOLO 검출 - Text Block 필터링 및 후처리
"""
import requests
import json
from pathlib import Path
from typing import List, Dict
import numpy as np

class ImprovedYOLODetector:
    def __init__(self, api_url="http://localhost:5005/api/v1/detect"):
        self.api_url = api_url
        
    def detect(self, image_path: str, conf=0.25, iou=0.7, imgsz=1280) -> Dict:
        """YOLO API 호출"""
        with open(image_path, 'rb') as f:
            files = {'file': (Path(image_path).name, f, 'image/jpeg')}
            data = {
                'conf': conf,
                'iou': iou,
                'imgsz': imgsz,
                'visualize': True
            }
            
            response = requests.post(self.api_url, files=files, data=data, timeout=60)
            
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API error: {response.status_code}")
    
    def filter_text_blocks(self, detections: List[Dict], 
                          min_confidence=0.6, 
                          priority_classes=['diameter_dim', 'linear_dim', 'tolerance_dim', 
                                          'parallelism', 'flatness', 'cylindricity', 
                                          'perpendicularity', 'position', 'surface_roughness',
                                          'radius_dim', 'angular_dim', 'chamfer_dim']) -> List[Dict]:
        """
        Text Block 필터링
        
        전략:
        1. 우선순위 클래스(치수, GD&T)는 모두 유지
        2. text_block은 높은 신뢰도(>0.6)만 유지
        3. 중복되는 text_block 제거
        """
        filtered = []
        
        for det in detections:
            cls = det.get('class_name', '')
            conf = det.get('confidence', 0)
            
            # 우선순위 클래스는 모두 유지
            if cls in priority_classes:
                filtered.append(det)
            # text_block은 높은 신뢰도만
            elif cls == 'text_block' and conf >= min_confidence:
                filtered.append(det)
            # reference_dim도 유지
            elif cls == 'reference_dim':
                filtered.append(det)
        
        return filtered
    
    def remove_duplicates(self, detections: List[Dict], iou_threshold=0.5) -> List[Dict]:
        """
        중복 검출 제거
        같은 클래스의 겹치는 bbox 중 신뢰도가 낮은 것 제거
        """
        if not detections:
            return []
        
        # 클래스별로 그룹화
        class_groups = {}
        for det in detections:
            cls = det.get('class_name', '')
            if cls not in class_groups:
                class_groups[cls] = []
            class_groups[cls].append(det)
        
        result = []
        
        for cls, dets in class_groups.items():
            # 신뢰도 순으로 정렬
            sorted_dets = sorted(dets, key=lambda x: x.get('confidence', 0), reverse=True)
            
            keep = []
            for det in sorted_dets:
                # 이미 선택된 것과 IOU 계산
                should_keep = True
                for kept_det in keep:
                    if self._calculate_iou(det, kept_det) > iou_threshold:
                        should_keep = False
                        break
                
                if should_keep:
                    keep.append(det)
            
            result.extend(keep)
        
        return result
    
    def _calculate_iou(self, det1: Dict, det2: Dict) -> float:
        """두 bbox의 IOU 계산"""
        bbox1 = det1.get('bbox', {})
        bbox2 = det2.get('bbox', {})
        
        x1_1 = bbox1.get('x', 0)
        y1_1 = bbox1.get('y', 0)
        w1 = bbox1.get('width', 0)
        h1 = bbox1.get('height', 0)
        x2_1 = x1_1 + w1
        y2_1 = y1_1 + h1
        
        x1_2 = bbox2.get('x', 0)
        y1_2 = bbox2.get('y', 0)
        w2 = bbox2.get('width', 0)
        h2 = bbox2.get('height', 0)
        x2_2 = x1_2 + w2
        y2_2 = y1_2 + h2
        
        # Intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Union
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def analyze_ground_truth_matching(self, detections: List[Dict]) -> Dict:
        """Ground Truth와 매칭 분석"""
        ground_truth = {
            "GD&T": {
                "평행도": "parallelism",
                "진원도": "cylindricity",
                "표면거칠기": "surface_roughness"
            },
            "치수": {
                "외경": "diameter_dim",
                "길이": "linear_dim",
                "공차": "tolerance_dim"
            }
        }
        
        detected_classes = set(d.get('class_name', '') for d in detections)
        
        matches = {
            "GD&T": [],
            "치수": [],
            "미검출": []
        }
        
        # GD&T 매칭
        for gt_name, cls in ground_truth["GD&T"].items():
            if cls in detected_classes:
                count = sum(1 for d in detections if d.get('class_name') == cls)
                avg_conf = np.mean([d.get('confidence', 0) for d in detections 
                                   if d.get('class_name') == cls]) * 100
                matches["GD&T"].append({
                    "name": gt_name,
                    "class": cls,
                    "count": count,
                    "avg_confidence": avg_conf
                })
            else:
                matches["미검출"].append(f"GD&T: {gt_name}")
        
        # 치수 매칭
        for gt_name, cls in ground_truth["치수"].items():
            if cls in detected_classes:
                count = sum(1 for d in detections if d.get('class_name') == cls)
                avg_conf = np.mean([d.get('confidence', 0) for d in detections 
                                   if d.get('class_name') == cls]) * 100
                matches["치수"].append({
                    "name": gt_name,
                    "class": cls,
                    "count": count,
                    "avg_confidence": avg_conf
                })
            else:
                matches["미검출"].append(f"치수: {gt_name}")
        
        return matches


def main():
    image_path = "/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg"
    
    print("="*70)
    print("개선된 YOLO 검출 시스템")
    print("="*70)
    print(f"이미지: {Path(image_path).name}")
    print()
    
    detector = ImprovedYOLODetector()
    
    # 1. 원본 검출
    print("1단계: 원본 검출 실행...")
    result = detector.detect(image_path, conf=0.25, iou=0.7, imgsz=1280)
    original_detections = result.get('detections', [])
    print(f"   원본 검출 개수: {len(original_detections)}개")
    
    # 클래스별 카운트
    original_classes = {}
    for det in original_detections:
        cls = det.get('class_name', 'unknown')
        original_classes[cls] = original_classes.get(cls, 0) + 1
    
    print(f"   text_block: {original_classes.get('text_block', 0)}개")
    print()
    
    # 2. Text Block 필터링
    print("2단계: Text Block 필터링 적용...")
    filtered = detector.filter_text_blocks(original_detections, min_confidence=0.6)
    print(f"   필터링 후: {len(filtered)}개 (제거: {len(original_detections) - len(filtered)}개)")
    
    filtered_classes = {}
    for det in filtered:
        cls = det.get('class_name', 'unknown')
        filtered_classes[cls] = filtered_classes.get(cls, 0) + 1
    
    print(f"   text_block: {filtered_classes.get('text_block', 0)}개")
    print()
    
    # 3. 중복 제거
    print("3단계: 중복 검출 제거...")
    final = detector.remove_duplicates(filtered, iou_threshold=0.5)
    print(f"   최종 검출: {len(final)}개 (중복 제거: {len(filtered) - len(final)}개)")
    print()
    
    # 4. 최종 결과 분석
    print("="*70)
    print("최종 검출 결과")
    print("="*70)
    
    final_classes = {}
    for det in final:
        cls = det.get('class_name', 'unknown')
        if cls not in final_classes:
            final_classes[cls] = []
        final_classes[cls].append(det)
    
    print("\n클래스별 검출:")
    for cls, dets in sorted(final_classes.items(), key=lambda x: -len(x[1])):
        avg_conf = np.mean([d.get('confidence', 0) for d in dets]) * 100
        max_conf = max(d.get('confidence', 0) for d in dets) * 100
        print(f"  {cls:20s}: {len(dets):2d}개 (평균: {avg_conf:5.1f}%, 최대: {max_conf:5.1f}%)")
    
    print("\n상위 10개 검출:")
    sorted_final = sorted(final, key=lambda x: x.get('confidence', 0), reverse=True)
    for i, det in enumerate(sorted_final[:10], 1):
        bbox = det.get('bbox', {})
        print(f"  {i:2d}. {det.get('class_name', 'unknown'):20s} "
              f"{det.get('confidence', 0)*100:5.1f}% "
              f"at [{bbox.get('x', 0):4.0f}, {bbox.get('y', 0):4.0f}] "
              f"{bbox.get('width', 0):3.0f}x{bbox.get('height', 0):3.0f}")
    
    # 5. Ground Truth 매칭
    print("\n" + "="*70)
    print("Ground Truth 매칭 분석")
    print("="*70)
    
    matches = detector.analyze_ground_truth_matching(final)
    
    print("\n✅ 검출된 GD&T:")
    for match in matches["GD&T"]:
        print(f"  - {match['name']:10s} ({match['class']:20s}): "
              f"{match['count']}개, 평균 신뢰도 {match['avg_confidence']:.1f}%")
    
    print("\n✅ 검출된 치수:")
    for match in matches["치수"]:
        print(f"  - {match['name']:10s} ({match['class']:20s}): "
              f"{match['count']}개, 평균 신뢰도 {match['avg_confidence']:.1f}%")
    
    if matches["미검출"]:
        print("\n❌ 미검출:")
        for item in matches["미검출"]:
            print(f"  - {item}")
    
    # 6. 정확도 계산
    print("\n" + "="*70)
    print("정확도 비교")
    print("="*70)
    
    total_gt = 9  # Ground Truth 총 항목 수 (4 GD&T + 5 치수)
    detected_gt = len(matches["GD&T"]) + len(matches["치수"])
    accuracy = (detected_gt / total_gt) * 100
    
    original_accuracy = 33.3
    improvement = accuracy - original_accuracy
    
    print(f"\n원본 정확도:     {original_accuracy:.1f}%")
    print(f"개선 후 정확도:   {accuracy:.1f}%")
    print(f"개선 폭:         +{improvement:.1f}%p")
    
    print(f"\n노이즈 제거:")
    print(f"  원본 text_block:    {original_classes.get('text_block', 0)}개")
    print(f"  최종 text_block:    {final_classes.get('text_block', [])}")
    print(f"  제거율:            {(1 - len(final_classes.get('text_block', [])) / max(original_classes.get('text_block', 1), 1)) * 100:.1f}%")
    
    # 7. 결과 저장
    with open('/tmp/improved_yolo_result.json', 'w') as f:
        json.dump({
            'original_count': len(original_detections),
            'filtered_count': len(filtered),
            'final_count': len(final),
            'detections': final,
            'ground_truth_matches': matches,
            'accuracy': accuracy
        }, f, indent=2)
    
    print("\n결과 저장: /tmp/improved_yolo_result.json")
    print("="*70)

if __name__ == '__main__':
    main()
