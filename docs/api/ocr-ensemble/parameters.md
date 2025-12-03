# OCR Ensemble API Parameters

> 4개 OCR 엔진 가중 투표 앙상블

## 기본 정보

| 항목 | 값 |
|------|-----|
| **Port** | 5011 |
| **Endpoint** | `/api/v1/ocr` |
| **Method** | POST |
| **Content-Type** | multipart/form-data |
| **Timeout** | 180초 |

## 앙상블 구성

| 엔진 | 기본 가중치 | 특징 |
|------|------------|------|
| eDOCr2 | 40% | 도면 특화 OCR |
| PaddleOCR | 35% | 다국어 범용 OCR |
| Tesseract | 15% | 빠른 범용 OCR |
| TrOCR | 10% | 손글씨/장면 텍스트 |

## 파라미터

### edocr2_weight
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.40` |
| **범위** | 0 ~ 1 (step: 0.05) |
| **설명** | eDOCr2 가중치 |

### paddleocr_weight
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.35` |
| **범위** | 0 ~ 1 (step: 0.05) |
| **설명** | PaddleOCR 가중치 |

### tesseract_weight
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.15` |
| **범위** | 0 ~ 1 (step: 0.05) |
| **설명** | Tesseract 가중치 |

### trocr_weight
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.10` |
| **범위** | 0 ~ 1 (step: 0.05) |
| **설명** | TrOCR 가중치 |

### similarity_threshold
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `0.7` |
| **범위** | 0.5 ~ 1.0 (step: 0.05) |
| **설명** | 텍스트 유사도 임계값 (투표 일치 판정) |

## 입력

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `image` | Image | ✅ | 분석할 이미지 |

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `results` | EnsembleResult[] | 앙상블 OCR 결과 |
| `full_text` | string | 전체 텍스트 |
| `engine_status` | object | 각 엔진 상태 |

## 사용 팁

- 단일 엔진보다 정확도가 높지만 느립니다 (약 3배)
- 가중치를 조절하여 도면 타입에 최적화하세요
- 여러 엔진이 동의하면 신뢰도가 올라갑니다

## 도면 유형별 추천 가중치

### 기계 도면 (치수 중심)
```
eDOCr2: 0.50, PaddleOCR: 0.30, Tesseract: 0.15, TrOCR: 0.05
```

### 손글씨 주석 포함
```
eDOCr2: 0.30, PaddleOCR: 0.25, Tesseract: 0.15, TrOCR: 0.30
```

### 다국어 문서
```
eDOCr2: 0.25, PaddleOCR: 0.45, Tesseract: 0.20, TrOCR: 0.10
```

## 앙상블 투표 알고리즘

1. 4개 엔진의 결과를 수집
2. 텍스트 유사도 기반으로 그룹화 (similarity_threshold 적용)
3. 각 그룹에서 가중치 합산
4. 최종 텍스트는 가장 높은 가중치 그룹에서 선택
