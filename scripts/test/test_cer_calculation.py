#!/usr/bin/env python3
"""
CER (Character Error Rate) 계산 스크립트

Multimodal LLM으로서 도면 이미지를 분석하고,
OCR 결과와 비교하여 실제 정확도를 측정
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path
import re

# Ground Truth: 도면에서 실제로 보이는 치수 및 텍스트
GROUND_TRUTH_SAMPLE1 = {
    'filename': 'S60ME-C INTERM-SHAFT_대 주조전.jpg',
    'dimensions': [
        {'text': 'φ476', 'type': 'diameter', 'value': 476.0},
        {'text': 'φ370', 'type': 'diameter', 'value': 370.0},
        {'text': 'φ9.204 +0.1 -0.2', 'type': 'diameter', 'value': 9.204, 'tolerance': '+0.1/-0.2'},
        {'text': 'φ1313±2', 'type': 'diameter', 'value': 1313.0, 'tolerance': '±2'},
        {'text': '(177)', 'type': 'reference', 'value': 177.0},
        {'text': '7±0.5', 'type': 'linear', 'value': 7.0, 'tolerance': '±0.5'},
        {'text': '5mm', 'type': 'linear', 'value': 5.0},
        {'text': '1.5', 'type': 'linear', 'value': 1.5},
        {'text': '5', 'type': 'linear', 'value': 5.0},
        # 정면도 (하단 원형 뷰)에 더 많은 치수가 있지만 작아서 읽기 어려움
    ],
    'gdt': [
        {'text': 'Ra 2', 'type': 'surface_roughness', 'value': 'Ra 2'},
        {'text': 'Ra 3', 'type': 'surface_roughness', 'value': 'Ra 3'},
        {'text': '⌖', 'type': 'position_tolerance', 'symbol': '⌖'},
        {'text': '△', 'type': 'triangular_note', 'symbol': '△'},
    ],
    'text': [
        'DWG-',
        'Ref.',
        'Rev.1',
        'Rev.2',
        'Rev.3',
        'Rev.9',
        'DSE BEARING Co., LTD.',
        # 테이블 내용들
    ]
}


def normalize_text(text: str) -> str:
    """텍스트 정규화: 공백 제거, 대소문자 통일"""
    return re.sub(r'\s+', '', text.lower())


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    CER (Character Error Rate) 계산

    CER = (S + D + I) / N
    S = Substitutions (대체)
    D = Deletions (삭제)
    I = Insertions (삽입)
    N = 참조 텍스트 길이
    """
    ref = normalize_text(reference)
    hyp = normalize_text(hypothesis)

    # Levenshtein Distance 계산
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i-1] == hyp[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(
                    dp[i-1][j] + 1,    # Deletion
                    dp[i][j-1] + 1,    # Insertion
                    dp[i-1][j-1] + 1   # Substitution
                )

    edit_distance = dp[n][m]
    cer = edit_distance / n if n > 0 else 0.0

    return cer, edit_distance, n


def match_dimensions(ground_truth: List[Dict], ocr_results: List[Dict]) -> Dict:
    """
    Ground Truth와 OCR 결과를 매칭하여 정확도 계산
    """
    matched = []
    unmatched_gt = []
    false_positives = []

    gt_used = [False] * len(ground_truth)
    ocr_used = [False] * len(ocr_results)

    # 값 기반 매칭
    for i, gt in enumerate(ground_truth):
        best_match = None
        best_score = float('inf')

        for j, ocr in enumerate(ocr_results):
            if ocr_used[j]:
                continue

            # 값 차이 계산
            value_diff = abs(gt['value'] - ocr['value'])

            if value_diff < best_score and value_diff < 10:  # 10 이내 오차 허용
                best_match = j
                best_score = value_diff

        if best_match is not None:
            gt_used[i] = True
            ocr_used[best_match] = True

            gt_text = gt.get('text', str(gt['value']))
            ocr_value = ocr_results[best_match]['value']
            ocr_text = f"φ{ocr_value}" if ocr_results[best_match]['type'] == 'diameter' else str(ocr_value)

            cer, dist, length = calculate_cer(gt_text, ocr_text)

            matched.append({
                'ground_truth': gt_text,
                'ocr_result': ocr_text,
                'value_diff': best_score,
                'cer': cer,
                'edit_distance': dist,
                'correct': cer < 0.2  # 20% 이하 오차는 정확한 것으로 간주
            })

    # 매칭 안된 GT (누락)
    for i, used in enumerate(gt_used):
        if not used:
            unmatched_gt.append(ground_truth[i])

    # 매칭 안된 OCR (오검출)
    for j, used in enumerate(ocr_used):
        if not used:
            false_positives.append(ocr_results[j])

    return {
        'matched': matched,
        'unmatched_gt': unmatched_gt,
        'false_positives': false_positives,
        'recall': len([m for m in matched if m['correct']]) / len(ground_truth) if ground_truth else 0,
        'precision': len([m for m in matched if m['correct']]) / len(ocr_results) if ocr_results else 0,
        'avg_cer': sum(m['cer'] for m in matched) / len(matched) if matched else 1.0
    }


def evaluate_ocr_results(json_file: str):
    """OCR 결과 JSON 파일을 읽고 CER 계산"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("="*80)
    print("OCR 성능 평가: CER (Character Error Rate) 기반")
    print("="*80)
    print()

    # 첫 번째 샘플 평가
    sample = data[0]
    print(f"샘플: {sample['sample']}")
    print(f"Ground Truth: {len(GROUND_TRUTH_SAMPLE1['dimensions'])}개 치수")
    print("-"*80)
    print()

    results_summary = []

    for test in sample['tests']:
        if not test['success']:
            continue

        method = test['method']
        ocr_dims = test.get('dimensions', [])

        if not ocr_dims:
            continue

        print(f"\n{'='*80}")
        print(f"방법: {method}")
        print(f"{'='*80}")

        # 치수 매칭 및 평가
        match_result = match_dimensions(GROUND_TRUTH_SAMPLE1['dimensions'], ocr_dims)

        print(f"\n📊 통계:")
        print(f"  - Ground Truth: {len(GROUND_TRUTH_SAMPLE1['dimensions'])}개")
        print(f"  - OCR 인식: {len(ocr_dims)}개")
        print(f"  - 정확 매칭: {len([m for m in match_result['matched'] if m['correct']])}개")
        print(f"  - 오차 있는 매칭: {len([m for m in match_result['matched'] if not m['correct']])}개")
        print(f"  - 누락 (False Negative): {len(match_result['unmatched_gt'])}개")
        print(f"  - 오검출 (False Positive): {len(match_result['false_positives'])}개")

        print(f"\n📈 성능 지표:")
        print(f"  - Recall (재현율): {match_result['recall']*100:.1f}%")
        print(f"  - Precision (정밀도): {match_result['precision']*100:.1f}%")
        print(f"  - 평균 CER: {match_result['avg_cer']*100:.1f}%")
        print(f"  - F1 Score: {2*match_result['recall']*match_result['precision']/(match_result['recall']+match_result['precision'])*100:.1f}%" if (match_result['recall']+match_result['precision']) > 0 else "  - F1 Score: 0.0%")

        # 상세 매칭 결과
        print(f"\n📝 상세 매칭 결과:")
        for i, match in enumerate(match_result['matched'][:10], 1):  # 처음 10개만
            status = "✅" if match['correct'] else "⚠️"
            print(f"  {status} {i}. GT: '{match['ground_truth']}' → OCR: '{match['ocr_result']}' "
                  f"(CER: {match['cer']*100:.1f}%, 값 차이: {match['value_diff']:.2f})")

        if len(match_result['matched']) > 10:
            print(f"  ... 외 {len(match_result['matched'])-10}개")

        # 누락된 것들
        if match_result['unmatched_gt']:
            print(f"\n❌ 누락된 치수 ({len(match_result['unmatched_gt'])}개):")
            for miss in match_result['unmatched_gt'][:5]:
                print(f"  - {miss.get('text', miss['value'])}")

        # 요약 저장
        results_summary.append({
            'method': method,
            'recall': match_result['recall'],
            'precision': match_result['precision'],
            'avg_cer': match_result['avg_cer'],
            'f1': 2*match_result['recall']*match_result['precision']/(match_result['recall']+match_result['precision']) if (match_result['recall']+match_result['precision']) > 0 else 0
        })

    # 최종 비교
    print(f"\n\n{'='*80}")
    print("최종 비교 (CER 기반)")
    print(f"{'='*80}\n")

    print(f"{'방법':<30} | {'Recall':<10} | {'Precision':<10} | {'Avg CER':<10} | {'F1 Score':<10}")
    print("-"*80)

    for result in sorted(results_summary, key=lambda x: x['f1'], reverse=True):
        print(f"{result['method']:<30} | "
              f"{result['recall']*100:>8.1f}% | "
              f"{result['precision']*100:>8.1f}% | "
              f"{result['avg_cer']*100:>8.1f}% | "
              f"{result['f1']*100:>8.1f}%")

    # 최적 모델 선정
    if results_summary:
        best = max(results_summary, key=lambda x: x['f1'])
        print(f"\n🏆 최적 모델 (F1 기준): {best['method']}")
        print(f"   - F1 Score: {best['f1']*100:.1f}%")
        print(f"   - Recall: {best['recall']*100:.1f}%")
        print(f"   - Precision: {best['precision']*100:.1f}%")
        print(f"   - Avg CER: {best['avg_cer']*100:.1f}%")


if __name__ == '__main__':
    json_file = 'ocr_performance_comparison_20251031_195252.json'
    evaluate_ocr_results(json_file)
