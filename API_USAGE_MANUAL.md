# API 사용 매뉴얼

**작성일**: 2025-11-03
**대상**: API 사용자 및 프론트엔드 개발자
**버전**: v1.0

---

## 📋 목차

1. [API 개요](#1-api-개요)
2. [인증 및 보안](#2-인증-및-보안)
3. [YOLOv11 API](#3-yolov11-api)
4. [eDOCr2 API](#4-edocr2-api)
5. [EDGNet API](#5-edgnet-api)
6. [Skin Model API](#6-skin-model-api)
7. [Gateway API](#7-gateway-api)
8. [에러 코드](#8-에러-코드)
9. [코드 예제](#9-코드-예제)

---

## 1. API 개요

### 베이스 URL

| 서비스 | URL | 포트 |
|--------|-----|------|
| YOLOv11 API | `http://localhost:5005` | 5005 |
| eDOCr2 API | `http://localhost:5001` | 5001 |
| EDGNet API | `http://localhost:5002` | 5002 |
| Skin Model API | `http://localhost:5003` | 5003 |
| Gateway API | `http://localhost:8000` | 8000 |

### 공통 응답 형식

**성공 응답**:
```json
{
  "status": "success",
  "data": {
    // 실제 데이터
  },
  "processing_time": 2.34,
  "timestamp": "2025-11-03T10:30:45Z"
}
```

**에러 응답**:
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "지원하지 않는 파일 형식입니다",
    "details": "Only PDF, PNG, JPG files are supported"
  },
  "timestamp": "2025-11-03T10:30:45Z"
}
```

### 공통 헤더

```http
Content-Type: application/json
Accept: application/json
```

---

## 2. 인증 및 보안

### API 키 (선택적)

프로덕션 환경에서는 API 키를 헤더에 포함:

```http
X-API-Key: your-api-key-here
```

### CORS 설정

개발 환경에서는 모든 origin 허용. 프로덕션에서는 화이트리스트 설정 필요.

### Rate Limiting

- **개발 환경**: 제한 없음
- **프로덕션**: 100 req/min per IP

---

## 3. YOLOv11 API

### 3.1. 객체 검출 (Object Detection)

**Endpoint**: `POST /api/v1/detect`

**설명**: 도면 이미지에서 치수, GD&T 기호 등을 검출합니다.

**요청**:
```bash
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@drawing.jpg" \
  -F "conf_threshold=0.25" \
  -F "iou_threshold=0.7" \
  -F "imgsz=1280" \
  -F "visualize=true"
```

**파라미터**:
| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| file | File | ✅ | - | 도면 이미지 (JPG/PNG) |
| conf_threshold | float | ❌ | 0.25 | 신뢰도 임계값 (0.0~1.0) |
| iou_threshold | float | ❌ | 0.7 | IoU 임계값 (0.0~1.0) |
| imgsz | int | ❌ | 1280 | 입력 이미지 크기 |
| visualize | bool | ❌ | true | 시각화 이미지 생성 여부 |

**응답**:
```json
{
  "status": "success",
  "data": {
    "detections": [
      {
        "class": "diameter_dim",
        "class_id": 0,
        "confidence": 0.87,
        "bbox": [120, 340, 180, 365],
        "bbox_normalized": [0.0625, 0.3148, 0.09375, 0.3379],
        "text": "φ476",
        "area": 1500
      },
      {
        "class": "linear_dim",
        "class_id": 1,
        "confidence": 0.92,
        "bbox": [450, 220, 490, 245],
        "bbox_normalized": [0.2344, 0.2037, 0.2552, 0.2269],
        "text": "120",
        "area": 1000
      }
    ],
    "total_detections": 23,
    "classes_detected": ["diameter_dim", "linear_dim", "flatness", "text_block"],
    "image_size": [1920, 1080],
    "visualization_url": "/results/drawing_detect_20251103_103045.jpg"
  },
  "processing_time": 2.34
}
```

---

### 3.2. 치수 추출 (Extract Dimensions)

**Endpoint**: `POST /api/v1/extract_dimensions`

**설명**: 검출 결과에서 치수 정보만 추출합니다.

**요청**:
```bash
curl -X POST http://localhost:5005/api/v1/extract_dimensions \
  -F "file=@drawing.jpg" \
  -F "conf_threshold=0.3"
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "type": "diameter",
        "value": 476.0,
        "unit": "mm",
        "tolerance": null,
        "bbox": [120, 340, 180, 365],
        "confidence": 0.87,
        "raw_text": "φ476"
      },
      {
        "type": "linear",
        "value": 120.0,
        "unit": "mm",
        "tolerance": {"plus": 0.1, "minus": 0.1},
        "bbox": [450, 220, 490, 245],
        "confidence": 0.92,
        "raw_text": "120 ±0.1"
      },
      {
        "type": "radius",
        "value": 50.0,
        "unit": "mm",
        "tolerance": null,
        "bbox": [680, 510, 720, 535],
        "confidence": 0.85,
        "raw_text": "R50"
      }
    ],
    "gdt_symbols": [
      {
        "type": "flatness",
        "value": 0.1,
        "datum": null,
        "bbox": [300, 400, 340, 430],
        "confidence": 0.78,
        "raw_text": "⌹0.1"
      },
      {
        "type": "position",
        "value": 0.05,
        "datum": "A",
        "bbox": [500, 600, 560, 630],
        "confidence": 0.82,
        "raw_text": "⌖0.05|A"
      }
    ],
    "total_dimensions": 15,
    "total_gdt": 8
  },
  "processing_time": 2.1
}
```

---

### 3.3. 헬스체크

**Endpoint**: `GET /api/v1/health`

**요청**:
```bash
curl http://localhost:5005/api/v1/health
```

**응답**:
```json
{
  "status": "healthy",
  "service": "YOLOv11 API",
  "version": "1.0.0",
  "model": {
    "loaded": true,
    "path": "/app/models/best.pt",
    "size": "yolo11n",
    "classes": 14
  },
  "system": {
    "device": "cuda:0",
    "gpu": "NVIDIA GeForce RTX 3080",
    "memory_available": "6.2 GB"
  },
  "uptime": 3600
}
```

---

### 3.4. API 문서 (Swagger)

**Endpoint**: `GET /api/v1/docs`

**브라우저에서 접속**:
```
http://localhost:5005/docs
```

대화형 API 문서를 통해 직접 테스트 가능.

---

## 4. eDOCr2 API

### 4.1. OCR 처리

**Endpoint**: `POST /api/v1/ocr`

**설명**: 도면에서 텍스트 및 치수를 OCR로 추출합니다.

**요청**:
```bash
curl -X POST http://localhost:5001/api/v1/ocr \
  -F "file=@drawing.pdf" \
  -F "extract_dimensions=true" \
  -F "extract_gdt=true" \
  -F "extract_text=true"
```

**파라미터**:
| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| file | File | ✅ | - | 도면 파일 (PDF/JPG/PNG) |
| extract_dimensions | bool | ❌ | true | 치수 추출 여부 |
| extract_gdt | bool | ❌ | true | GD&T 추출 여부 |
| extract_text | bool | ❌ | true | 일반 텍스트 추출 여부 |

**응답**:
```json
{
  "status": "success",
  "data": {
    "dimensions": [
      {
        "value": 392,
        "unit": "mm",
        "type": "diameter",
        "tolerance": "±0.1",
        "bbox": [1234, 567, 1289, 590]
      }
    ],
    "gdt": [
      {
        "type": "flatness",
        "value": 0.05,
        "bbox": [890, 450, 920, 480]
      }
    ],
    "text": {
      "drawing_number": "A12-311197-9",
      "revision": "Rev.2",
      "title": "SHAFT ASSEMBLY",
      "material": "S45C"
    },
    "ocr_confidence": 0.83
  },
  "processing_time": 8.5
}
```

---

## 5. EDGNet API

### 5.1. 도면 세그멘테이션

**Endpoint**: `POST /api/v1/segment`

**설명**: 그래프 신경망으로 도면 컴포넌트를 분류합니다.

**요청**:
```bash
curl -X POST http://localhost:5002/api/v1/segment \
  -F "file=@drawing.png" \
  -F "visualize=true"
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "classifications": {
      "contour": 80,
      "text": 30,
      "dimension": 40,
      "centerline": 15,
      "hatch": 5
    },
    "graph": {
      "nodes": 150,
      "edges": 280,
      "connected_components": 12
    },
    "visualization_url": "/results/drawing_segment.png"
  },
  "processing_time": 12.3
}
```

---

### 5.2. 벡터화

**Endpoint**: `POST /api/v1/vectorize`

**설명**: 래스터 도면을 벡터 형식으로 변환합니다.

**요청**:
```bash
curl -X POST http://localhost:5002/api/v1/vectorize \
  -F "file=@drawing.png" \
  -F "output_format=dxf"
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "vector_file_url": "/results/drawing.dxf",
    "entities": {
      "lines": 245,
      "arcs": 38,
      "circles": 12,
      "texts": 45
    }
  },
  "processing_time": 15.7
}
```

---

## 6. Skin Model API

### 6.1. 공차 예측

**Endpoint**: `POST /api/v1/tolerance`

**설명**: 치수 정보를 기반으로 공차를 예측합니다.

**요청**:
```bash
curl -X POST http://localhost:5003/api/v1/tolerance \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [
      {"type": "diameter", "value": 392, "tolerance": 0.1}
    ],
    "material": "Steel",
    "manufacturing_process": "CNC"
  }'
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "predicted_tolerances": {
      "flatness": 0.048,
      "cylindricity": 0.092,
      "parallelism": 0.035
    },
    "manufacturability": {
      "score": 0.85,
      "difficulty": "Medium",
      "estimated_cost_factor": 1.2
    },
    "recommendations": [
      "Consider increasing flatness tolerance to 0.05mm for better manufacturability"
    ]
  },
  "processing_time": 2.1
}
```

---

### 6.2. GD&T 검증

**Endpoint**: `POST /api/v1/validate`

**설명**: GD&T 설계가 제조 가능한지 검증합니다.

**요청**:
```bash
curl -X POST http://localhost:5003/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{
    "gdt": [
      {"type": "flatness", "value": 0.01},
      {"type": "cylindricity", "value": 0.02}
    ],
    "material": "Aluminum"
  }'
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "is_valid": true,
    "warnings": [
      "Flatness 0.01mm is very tight, may increase cost"
    ],
    "errors": [],
    "manufacturability_score": 0.75
  }
}
```

---

## 7. Gateway API

### 7.1. 통합 처리

**Endpoint**: `POST /api/v1/process`

**설명**: 전체 파이프라인을 한 번에 실행합니다.

**요청**:
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf" \
  -F "use_yolo=true" \
  -F "use_edgnet=true" \
  -F "use_skinmodel=true" \
  -F "generate_quote=true"
```

**파라미터**:
| 이름 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| file | File | ✅ | - | 도면 파일 |
| use_yolo | bool | ❌ | true | YOLO 사용 여부 |
| use_edocr | bool | ❌ | false | eDOCr 사용 여부 |
| use_edgnet | bool | ❌ | true | EDGNet 사용 여부 |
| use_skinmodel | bool | ❌ | true | Skin Model 사용 여부 |
| generate_quote | bool | ❌ | false | 견적 생성 여부 |

**응답**:
```json
{
  "status": "success",
  "data": {
    "yolo_results": {
      "total_detections": 23,
      "dimensions": [...],
      "gdt": [...]
    },
    "edgnet_results": {
      "classifications": {...}
    },
    "skinmodel_results": {
      "predicted_tolerances": {...},
      "manufacturability": {...}
    },
    "quote": {
      "total": 11200.00,
      "currency": "KRW",
      "breakdown": {
        "material": 1500.00,
        "machining": 8500.00,
        "tolerance_premium": 1200.00
      },
      "lead_time_days": 7
    }
  },
  "processing_time": 25.8
}
```

---

### 7.2. 견적 생성

**Endpoint**: `POST /api/v1/quote`

**설명**: 분석 결과를 기반으로 견적서를 생성합니다.

**요청**:
```bash
curl -X POST http://localhost:8000/api/v1/quote \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": [...],
    "gdt": [...],
    "material": "Steel",
    "quantity": 100
  }'
```

**응답**:
```json
{
  "status": "success",
  "data": {
    "quote_id": "Q20251103-001",
    "total": 112000.00,
    "unit_price": 1120.00,
    "quantity": 100,
    "breakdown": {
      "material_per_unit": 150.00,
      "machining_per_unit": 850.00,
      "tolerance_premium_per_unit": 120.00
    },
    "lead_time": {
      "days": 7,
      "rush_available": true,
      "rush_days": 3,
      "rush_extra_cost": 30000.00
    },
    "valid_until": "2025-11-10"
  }
}
```

---

## 8. 에러 코드

| 코드 | HTTP | 설명 | 해결방법 |
|------|------|------|----------|
| INVALID_INPUT | 400 | 잘못된 입력 파라미터 | 파라미터 확인 |
| FILE_TOO_LARGE | 400 | 파일 크기 초과 (>10MB) | 파일 크기 줄이기 |
| UNSUPPORTED_FORMAT | 400 | 지원하지 않는 파일 형식 | JPG/PNG/PDF만 가능 |
| MODEL_NOT_LOADED | 500 | 모델 로드 실패 | 서버 재시작 |
| INFERENCE_ERROR | 500 | 추론 중 오류 | 이미지 품질 확인 |
| TIMEOUT | 504 | 처리 시간 초과 | 이미지 해상도 낮추기 |
| RATE_LIMIT_EXCEEDED | 429 | 요청 제한 초과 | 잠시 후 재시도 |

---

## 9. 코드 예제

### Python (requests)

```python
import requests
import json

# YOLOv11 API - 객체 검출
url = "http://localhost:5005/api/v1/detect"
files = {"file": open("drawing.jpg", "rb")}
data = {
    "conf_threshold": 0.25,
    "visualize": True
}

response = requests.post(url, files=files, data=data)
result = response.json()

if result["status"] == "success":
    print(f"검출된 객체: {result['data']['total_detections']}개")
    for det in result['data']['detections']:
        print(f"  - {det['class']}: {det.get('text', 'N/A')} (신뢰도: {det['confidence']:.2f})")
else:
    print(f"에러: {result['error']['message']}")
```

### JavaScript (axios)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function detectObjects(imagePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(imagePath));
  form.append('conf_threshold', '0.25');
  form.append('visualize', 'true');

  try {
    const response = await axios.post(
      'http://localhost:5005/api/v1/detect',
      form,
      { headers: form.getHeaders() }
    );

    console.log('검출 결과:', response.data);
    return response.data;
  } catch (error) {
    console.error('에러:', error.response?.data || error.message);
  }
}

detectObjects('drawing.jpg');
```

### cURL

```bash
# YOLOv11 - 객체 검출
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@drawing.jpg" \
  -F "conf_threshold=0.25" \
  -F "visualize=true" \
  | jq '.data.detections[] | {class, confidence, text}'

# Gateway - 통합 처리
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@drawing.pdf" \
  -F "use_yolo=true" \
  -F "generate_quote=true" \
  | jq '.data.quote'

# 헬스체크
curl http://localhost:5005/api/v1/health | jq .
```

### Python (httpx - async)

```python
import httpx
import asyncio

async def process_drawing(file_path: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {"file": open(file_path, "rb")}
        data = {
            "use_yolo": True,
            "use_edgnet": True,
            "generate_quote": True
        }

        response = await client.post(
            "http://localhost:8000/api/v1/process",
            files=files,
            data=data
        )

        return response.json()

# 실행
result = asyncio.run(process_drawing("drawing.pdf"))
print(f"견적 금액: {result['data']['quote']['total']}원")
```

---

## 📚 추가 리소스

- **Swagger UI**: 각 API의 `/docs` 엔드포인트에서 대화형 문서 확인
- **상세 구현 가이드**: `YOLOV11_IMPLEMENTATION_GUIDE.md`
- **빠른 시작**: `YOLOV11_QUICKSTART.md`
- **트러블슈팅**: `TROUBLESHOOTING_GUIDE.md`

---

**작성자**: AX 실증사업팀
**최종 업데이트**: 2025-11-03
**문의**: dev@uproot.com
