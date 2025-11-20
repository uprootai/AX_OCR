#!/usr/bin/env python3
"""
BlueprintFlow 실제 이미지 워크플로우 테스트
YOLO → eDOCr2 파이프라인
"""
import sys
import json
import base64
import requests
from pathlib import Path


def encode_image_to_base64(image_path: str) -> str:
    """이미지를 base64로 인코딩"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def test_yolo_edocr2_workflow(image_path: str):
    """YOLO → eDOCr2 워크플로우 테스트"""

    print(f"=== BlueprintFlow 워크플로우 테스트 ===")
    print(f"이미지: {image_path}")

    # 이미지 base64 인코딩
    print("\n[1/3] 이미지 인코딩 중...")
    image_b64 = encode_image_to_base64(image_path)
    print(f"  ✓ 이미지 크기: {len(image_b64)} bytes")

    # 워크플로우 정의
    workflow_definition = {
        "workflow": {
            "name": "YOLO → eDOCr2 파이프라인",
            "description": "객체 검출 후 차원 OCR 수행",
            "version": "1.0.0",
            "nodes": [
                {
                    "id": "yolo_node",
                    "type": "yolo",
                    "label": "YOLO 객체 검출",
                    "parameters": {
                        "confidence": 0.5,
                        "iou": 0.45,
                        "visualize": True
                    }
                },
                {
                    "id": "edocr2_node",
                    "type": "edocr2",
                    "label": "eDOCr2 차원 OCR",
                    "parameters": {}
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "yolo_node",
                    "target": "edocr2_node"
                }
            ]
        },
        "inputs": {
            "image": image_b64
        }
    }

    # 워크플로우 실행
    print("\n[2/3] 워크플로우 실행 중...")
    url = "http://localhost:8000/api/v1/workflow/execute"

    response = requests.post(url, json=workflow_definition)

    if response.status_code != 200:
        print(f"  ✗ 에러: {response.status_code}")
        print(response.text)
        return

    result = response.json()

    # 결과 출력
    print("\n[3/3] 실행 결과:")
    print(f"  ✓ 실행 ID: {result['execution_id']}")
    print(f"  ✓ 상태: {result['status']}")
    print(f"  ✓ 실행 시간: {result.get('execution_time_ms', 0):.2f}ms")

    print(f"\n노드 상태:")
    for node_status in result['node_statuses']:
        status_icon = "✓" if node_status['status'] == 'completed' else "✗"
        print(f"  {status_icon} {node_status['node_id']}: {node_status['status']}")

        if node_status.get('output'):
            output = node_status['output']

            # YOLO 결과
            if node_status['node_id'] == 'yolo_node':
                total = output.get('total_detections', 0)
                print(f"     → 검출된 객체: {total}개")

            # eDOCr2 결과
            elif node_status['node_id'] == 'edocr2_node':
                total = output.get('total_dimensions', 0)
                print(f"     → 추출된 차원: {total}개")
                if total > 0:
                    dims = output.get('dimensions', [])[:3]  # 처음 3개만
                    for dim in dims:
                        print(f"        · {dim}")

    # 최종 출력
    if result.get('final_output'):
        print(f"\n최종 출력:")
        final = result['final_output'].get('edocr2_node', {})
        print(f"  차원 정보: {final.get('total_dimensions', 0)}개")

    # 결과 저장
    output_path = Path("/home/uproot/ax/poc/workflow_test_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n전체 결과 저장: {output_path}")

    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 기본 샘플 이미지
        image_path = "/home/uproot/ax/poc/samples/S60ME-C INTERM-SHAFT_대 주조전.jpg"

    if not Path(image_path).exists():
        print(f"에러: 이미지를 찾을 수 없습니다: {image_path}")
        sys.exit(1)

    test_yolo_edocr2_workflow(image_path)
