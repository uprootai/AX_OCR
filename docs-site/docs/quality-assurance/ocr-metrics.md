---
sidebar_position: 4
title: OCR 메트릭
description: OCR 성능 측정 메트릭
---

# OCR 메트릭 (OCR Metrics)

## 핵심 메트릭 (Key Metrics)

| 메트릭 | 설명 | 공식 |
|--------|------|------|
| **CER** | 문자 오류율 (Character Error Rate) | `(S + D + I) / N` |
| **WER** | 단어 오류율 (Word Error Rate) | `(Sw + Dw + Iw) / Nw` |
| **치수 정확도** (Dimension Accuracy) | 치수 파싱 정확도 | `correct_dims / total_dims` |

### CER / WER 계산

CER은 문자 레벨에서 편집 거리(Levenshtein distance)를 기반으로 계산됩니다:

```
CER = (Substitutions + Deletions + Insertions) / Total Reference Characters
```

**예시**: 참조값 `Ø45.2` vs OCR 출력 `045.2`

| 연산 | 횟수 | 상세 |
|------|------|------|
| 대체 (Substitution) | 1 | `Ø` → `0` |
| 삭제 (Deletion) | 0 | - |
| 삽입 (Insertion) | 0 | - |
| **CER** | **1/5 = 20%** | |

WER은 동일한 원리를 단어 단위로 적용합니다:

```
WER = (Word Substitutions + Word Deletions + Word Insertions) / Total Reference Words
```

## 오류 카테고리 (Error Categories)

| 카테고리 | 유형 | 설명 | 예시 |
|----------|------|------|------|
| **대체** (Substitution) | 문자 | 다른 문자로 대체 | `Ø` → `0`, `±` → `+` |
| **삭제** (Deletion) | 문자 | 문자 누락 | `45.2` → `45.` |
| **삽입** (Insertion) | 문자 | 불필요한 문자 삽입 | `M20` → `M20.` |
| **심볼 오류** (Symbol error) | 의미 | 특수 심볼 오인식 | `Ø` → `0`, `∅` → `O` |
| **소수점 오류** (Decimal error) | 의미 | 소수점 오류 | `45.2` → `452` |
| **단위 혼동** (Unit confusion) | 의미 | 단위 혼동 | `mm` → `in` |
| **공차 누락** (Tolerance miss) | 의미 | 공차 미인식 | `±0.05` 누락 |

## 엔진 비교 (Engine Comparison)

| 엔진 | CER | WER | 속도 | GPU | 적합 용도 |
|------|-----|-----|------|-----|----------|
| **eDOCr2** | ~3% | ~5% | 보통 | 필요 | 한국어 치수 |
| **PaddleOCR** | ~4% | ~7% | 빠름 | 불필요 | 다국어 범용 |
| **Tesseract** | ~6% | ~10% | 빠름 | 불필요 | 문서 텍스트 |
| **TrOCR** | ~5% | ~8% | 느림 | 필요 | 필기체 |
| **OCR Ensemble** | ~2% | ~4% | 가장 느림 | 필요 | 최고 정확도 |
| **Surya OCR** | ~4% | ~7% | 보통 | 불필요 | 레이아웃 분석 |
| **DocTR** | ~4% | ~6% | 보통 | 불필요 | 문서 구조 |
| **EasyOCR** | ~5% | ~8% | 보통 | 불필요 | CPU 환경 |

### 앙상블 투표 메커니즘 (Ensemble Voting Mechanism)

OCR 앙상블(Ensemble)은 가중 투표(Weighted Voting)로 다중 엔진 결과를 병합합니다:

```python
# 1. 텍스트 유사도로 클러스터링 (Jaccard similarity >= 0.7)
# 2. 클러스터 내 가중 투표: vote = weight * confidence
# 3. 합의 보너스: +0.05 per agreeing engine (max 0.2)
# 4. 최종 confidence = weighted_avg_confidence + agreement_bonus
```

## 치수 파싱 정확도 (Dimension Parsing Accuracy)

치수 파싱은 OCR 결과에서 수치, 단위, 공차, 타입을 추출합니다.

```mermaid
flowchart LR
    RAW["OCR 텍스트\n'Ø45.2 ±0.05'"] --> FIX["심볼 보정\n(0→Ø 변환)"]
    FIX --> FILTER["패턴 필터\n(20+ 정규식)"]
    FILTER --> PARSE["타입 파서"]
    PARSE --> VAL["값: 45.2"]
    PARSE --> TYPE["타입: DIAMETER"]
    PARSE --> TOL["공차: ±0.05"]
    PARSE --> UNIT["단위: mm"]
```

### 치수 타입 (Dimension Types)

`parse_dimension_text()` 가 인식하는 치수 타입:

| 치수 타입 (DimensionType) | 패턴 | 예시 |
|--------------------------|------|------|
| `DIAMETER` | `Ø\d+` | `Ø45.2` |
| `RADIUS` | `R\d+` | `R12.5` |
| `THREAD` | `M\d+` | `M20×1.5` |
| `ANGLE` | `\d+°` | `45°` |
| `CHAMFER` | `C\d+` | `C2×45°` |
| `SURFACE_FINISH` | `Ra\d+` 또는 ISO 4287 | `Ra3.2` |
| `LENGTH` | `\d+` (기본값) | `125.0` |

### 품질 필터 (Quality Filters)

`is_valid_dimension()` 은 OCR 오탐을 제거하는 6단계 필터를 적용합니다:

1. 텍스트 길이 `> 1` and 숫자 포함
2. 불필요 문자 비율 `< 30%` (`:;|{}[]\\`)
3. 줄바꿈 없음, 텍스트 길이 `<= 30`
4. 숫자 비율 `>= 30%`
5. BBox 너비 `<= 500px`
6. 수치 값 `< 5000` (비현실적 치수 제외)

## 개선 추적 (Improvement Tracking)

```mermaid
flowchart TD
    V1["v1.0: 52% 정확도"] --> FIX1["7개 오류 카테고리 수정"]
    FIX1 --> V2["v1.1: 85% 정확도"]
    V2 --> ENS["앙상블 투표"]
    ENS --> V3["v1.2: 92% 정확도"]
    V3 --> AL["능동 학습"]
    AL --> V4["v2.0: 95%+ 목표"]
```
