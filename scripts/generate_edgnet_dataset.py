#!/usr/bin/env python3
"""
EDGNet 데이터셋 자동 생성 스크립트
YOLO + eDOCr2 결과를 활용하여 그래프 학습 데이터 생성
"""

import os
import json
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# 설정
YOLO_API_URL = "http://localhost:5005/api/v1/detect"
EDOCR2_API_URL = "http://localhost:5001/api/v1/ocr"
TEST_DRAWINGS_DIR = Path("/home/uproot/ax/poc/test_samples/drawings")
OUTPUT_DIR = Path("/home/uproot/ax/poc/edgnet_dataset")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def process_drawing(drawing_path: Path, client: httpx.AsyncClient) -> Dict[str, Any]:
    """단일 도면 처리"""
    print(f"\n📄 Processing: {drawing_path.name}")
    
    result = {
        'filename': drawing_path.name,
        'yolo_detections': [],
        'edocr2_results': {},
        'graph_nodes': [],
        'graph_edges': []
    }
    
    # 1. YOLO 검출
    try:
        with open(drawing_path, 'rb') as f:
            files = {'file': (drawing_path.name, f, 'application/octet-stream')}
            data = {'confidence': '0.25', 'save_visualization': 'false'}
            
            response = await client.post(YOLO_API_URL, files=files, data=data, timeout=60.0)
            
            if response.status_code == 200:
                yolo_result = response.json()
                detections = yolo_result.get('detections', [])
                result['yolo_detections'] = detections
                print(f"  ✅ YOLO: {len(detections)} objects detected")
            else:
                print(f"  ⚠️  YOLO failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ YOLO error: {e}")
    
    # 2. eDOCr2 OCR (JPG만)
    if drawing_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            with open(drawing_path, 'rb') as f:
                files = {'file': (drawing_path.name, f, 'image/jpeg')}
                data = {
                    'extract_dimensions': 'true',
                    'extract_gdt': 'true',
                    'extract_text': 'true'
                }
                
                response = await client.post(EDOCR2_API_URL, files=files, data=data, timeout=120.0)
                
                if response.status_code == 200:
                    edocr2_result = response.json()
                    result['edocr2_results'] = edocr2_result.get('data', {})
                    dims = result['edocr2_results'].get('dimensions', [])
                    gdts = result['edocr2_results'].get('gdt', [])
                    print(f"  ✅ eDOCr2: {len(dims)} dimensions, {len(gdts)} GD&T")
                else:
                    print(f"  ⚠️  eDOCr2 failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ eDOCr2 error: {e}")
    
    # 3. 그래프 노드 생성 (YOLO bbox → graph nodes)
    for i, detection in enumerate(result['yolo_detections']):
        bbox = detection['bbox']
        node = {
            'id': i,
            'class_id': detection['class_id'],
            'class_name': detection['class_name'],
            'confidence': detection['confidence'],
            'bbox': bbox,
            'center': [
                bbox['x'] + bbox['width'] / 2,
                bbox['y'] + bbox['height'] / 2
            ],
            'area': bbox['width'] * bbox['height']
        }
        result['graph_nodes'].append(node)
    
    # 4. 그래프 엣지 생성 (공간적 인접성 기반)
    nodes = result['graph_nodes']
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            # 두 노드 간 거리 계산
            dist = np.linalg.norm(
                np.array(nodes[i]['center']) - np.array(nodes[j]['center'])
            )
            
            # 거리 임계값 내에 있으면 엣지 생성
            if dist < 200:  # 200 픽셀 이내
                edge = {
                    'source': i,
                    'target': j,
                    'distance': float(dist),
                    'weight': 1.0 / (dist + 1)  # 거리 반비례 가중치
                }
                result['graph_edges'].append(edge)
    
    print(f"  📊 Graph: {len(result['graph_nodes'])} nodes, {len(result['graph_edges'])} edges")
    
    return result

async def generate_dataset():
    """전체 데이터셋 생성"""
    print("🚀 Starting EDGNet Dataset Generation")
    print(f"📂 Input: {TEST_DRAWINGS_DIR}")
    print(f"💾 Output: {OUTPUT_DIR}")
    
    # 도면 파일 찾기
    drawing_files = []
    for ext in ['.jpg', '.jpeg', '.png']:  # PDF는 일단 제외 (이미지 변환 필요)
        drawing_files.extend(TEST_DRAWINGS_DIR.glob(f'*{ext}'))
    
    print(f"\n📋 Found {len(drawing_files)} drawings")
    
    # 비동기 처리
    async with httpx.AsyncClient() as client:
        results = []
        for drawing_file in drawing_files:
            result = await process_drawing(drawing_file, client)
            results.append(result)
            
            # 개별 결과 저장
            output_file = OUTPUT_DIR / f"{drawing_file.stem}.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
    
    # 통계 계산
    total_nodes = sum(len(r['graph_nodes']) for r in results)
    total_edges = sum(len(r['graph_edges']) for r in results)
    total_detections = sum(len(r['yolo_detections']) for r in results)
    
    # 메타데이터 저장
    metadata = {
        'num_drawings': len(results),
        'total_nodes': total_nodes,
        'total_edges': total_edges,
        'total_detections': total_detections,
        'avg_nodes_per_drawing': total_nodes / len(results) if results else 0,
        'avg_edges_per_drawing': total_edges / len(results) if results else 0,
        'class_distribution': {}
    }
    
    # 클래스 분포 계산
    for result in results:
        for node in result['graph_nodes']:
            class_name = node['class_name']
            metadata['class_distribution'][class_name] = \
                metadata['class_distribution'].get(class_name, 0) + 1
    
    with open(OUTPUT_DIR / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Dataset Generation Complete!")
    print("="*60)
    print(f"📊 Statistics:")
    print(f"  - Drawings processed: {metadata['num_drawings']}")
    print(f"  - Total nodes: {metadata['total_nodes']}")
    print(f"  - Total edges: {metadata['total_edges']}")
    print(f"  - Avg nodes/drawing: {metadata['avg_nodes_per_drawing']:.1f}")
    print(f"  - Avg edges/drawing: {metadata['avg_edges_per_drawing']:.1f}")
    print(f"\n📁 Class Distribution:")
    for class_name, count in sorted(metadata['class_distribution'].items(), 
                                    key=lambda x: x[1], reverse=True):
        print(f"  - {class_name}: {count}")
    print(f"\n💾 Output saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(generate_dataset())
