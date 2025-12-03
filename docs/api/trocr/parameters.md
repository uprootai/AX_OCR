# TrOCR API Parameters

> Microsoft Transformer 기반 OCR - 손글씨/장면 텍스트에 강함

## 기본 정보

| 항목 | 값 |
|------|-----|
| **Port** | 5009 |
| **Endpoint** | `/api/v1/ocr` |
| **Method** | POST |
| **Content-Type** | multipart/form-data |
| **Timeout** | 120초 |

## 파라미터

### model_type
| 항목 | 값 |
|------|-----|
| **타입** | select |
| **기본값** | `printed` |
| **옵션** | `printed`, `handwritten`, `large-printed`, `large-handwritten` |
| **설명** | 모델 타입 |

- **printed**: 인쇄체 텍스트 (base 모델)
- **handwritten**: 손글씨 텍스트 (base 모델)
- **large-printed**: 인쇄체 텍스트 (large 모델, 더 정확)
- **large-handwritten**: 손글씨 텍스트 (large 모델, 더 정확)

### max_length
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `64` |
| **범위** | 16 ~ 256 (step: 8) |
| **설명** | 최대 출력 길이 (토큰 수) |

### num_beams
| 항목 | 값 |
|------|-----|
| **타입** | number |
| **기본값** | `4` |
| **범위** | 1 ~ 10 (step: 1) |
| **설명** | Beam Search 빔 수 |

- 높을수록 정확도 증가, 속도 감소
- 1: Greedy decoding (가장 빠름)
- 4~5: 권장 값

## 입력

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `image` | Image | ✅ | 텍스트 라인 이미지 (크롭 권장) |

## 출력

| 필드 | 타입 | 설명 |
|------|------|------|
| `texts` | OCRResult[] | 인식된 텍스트 목록 |
| `full_text` | string | 전체 텍스트 |

## 사용 팁

- 단일 텍스트 라인에 최적화됨
- YOLO로 텍스트 영역 검출 후 사용 권장
- OCR Ensemble과 함께 사용시 10% 가중치 권장
- 손글씨 메모나 주석 인식에 특히 강함

## 추천 연결

| 소스 노드 | 필드 | 이유 |
|-----------|------|------|
| YOLO | detections | YOLO로 검출한 텍스트 영역을 개별 처리합니다 |
