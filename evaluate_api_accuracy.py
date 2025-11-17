#!/usr/bin/env python3
"""
기존 API 성능 평가 스크립트
Claude가 분석한 Ground Truth와 각 API 결과를 비교
"""

import requests
import json
from pathlib import Path
import time

# 테스트 이미지
TEST_IMAGE = "/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg"

# API 엔드포인트
YOLO_URL = "http://localhost:5005"
EDOCR_V1_URL = "http://localhost:5001"
EDOCR_V2_URL = "http://localhost:5002"
PADDLE_URL = "http://localhost:5006"
EDGNET_URL = "http://localhost:5012"

# Claude가 분석한 Ground Truth (실제 정답)
GROUND_TRUTH = {
    "부품명": "Intermediate Shaft (중간축)",
    "모델": "S60ME-C",
    "회사": "DOOSAN ENGINE CO., LTD.",

    "주요 치수": {
        "외경": "Ø476",
        "중간 직경": "Ø370",
        "내경 관련": "Ø324",
        "길이": "163+2/-1.2",
        "깊이": "7-9"
    },

    "GD&T 기호": {
        "평행도": "∥ 0.2",
        "진원도": ["Rev.1", "Rev.2", "Rev.3"],
        "기준면": ["△A", "△B"],
        "표면거칠기": ["Ra 3.2", "Ra 6.3"]
    },

    "참조 도면": [
        "18166834-2 (Rev.1)",
        "18166840 (Rev.3)",
        "12-206840 (Rev.2)",
        "A12-311197-9",
        "E30008100 (Rev.1)"
    ],

    "뷰 정보": {
        "상단": "직사각형 단면도 (해칭 포함)",
        "하단": "원형 정면도 (3개 동심원)",
        "우측 상단": "상세 단면도"
    }
}

def test_yolo():
    """YOLO API 테스트"""
    print("\n1️⃣  YOLO API 테스트")
    print("="*60)

    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': (Path(TEST_IMAGE).name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(f"{YOLO_URL}/api/v1/detect", files=files, timeout=60)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()
            detections = result.get('detections', [])

            print(f"✅ 성공 ({elapsed:.2f}s)")
            print(f"   감지된 객체: {len(detections)}개")

            # 클래스별 분류
            classes = {}
            for det in detections:
                cls = det.get('class', 'unknown')
                classes[cls] = classes.get(cls, 0) + 1

            print(f"   클래스 분포:")
            for cls, count in sorted(classes.items(), key=lambda x: -x[1]):
                print(f"     - {cls}: {count}개")

            return {
                'success': True,
                'total_objects': len(detections),
                'classes': classes
            }
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            return {'success': False}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False}

def test_ocr_api(name, url):
    """OCR API 테스트"""
    print(f"\n{name} 테스트")
    print("="*60)

    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': (Path(TEST_IMAGE).name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(url, files=files, timeout=120)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()

            # 텍스트 추출
            texts = []
            if 'texts' in result:
                texts = result['texts']
            elif 'result' in result:
                for item in result.get('result', []):
                    if isinstance(item, list) and len(item) > 1:
                        if isinstance(item[1], (list, tuple)):
                            texts.append(item[1][0])

            print(f"✅ 성공 ({elapsed:.2f}s)")
            print(f"   감지된 텍스트: {len(texts)}개")

            if texts:
                print(f"   샘플 텍스트 (처음 10개):")
                for i, text in enumerate(texts[:10], 1):
                    print(f"     {i}. {text}")

            # Ground Truth와 비교
            matched_dims = []
            matched_refs = []

            # 치수 매칭
            gt_dims = list(GROUND_TRUTH['주요 치수'].values())
            for text in texts:
                for dim in gt_dims:
                    if dim.replace('Ø', '').replace('+', '').replace('-', '').replace('/', '') in text:
                        matched_dims.append(dim)

            # 참조 도면 매칭
            for text in texts:
                for ref in GROUND_TRUTH['참조 도면']:
                    if ref.split()[0] in text:
                        matched_refs.append(ref)

            accuracy = {
                'dimensions_found': len(set(matched_dims)),
                'dimensions_total': len(gt_dims),
                'references_found': len(set(matched_refs)),
                'references_total': len(GROUND_TRUTH['참조 도면'])
            }

            print(f"\n   📊 정확도 분석:")
            print(f"     치수 인식: {accuracy['dimensions_found']}/{accuracy['dimensions_total']}")
            print(f"     참조 도면: {accuracy['references_found']}/{accuracy['references_total']}")

            return {
                'success': True,
                'text_count': len(texts),
                'texts': texts,
                'accuracy': accuracy
            }
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            print(f"   응답: {response.text[:200]}")
            return {'success': False}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False}

def test_edgnet():
    """EDGNet API 테스트"""
    print(f"\n5️⃣  EDGNet API 테스트")
    print("="*60)

    try:
        with open(TEST_IMAGE, 'rb') as f:
            files = {'file': (Path(TEST_IMAGE).name, f, 'image/jpeg')}
            start = time.time()
            response = requests.post(f"{EDGNET_URL}/api/v1/segment", files=files, timeout=120)
            elapsed = time.time() - start

        if response.status_code == 200:
            result = response.json()

            print(f"✅ 성공 ({elapsed:.2f}s)")
            print(f"   세그먼트 검출 완료")

            return {
                'success': True,
                'elapsed': elapsed
            }
        else:
            print(f"❌ 실패: HTTP {response.status_code}")
            return {'success': False}

    except Exception as e:
        print(f"❌ 오류: {e}")
        return {'success': False}

def print_ground_truth():
    """Ground Truth 출력"""
    print("\n" + "="*60)
    print("🎯 Ground Truth (Claude가 분석한 정답)")
    print("="*60)

    print(f"\n부품 정보:")
    print(f"  부품명: {GROUND_TRUTH['부품명']}")
    print(f"  모델: {GROUND_TRUTH['모델']}")
    print(f"  회사: {GROUND_TRUTH['회사']}")

    print(f"\n주요 치수:")
    for key, value in GROUND_TRUTH['주요 치수'].items():
        print(f"  {key}: {value}")

    print(f"\nGD&T 기호:")
    for key, value in GROUND_TRUTH['GD&T 기호'].items():
        if isinstance(value, list):
            print(f"  {key}: {', '.join(value)}")
        else:
            print(f"  {key}: {value}")

    print(f"\n참조 도면:")
    for ref in GROUND_TRUTH['참조 도면']:
        print(f"  - {ref}")

    print("="*60)

def main():
    print("="*60)
    print("기존 API 성능 평가 (vs Claude Ground Truth)")
    print("="*60)
    print(f"테스트 이미지: {Path(TEST_IMAGE).name}")

    # Ground Truth 표시
    print_ground_truth()

    # 각 API 테스트
    results = {}

    results['yolo'] = test_yolo()
    results['edocr_v1'] = test_ocr_api("2️⃣  eDOCr2 v1 API", f"{EDOCR_V1_URL}/api/v1/ocr")
    results['edocr_v2'] = test_ocr_api("3️⃣  eDOCr2 v2 API", f"{EDOCR_V2_URL}/api/v2/ocr")
    results['paddleocr'] = test_ocr_api("4️⃣  PaddleOCR API", f"{PADDLE_URL}/api/v1/ocr")
    results['edgnet'] = test_edgnet()

    # 최종 요약
    print("\n" + "="*60)
    print("📊 최종 평가 요약")
    print("="*60)

    for api, result in results.items():
        if result.get('success'):
            print(f"\n{api.upper()}:")
            if 'accuracy' in result:
                acc = result['accuracy']
                dim_rate = (acc['dimensions_found'] / acc['dimensions_total'] * 100) if acc['dimensions_total'] > 0 else 0
                ref_rate = (acc['references_found'] / acc['references_total'] * 100) if acc['references_total'] > 0 else 0
                print(f"  치수 인식률: {dim_rate:.1f}% ({acc['dimensions_found']}/{acc['dimensions_total']})")
                print(f"  참조 인식률: {ref_rate:.1f}% ({acc['references_found']}/{acc['references_total']})")
            elif 'total_objects' in result:
                print(f"  객체 감지: {result['total_objects']}개")
        else:
            print(f"\n{api.upper()}: ❌ 실패")

    # 결과 저장
    output_path = Path("/home/uproot/ax/poc/api_accuracy_evaluation.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        save_data = {
            'ground_truth': GROUND_TRUTH,
            'test_image': TEST_IMAGE,
            'results': results
        }
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 결과 저장: {output_path}")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
