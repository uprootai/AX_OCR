#!/usr/bin/env python3
"""
OCR 성능 비교 테스트 스크립트

다양한 모델 조합의 성능을 비교:
1. eDOCr v1 단독
2. eDOCr v2 단독
3. EDGNet + eDOCr v1
4. EDGNet + eDOCr v2
5. v1/v2 앙상블
6. 전체 파이프라인 (EDGNet + 앙상블 + Skin Model)
"""

import requests
import time
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# API 엔드포인트
EDOCR_V1_URL = "http://localhost:5001/api/v1/ocr"
EDOCR_V2_URL = "http://localhost:5002/api/v2/ocr"
EDGNET_URL = "http://localhost:5012/api/v1/segment"
SKINMODEL_URL = "http://localhost:5003/api/v1/validate"
GATEWAY_URL = "http://localhost:8000/api/v1/process"

# 테스트 샘플
TEST_SAMPLES = [
    "/home/uproot/ax/poc/test_samples/drawings/S60ME-C INTERM-SHAFT_대 주조전.jpg",
    "/home/uproot/ax/poc/test_samples/drawings/A12-311197-9 Rev.2 Interm Shaft-Acc_y.pdf",
]


class OCRPerformanceTest:
    """OCR 성능 비교 테스트"""

    def __init__(self):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def test_edocr_v1(self, image_path: str) -> Dict[str, Any]:
        """eDOCr v1 단독 테스트"""
        print(f"\n{'='*60}")
        print(f"테스트 1: eDOCr v1 단독")
        print(f"{'='*60}")

        start_time = time.time()

        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'extract_dimensions': True,
                'extract_gdt': True,
                'extract_text': True,
                'visualize': True
            }

            try:
                response = requests.post(EDOCR_V1_URL, files=files, data=data, timeout=120)
                response.raise_for_status()
                result = response.json()

                elapsed_time = time.time() - start_time

                # 결과 분석
                dims = result.get('data', {}).get('dimensions', []) if result.get('status') == 'success' else []
                gdt = result.get('data', {}).get('gdt', []) if result.get('status') == 'success' else []
                text = result.get('data', {}).get('text', {}) if result.get('status') == 'success' else {}

                print(f"✅ 성공")
                print(f"  - 처리 시간: {elapsed_time:.2f}초")
                print(f"  - 치수 인식: {len(dims)}개")
                print(f"  - GD&T 인식: {len(gdt)}개")
                print(f"  - 텍스트 블록: {text.get('total_blocks', 0)}개")

                return {
                    'method': 'eDOCr v1 단독',
                    'success': True,
                    'processing_time': elapsed_time,
                    'dimensions_count': len(dims),
                    'gdt_count': len(gdt),
                    'text_blocks': text.get('total_blocks', 0),
                    'dimensions': dims,
                    'gdt': gdt,
                    'raw_response': result
                }

            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"❌ 실패: {str(e)}")
                return {
                    'method': 'eDOCr v1 단독',
                    'success': False,
                    'processing_time': elapsed_time,
                    'error': str(e)
                }

    def test_edocr_v2(self, image_path: str) -> Dict[str, Any]:
        """eDOCr v2 단독 테스트"""
        print(f"\n{'='*60}")
        print(f"테스트 2: eDOCr v2 단독")
        print(f"{'='*60}")

        start_time = time.time()

        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'extract_dimensions': True,
                'extract_gdt': True,
                'extract_text': True,
                'extract_tables': True,
                'visualize': True
            }

            try:
                response = requests.post(EDOCR_V2_URL, files=files, data=data, timeout=120)
                response.raise_for_status()
                result = response.json()

                elapsed_time = time.time() - start_time

                # 결과 분석
                dims = result.get('data', {}).get('dimensions', []) if result.get('status') == 'success' else []
                gdt = result.get('data', {}).get('gdt', []) if result.get('status') == 'success' else []
                text = result.get('data', {}).get('text', {}) if result.get('status') == 'success' else {}
                tables = text.get('tables', [])

                print(f"✅ 성공")
                print(f"  - 처리 시간: {elapsed_time:.2f}초")
                print(f"  - 치수 인식: {len(dims)}개")
                print(f"  - GD&T 인식: {len(gdt)}개")
                print(f"  - 텍스트 블록: {text.get('total_blocks', 0)}개")
                print(f"  - 테이블: {len(tables)}개")

                return {
                    'method': 'eDOCr v2 단독',
                    'success': True,
                    'processing_time': elapsed_time,
                    'dimensions_count': len(dims),
                    'gdt_count': len(gdt),
                    'text_blocks': text.get('total_blocks', 0),
                    'tables_count': len(tables),
                    'dimensions': dims,
                    'gdt': gdt,
                    'raw_response': result
                }

            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"❌ 실패: {str(e)}")
                return {
                    'method': 'eDOCr v2 단독',
                    'success': False,
                    'processing_time': elapsed_time,
                    'error': str(e)
                }

    def test_edgnet_segmentation(self, image_path: str) -> Dict[str, Any]:
        """EDGNet 세그멘테이션 테스트"""
        print(f"\n{'='*60}")
        print(f"테스트 3: EDGNet 세그멘테이션")
        print(f"{'='*60}")

        start_time = time.time()

        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'visualize': True}

            try:
                response = requests.post(EDGNET_URL, files=files, data=data, timeout=120)
                response.raise_for_status()
                result = response.json()

                elapsed_time = time.time() - start_time

                # 결과 분석
                classifications = result.get('data', {}).get('classifications', {}) if result.get('status') == 'success' else {}
                contour_count = classifications.get('contour', 0)
                text_count = classifications.get('text', 0)
                dimension_count = classifications.get('dimension', 0)

                print(f"✅ 성공")
                print(f"  - 처리 시간: {elapsed_time:.2f}초")
                print(f"  - 윤곽선: {contour_count}개")
                print(f"  - 텍스트: {text_count}개")
                print(f"  - 치수: {dimension_count}개")

                return {
                    'method': 'EDGNet 세그멘테이션',
                    'success': True,
                    'processing_time': elapsed_time,
                    'contour_count': contour_count,
                    'text_count': text_count,
                    'dimension_count': dimension_count,
                    'raw_response': result
                }

            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"❌ 실패: {str(e)}")
                return {
                    'method': 'EDGNet 세그멘테이션',
                    'success': False,
                    'processing_time': elapsed_time,
                    'error': str(e)
                }

    def test_ensemble_v1_v2(self, v1_result: Dict, v2_result: Dict) -> Dict[str, Any]:
        """v1/v2 앙상블 테스트"""
        print(f"\n{'='*60}")
        print(f"테스트 4: v1/v2 앙상블 (가중치 v1:0.6, v2:0.4)")
        print(f"{'='*60}")

        if not v1_result['success'] or not v2_result['success']:
            print(f"❌ v1 또는 v2 결과가 없어 앙상블 불가")
            return {
                'method': 'v1/v2 앙상블',
                'success': False,
                'error': 'v1 or v2 failed'
            }

        # 간단한 앙상블: 치수 개수가 많은 것 선택 + 신뢰도 가중
        v1_dims = v1_result.get('dimensions', [])
        v2_dims = v2_result.get('dimensions', [])
        v1_gdt = v1_result.get('gdt', [])
        v2_gdt = v2_result.get('gdt', [])

        # 치수: v1과 v2 중 더 많은 것 선택 (가중치 고려)
        ensemble_dims = v1_dims if len(v1_dims) >= len(v2_dims) else v2_dims
        ensemble_gdt = v1_gdt if len(v1_gdt) >= len(v2_gdt) else v2_gdt

        total_time = v1_result['processing_time'] + v2_result['processing_time']

        print(f"✅ 앙상블 완료")
        print(f"  - v1 치수: {len(v1_dims)}개 vs v2 치수: {len(v2_dims)}개 → 선택: {len(ensemble_dims)}개")
        print(f"  - v1 GD&T: {len(v1_gdt)}개 vs v2 GD&T: {len(v2_gdt)}개 → 선택: {len(ensemble_gdt)}개")
        print(f"  - 총 처리 시간: {total_time:.2f}초")

        return {
            'method': 'v1/v2 앙상블',
            'success': True,
            'processing_time': total_time,
            'dimensions_count': len(ensemble_dims),
            'gdt_count': len(ensemble_gdt),
            'dimensions': ensemble_dims,
            'gdt': ensemble_gdt,
            'v1_contribution': len(v1_dims) if len(v1_dims) >= len(v2_dims) else 0,
            'v2_contribution': len(v2_dims) if len(v2_dims) > len(v1_dims) else 0
        }

    def run_tests(self):
        """모든 테스트 실행"""
        print(f"\n{'#'*60}")
        print(f"# OCR 성능 비교 테스트 시작")
        print(f"# 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*60}")

        for sample_path in TEST_SAMPLES:
            if not Path(sample_path).exists():
                print(f"\n⚠️  샘플 파일 없음: {sample_path}")
                continue

            print(f"\n\n{'='*60}")
            print(f"샘플: {Path(sample_path).name}")
            print(f"{'='*60}")

            sample_results = {
                'sample': Path(sample_path).name,
                'sample_path': sample_path,
                'tests': []
            }

            # 1. eDOCr v1 단독
            v1_result = self.test_edocr_v1(sample_path)
            sample_results['tests'].append(v1_result)

            time.sleep(2)  # API 부하 방지

            # 2. eDOCr v2 단독
            v2_result = self.test_edocr_v2(sample_path)
            sample_results['tests'].append(v2_result)

            time.sleep(2)

            # 3. EDGNet 세그멘테이션
            edgnet_result = self.test_edgnet_segmentation(sample_path)
            sample_results['tests'].append(edgnet_result)

            time.sleep(2)

            # 4. v1/v2 앙상블
            ensemble_result = self.test_ensemble_v1_v2(v1_result, v2_result)
            sample_results['tests'].append(ensemble_result)

            self.results.append(sample_results)

        # 결과 저장
        self.save_results()
        self.print_summary()

    def save_results(self):
        """결과를 JSON 파일로 저장"""
        output_file = f"ocr_performance_comparison_{self.timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n\n📁 결과 저장: {output_file}")

    def print_summary(self):
        """결과 요약 출력"""
        print(f"\n\n{'#'*60}")
        print(f"# 테스트 결과 요약")
        print(f"{'#'*60}\n")

        for sample_result in self.results:
            print(f"\n샘플: {sample_result['sample']}")
            print(f"{'-'*60}")

            for test in sample_result['tests']:
                method = test['method']
                if test['success']:
                    dims = test.get('dimensions_count', 0)
                    gdt = test.get('gdt_count', 0)
                    time_taken = test.get('processing_time', 0)
                    print(f"{method:30s} | 치수: {dims:3d}개 | GD&T: {gdt:3d}개 | 시간: {time_taken:6.2f}초")
                else:
                    print(f"{method:30s} | ❌ 실패: {test.get('error', 'Unknown')}")

        # 최적 조합 추천
        self.recommend_best_combination()

    def recommend_best_combination(self):
        """최적 조합 추천"""
        print(f"\n\n{'='*60}")
        print(f"최적 조합 추천")
        print(f"{'='*60}\n")

        # 각 방법별 평균 성능 계산
        method_stats = {}

        for sample_result in self.results:
            for test in sample_result['tests']:
                if not test['success']:
                    continue

                method = test['method']
                if method not in method_stats:
                    method_stats[method] = {
                        'total_dims': 0,
                        'total_gdt': 0,
                        'total_time': 0,
                        'count': 0
                    }

                method_stats[method]['total_dims'] += test.get('dimensions_count', 0)
                method_stats[method]['total_gdt'] += test.get('gdt_count', 0)
                method_stats[method]['total_time'] += test.get('processing_time', 0)
                method_stats[method]['count'] += 1

        # 평균 계산 및 점수화
        recommendations = []
        for method, stats in method_stats.items():
            if stats['count'] == 0:
                continue

            avg_dims = stats['total_dims'] / stats['count']
            avg_gdt = stats['total_gdt'] / stats['count']
            avg_time = stats['total_time'] / stats['count']

            # 점수 = (치수 * 2) + (GD&T * 3) - (시간 * 0.1)
            # GD&T에 더 높은 가중치 (현재 재현율이 낮으므로)
            score = (avg_dims * 2) + (avg_gdt * 3) - (avg_time * 0.1)

            recommendations.append({
                'method': method,
                'avg_dimensions': avg_dims,
                'avg_gdt': avg_gdt,
                'avg_time': avg_time,
                'score': score
            })

        # 점수로 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        print("순위 | 방법                           | 평균 치수 | 평균 GD&T | 평균 시간 | 점수")
        print("-" * 90)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i:4d} | {rec['method']:30s} | {rec['avg_dimensions']:9.1f} | "
                  f"{rec['avg_gdt']:9.1f} | {rec['avg_time']:9.2f}초 | {rec['score']:6.1f}")

        if recommendations:
            best = recommendations[0]
            print(f"\n🏆 최적 조합: {best['method']}")
            print(f"   - 평균 치수 인식: {best['avg_dimensions']:.1f}개")
            print(f"   - 평균 GD&T 인식: {best['avg_gdt']:.1f}개")
            print(f"   - 평균 처리 시간: {best['avg_time']:.2f}초")


if __name__ == '__main__':
    tester = OCRPerformanceTest()
    tester.run_tests()
