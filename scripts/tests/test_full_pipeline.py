#!/usr/bin/env python3
"""
전체 시스템 파이프라인 통합 테스트

1. YOLO API: 도면에서 치수/GD&T 객체 감지
2. eDOCr2 API: OCR로 텍스트 추출
3. PaddleOCR API: 대체 OCR
4. EDGNet API: 엣지 검출
5. 결과 통합 및 분석
"""

import requests
import json
from pathlib import Path
import time
from datetime import datetime

# API 엔드포인트 (Docker 포트 매핑에 맞춤)
GATEWAY_URL = "http://localhost:8000"
YOLO_URL = "http://localhost:5005"
EDOCR_V1_URL = "http://localhost:5001"
EDOCR_V2_URL = "http://localhost:5002"
PADDLE_URL = "http://localhost:5006"
EDGNET_URL = "http://localhost:5012"

def test_api_health():
    """모든 API 헬스 체크"""
    apis = {
        'Gateway': f"{GATEWAY_URL}/health",
        'YOLO': f"{YOLO_URL}/api/v1/health",
        'eDOCr2 v1': f"{EDOCR_V1_URL}/api/v1/health",
        'eDOCr2 v2': f"{EDOCR_V2_URL}/api/v2/health",
        'PaddleOCR': f"{PADDLE_URL}/api/v1/health",
        'EDGNet': f"{EDGNET_URL}/api/v1/health"
    }

    print("="*60)
    print("API 헬스 체크")
    print("="*60)

    all_healthy = True
    for name, url in apis.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name:15s} - OK")
            else:
                print(f"❌ {name:15s} - HTTP {response.status_code}")
                all_healthy = False
        except Exception as e:
            print(f"❌ {name:15s} - {e}")
            all_healthy = False

    print("="*60)
    return all_healthy

def test_yolo(image_path):
    """YOLO API 테스트"""
    print(f"\n1️⃣  YOLO 객체 감지 테스트")
    print("-" * 60)

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(f"{YOLO_URL}/api/v1/detect", files=files, timeout=60)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            detections = result.get('detections', [])
            print(f"✅ 성공: {elapsed:.2f}s")
            print(f"   감지된 객체: {len(detections)}개")

            # 클래스별 카운트
            class_counts = {}
            for det in detections:
                cls = det.get('class', 'unknown')
                class_counts[cls] = class_counts.get(cls, 0) + 1

            if class_counts:
                print(f"   클래스별 분포:")
                for cls, count in sorted(class_counts.items(), key=lambda x: -x[1])[:5]:
                    print(f"     - {cls}: {count}개")

            return {'success': True, 'elapsed': elapsed, 'detections': len(detections), 'result': result}
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            return {'success': False, 'error': response.text}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False, 'error': str(e)}

def test_ocr(api_name, api_url, image_path):
    """OCR API 테스트"""
    print(f"\n{api_name} 테스트")
    print("-" * 60)

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(f"{api_url}/ocr", files=files, timeout=120)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()

            # 텍스트 수 카운트
            text_count = 0
            if 'texts' in result:
                text_count = len(result['texts'])
            elif 'result' in result:
                text_count = len(result['result'])

            print(f"✅ 성공: {elapsed:.2f}s")
            print(f"   감지된 텍스트: {text_count}개")

            return {'success': True, 'elapsed': elapsed, 'text_count': text_count, 'result': result}
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            return {'success': False, 'error': response.text[:200]}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False, 'error': str(e)}

def test_edgnet(image_path):
    """EDGNet API 테스트"""
    print(f"\n5️⃣  EDGNet 세그먼트 검출 테스트")
    print("-" * 60)

    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(f"{EDGNET_URL}/api/v1/segment", files=files, timeout=60)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공: {elapsed:.2f}s")

            if 'edge_map' in result:
                print(f"   엣지 맵 생성 완료")

            return {'success': True, 'elapsed': elapsed, 'result': result}
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            return {'success': False, 'error': response.text[:200]}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False, 'error': str(e)}

def run_full_pipeline(image_path):
    """전체 파이프라인 실행"""
    print("\n" + "="*60)
    print(f"전체 파이프라인 테스트: {image_path.name}")
    print("="*60)

    results = {}

    # 1. YOLO
    results['yolo'] = test_yolo(image_path)

    # 2. eDOCr2 v1
    results['edocr_v1'] = test_ocr("2️⃣  eDOCr2 v1", EDOCR_V1_URL + "/api/v1", image_path)

    # 3. eDOCr2 v2
    results['edocr_v2'] = test_ocr("3️⃣  eDOCr2 v2", EDOCR_V2_URL + "/api/v2", image_path)

    # 4. PaddleOCR
    results['paddleocr'] = test_ocr("4️⃣  PaddleOCR", PADDLE_URL + "/api/v1", image_path)

    # 5. EDGNet
    results['edgnet'] = test_edgnet(image_path)

    return results

def print_summary(all_results):
    """전체 결과 요약"""
    print("\n" + "="*60)
    print("전체 테스트 결과 요약")
    print("="*60)

    for img_name, results in all_results.items():
        print(f"\n📄 {img_name}")
        print("-" * 60)

        for api, result in results.items():
            if result.get('success'):
                elapsed = result.get('elapsed', 0)
                if api == 'yolo':
                    dets = result.get('detections', 0)
                    print(f"  ✅ {api:12s}: {elapsed:5.2f}s - {dets}개 객체")
                elif api in ['edocr_v1', 'edocr_v2', 'paddleocr']:
                    texts = result.get('text_count', 0)
                    print(f"  ✅ {api:12s}: {elapsed:5.2f}s - {texts}개 텍스트")
                else:
                    print(f"  ✅ {api:12s}: {elapsed:5.2f}s")
            else:
                error = result.get('error', 'Unknown error')[:50]
                print(f"  ❌ {api:12s}: {error}")

    print("\n" + "="*60)

def main():
    # 테스트 이미지 선택
    test_images = [
        Path("/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg"),
        Path("/home/uproot/ax/poc/test_samples/drawings/A12-311197-9 Rev.2 Interm Shaft-Acc_y_1.jpg")
    ]

    # 존재하는 이미지만 필터링
    test_images = [img for img in test_images if img.exists()]

    if not test_images:
        print("❌ 테스트 이미지를 찾을 수 없습니다!")
        return

    print("="*60)
    print("전체 시스템 통합 테스트")
    print("="*60)
    print(f"테스트 이미지 수: {len(test_images)}")
    print("="*60)

    # 헬스 체크
    if not test_api_health():
        print("\n⚠️  일부 API가 응답하지 않습니다. 계속 진행합니다...")

    # 각 이미지에 대해 테스트
    all_results = {}
    for img_path in test_images:
        results = run_full_pipeline(img_path)
        all_results[img_path.name] = results

    # 결과 요약
    print_summary(all_results)

    # 결과 저장
    output_path = Path("/home/uproot/ax/poc/full_pipeline_test_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        # 복잡한 객체는 제외하고 저장
        save_results = {}
        for img_name, results in all_results.items():
            save_results[img_name] = {}
            for api, result in results.items():
                save_results[img_name][api] = {
                    'success': result.get('success', False),
                    'elapsed': result.get('elapsed', 0),
                    'detections': result.get('detections', 0) if api == 'yolo' else None,
                    'text_count': result.get('text_count', 0) if 'ocr' in api or 'paddle' in api else None,
                    'error': result.get('error', None) if not result.get('success') else None
                }

        json.dump(save_results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 결과 저장: {output_path}")
    print("\n✅ 전체 테스트 완료!")

if __name__ == '__main__':
    main()
