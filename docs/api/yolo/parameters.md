# YOLO API

> 통합 객체 검출 - 기계도면(14종) 및 P&ID(60종) 심볼
> **포트**: 5005 | **카테고리**: Detection | **GPU**: 권장 (RTX 3060+)

---

## 개요

통합 YOLO API로 기계도면과 P&ID 심볼을 검출합니다. 4가지 모델 타입을 지원하며, SAHI 슬라이싱으로 대형 도면도 처리 가능합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/detect` | 이미지에서 심볼 검출 |
| GET | `/api/v1/health` | 헬스체크 |

---

## 파라미터

### model_type (모델 선택)

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `model_type` | select | bom_detector | 용도별 모델 선택 |

**옵션:**

| 모델 | 클래스 수 | 설명 | 권장 confidence |
|------|----------|------|-----------------|
| `engineering` | 14 | 기계도면 심볼 (치수선, GD&T 등) | 0.25 |
| `pid_class_aware` | 32 | P&ID 심볼 분류 (밸브, 펌프 등) | 0.25 |
| `pid_class_agnostic` | 1 | P&ID 위치만 검출 | 0.15 |
| `bom_detector` | 27 | 전력 설비 (변압기, 스위치 등) | 0.4 |

### 검출 파라미터

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `confidence` | number | 0.4 | 0.05-1.0 | 검출 신뢰도 임계값 |
| `iou` | number | 0.5 | 0-1.0 | NMS IoU 임계값 |
| `imgsz` | number | 1024 | 320-3520 | 입력 이미지 크기 |
| `visualize` | boolean | true | - | 결과 시각화 생성 |
| `task` | select | detect | detect, segment | 작업 유형 |

### SAHI 슬라이싱 파라미터

| 파라미터 | 타입 | 기본값 | 범위 | 설명 |
|---------|------|--------|------|------|
| `use_sahi` | boolean | false | - | SAHI 슬라이싱 활성화 |
| `slice_height` | number | 512 | 256-2048 | 슬라이스 높이 |
| `slice_width` | number | 512 | 256-2048 | 슬라이스 너비 |
| `overlap_ratio` | number | 0.25 | 0.1-0.5 | 슬라이스 오버랩 비율 |

---

## 모델별 권장 설정

### engineering (기계도면)

```json
{
  "model_type": "engineering",
  "confidence": 0.25,
  "iou": 0.45,
  "imgsz": 1280,
  "use_sahi": false
}
```

**검출 가능 심볼 (14종):**
- linear_dim, angular_dim, radius_dim, diameter_dim
- text_block, tolerance_dim, surface_finish
- flatness, cylindricity, parallelism, perpendicularity
- position, reference_dim, chamfer_dim

### pid_class_aware (P&ID 분류)

```json
{
  "model_type": "pid_class_aware",
  "confidence": 0.25,
  "iou": 0.45,
  "imgsz": 640,
  "use_sahi": true,
  "slice_height": 512,
  "slice_width": 512,
  "overlap_ratio": 0.25
}
```

**검출 가능 심볼 (32종):**
- 밸브: gate_valve, globe_valve, ball_valve, butterfly_valve, check_valve, control_valve, safety_valve
- 설비: pump, compressor, heat_exchanger, tank, vessel
- 계기: pressure_gauge, temperature_gauge, flow_meter, level_indicator

### pid_class_agnostic (P&ID 위치만)

```json
{
  "model_type": "pid_class_agnostic",
  "confidence": 0.15,
  "iou": 0.40,
  "imgsz": 640,
  "use_sahi": true
}
```

### bom_detector (전력 설비)

```json
{
  "model_type": "bom_detector",
  "confidence": 0.4,
  "iou": 0.5,
  "imgsz": 1024,
  "use_sahi": false
}
```

**검출 가능 심볼 (27종):**
- transformer, circuit_breaker, fuse, switch, relay
- motor, generator, meter, panel, cable_tray

---

## 응답

```json
{
  "status": "success",
  "data": {
    "detections": [
      {
        "bbox": [100, 200, 150, 250],
        "class_name": "gate_valve",
        "class_id": 0,
        "confidence": 0.92,
        "center": [125, 225]
      }
    ],
    "total_detections": 15,
    "class_counts": {
      "gate_valve": 3,
      "pump": 2
    },
    "visualized_image": "data:image/jpeg;base64,..."
  },
  "processing_time": 1.23
}
```

---

## 사용 예시

```bash
# 기계도면 심볼 검출
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@drawing.png" \
  -F "model_type=engineering" \
  -F "confidence=0.25"

# P&ID 심볼 분류 (SAHI 사용)
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@pid.png" \
  -F "model_type=pid_class_aware" \
  -F "use_sahi=true"
```

---

## 리소스 요구사항

| 환경 | VRAM/RAM | 처리 속도 |
|------|----------|----------|
| GPU (권장) | ~3GB VRAM | 1-2초 |
| CPU | ~4GB RAM | 10-20초 |

**imgsz별 VRAM 사용:**
- 640: ~1.5GB
- 1280: ~2.5GB
- 3520: ~6GB+

---

**최종 수정**: 2026-01-17
