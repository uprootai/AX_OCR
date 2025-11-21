#!/usr/bin/env python3
"""
BlueprintFlow 워크플로우 시나리오 자동 테스트
"""
import base64
import json
import requests
import time
from pathlib import Path

# 테스트 이미지
TEST_IMAGE = "/home/uproot/ax/poc/samples/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg"
API_URL = "http://localhost:8000/api/v1/workflow/execute-stream"

def load_image_as_base64(image_path: str) -> str:
    """이미지를 Data URL 형식으로 로드"""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    b64 = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

def test_scenario(name: str, workflow_def: dict, image_data: str):
    """워크플로우 시나리오 테스트"""
    print(f"\n{'='*60}")
    print(f"🧪 테스트: {name}")
    print(f"{'='*60}")

    payload = {
        "workflow": workflow_def,
        "inputs": {"image": image_data},
        "config": {}
    }

    try:
        response = requests.post(API_URL, json=payload, stream=True, timeout=60)

        if response.status_code != 200:
            print(f"❌ HTTP 에러: {response.status_code}")
            print(response.text)
            return False

        # SSE 이벤트 읽기
        events = []
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    events.append(data)

                    # 이벤트 출력
                    event_type = data.get('type', 'unknown')
                    if event_type == 'workflow_start':
                        print(f"▶️  워크플로우 시작: {data.get('workflow_name')}")
                    elif event_type == 'node_start':
                        print(f"   🔵 노드 시작: {data.get('node_id')}")
                    elif event_type == 'node_complete':
                        status = data.get('status', 'unknown')
                        icon = '✅' if status == 'completed' else '❌'
                        print(f"   {icon} 노드 완료: {data.get('node_id')} - {status}")
                    elif event_type == 'node_error':
                        print(f"   ❌ 노드 실패: {data.get('node_id')} - {data.get('error')}")
                    elif event_type == 'workflow_complete':
                        status = data.get('status')
                        time_ms = data.get('execution_time_ms', 0)
                        icon = '✅' if status == 'completed' else '❌'
                        print(f"{icon} 워크플로우 완료: {status} ({time_ms:.0f}ms)")

                        # 최종 결과
                        if status == 'completed':
                            return True
                        else:
                            return False

        return False

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        return False

def main():
    print("🚀 BlueprintFlow 자동 테스트 시작")
    print(f"📁 테스트 이미지: {TEST_IMAGE}")

    if not Path(TEST_IMAGE).exists():
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {TEST_IMAGE}")
        return

    # 이미지 로드
    print("\n📷 이미지 로딩 중...")
    image_data = load_image_as_base64(TEST_IMAGE)
    print(f"✅ 이미지 로드 완료 (크기: {len(image_data)} chars)")

    results = {}

    # 시나리오 1: ImageInput → YOLO
    scenario1 = {
        "id": "test-1",
        "name": "Scenario 1: ImageInput → YOLO",
        "nodes": [
            {"id": "node_0", "type": "imageinput", "position": {"x": 0, "y": 0}, "parameters": {}},
            {"id": "node_1", "type": "yolo", "position": {"x": 200, "y": 0}, "parameters": {
                "confidence": 0.5,
                "iou": 0.5,
                "imgsz": 640,
                "visualize": False
            }}
        ],
        "edges": [
            {"id": "e0-1", "source": "node_0", "target": "node_1"}
        ]
    }
    results['Scenario 1'] = test_scenario("ImageInput → YOLO", scenario1, image_data)
    time.sleep(2)

    # 시나리오 2: ImageInput → EDGNet
    scenario2 = {
        "id": "test-2",
        "name": "Scenario 2: ImageInput → EDGNet",
        "nodes": [
            {"id": "node_0", "type": "imageinput", "position": {"x": 0, "y": 0}, "parameters": {}},
            {"id": "node_1", "type": "edgnet", "position": {"x": 200, "y": 0}, "parameters": {
                "visualize": False,
                "num_classes": 2,
                "save_graph": False
            }}
        ],
        "edges": [
            {"id": "e0-1", "source": "node_0", "target": "node_1"}
        ]
    }
    results['Scenario 2'] = test_scenario("ImageInput → EDGNet", scenario2, image_data)
    time.sleep(2)

    # 시나리오 3: ImageInput → PaddleOCR
    scenario3 = {
        "id": "test-3",
        "name": "Scenario 3: ImageInput → PaddleOCR",
        "nodes": [
            {"id": "node_0", "type": "imageinput", "position": {"x": 0, "y": 0}, "parameters": {}},
            {"id": "node_1", "type": "paddleocr", "position": {"x": 200, "y": 0}, "parameters": {
                "lang": "korean",
                "min_confidence": 0.5
            }}
        ],
        "edges": [
            {"id": "e0-1", "source": "node_0", "target": "node_1"}
        ]
    }
    results['Scenario 3'] = test_scenario("ImageInput → PaddleOCR", scenario3, image_data)
    time.sleep(2)

    # 시나리오 4: ImageInput → eDOCr2
    scenario4 = {
        "id": "test-4",
        "name": "Scenario 4: ImageInput → eDOCr2",
        "nodes": [
            {"id": "node_0", "type": "imageinput", "position": {"x": 0, "y": 0}, "parameters": {}},
            {"id": "node_1", "type": "edocr2", "position": {"x": 200, "y": 0}, "parameters": {
                "batch_size": 1,
                "visualize": False
            }}
        ],
        "edges": [
            {"id": "e0-1", "source": "node_0", "target": "node_1"}
        ]
    }
    results['Scenario 4'] = test_scenario("ImageInput → eDOCr2", scenario4, image_data)

    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)

    for name, success in results.items():
        icon = "✅" if success else "❌"
        status = "성공" if success else "실패"
        print(f"{icon} {name}: {status}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n🎯 총 {total}개 중 {passed}개 성공 ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 모든 테스트 통과!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")

if __name__ == "__main__":
    main()
