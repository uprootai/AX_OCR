#!/usr/bin/env python3
"""
P&ID 심볼 이미지로 OCR API 테스트
3가지 OCR API 성능 비교
"""

import requests
import json
from pathlib import Path
import random
import time
from PIL import Image

# API 엔드포인트
APIS = {
    'eDOCr2 v1': 'http://localhost:5001/api/v1/ocr',
    'eDOCr2 v2': 'http://localhost:5002/api/v2/ocr',
    'PaddleOCR': 'http://localhost:5003/api/v1/ocr'
}

def select_sample_images(dataset_path, num_samples=10):
    """테스트용 샘플 이미지 선택"""
    images_dir = dataset_path / 'images' / 'test'
    all_images = list(images_dir.glob("*.png"))

    if len(all_images) < num_samples:
        num_samples = len(all_images)

    # 랜덤 샘플 선택
    samples = random.sample(all_images, num_samples)

    print(f"✅ {num_samples}개 샘플 이미지 선택")
    return samples

def test_ocr_api(api_name, api_url, image_path):
    """OCR API 테스트"""
    try:
        # 이미지 열기
        img = Image.open(image_path)

        # API 요청
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/png')}
            start_time = time.time()
            response = requests.post(api_url, files=files, timeout=30)
            elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'elapsed': elapsed,
                'result': result
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}",
                'elapsed': elapsed
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'elapsed': 0
        }

def extract_text_from_result(result):
    """OCR 결과에서 텍스트 추출"""
    if not result or not isinstance(result, dict):
        return []

    texts = []

    # eDOCr2 형식
    if 'texts' in result:
        texts = result['texts']
    # PaddleOCR 형식
    elif 'result' in result and isinstance(result['result'], list):
        for item in result['result']:
            if isinstance(item, list) and len(item) > 0:
                if isinstance(item[0], list):
                    # [[box], (text, conf)]
                    if len(item) > 1 and isinstance(item[1], (list, tuple)):
                        texts.append(item[1][0])
                else:
                    texts.append(str(item))

    return texts

def run_tests(samples):
    """모든 샘플에 대해 OCR 테스트 실행"""
    results = {api_name: [] for api_name in APIS.keys()}

    print("\n" + "="*60)
    print("OCR API 테스트 시작")
    print("="*60)

    for idx, img_path in enumerate(samples, 1):
        print(f"\n[{idx}/{len(samples)}] {img_path.name}")
        print("-" * 60)

        for api_name, api_url in APIS.items():
            print(f"  {api_name}...", end=" ", flush=True)

            result = test_ocr_api(api_name, api_url, img_path)

            if result['success']:
                texts = extract_text_from_result(result['result'])
                text_count = len(texts)
                print(f"✅ {result['elapsed']:.2f}s - {text_count}개 텍스트 감지")

                if texts:
                    print(f"     → {', '.join(texts[:3])}" + ("..." if len(texts) > 3 else ""))

                results[api_name].append({
                    'image': img_path.name,
                    'success': True,
                    'elapsed': result['elapsed'],
                    'text_count': text_count,
                    'texts': texts
                })
            else:
                print(f"❌ {result['error']}")
                results[api_name].append({
                    'image': img_path.name,
                    'success': False,
                    'error': result['error']
                })

    return results

def print_summary(results):
    """결과 요약 출력"""
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    for api_name, api_results in results.items():
        total = len(api_results)
        successful = sum(1 for r in api_results if r.get('success', False))
        failed = total - successful

        if successful > 0:
            avg_time = sum(r['elapsed'] for r in api_results if r.get('success', False)) / successful
            total_texts = sum(r.get('text_count', 0) for r in api_results if r.get('success', False))
        else:
            avg_time = 0
            total_texts = 0

        print(f"\n{api_name}:")
        print(f"  성공: {successful}/{total}")
        print(f"  실패: {failed}/{total}")
        print(f"  평균 처리 시간: {avg_time:.2f}s")
        print(f"  총 감지 텍스트: {total_texts}개")

    print("\n" + "="*60)

def save_results(results, output_path):
    """결과를 JSON 파일로 저장"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 결과 저장: {output_path}")

def main():
    dataset_path = Path('/home/uproot/ax/poc/datasets/pid_symbols')
    output_path = Path('/home/uproot/ax/poc/pid_ocr_test_results.json')

    print("="*60)
    print("P&ID 심볼 OCR 테스트")
    print("="*60)

    # 샘플 선택
    samples = select_sample_images(dataset_path, num_samples=10)

    # 테스트 실행
    results = run_tests(samples)

    # 결과 요약
    print_summary(results)

    # 결과 저장
    save_results(results, output_path)

    print("\n✅ 모든 테스트 완료!")

if __name__ == '__main__':
    main()
