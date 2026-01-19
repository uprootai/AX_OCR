# GT Comparison API

> Ground Truth 비교 및 평가 메트릭 계산
> **포트**: 5020 | **카테고리**: Analysis | **GPU**: 불필요

---

## 개요

Ground Truth(정답 라벨)와 YOLO 검출 결과를 비교하여 Precision, Recall, F1 스코어를 계산합니다.

---

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/ground-truth` | GT 파일 목록 조회 |
| GET | `/api/ground-truth/{filename}` | GT 라벨 로드 |
| POST | `/api/ground-truth/compare` | GT 비교 실행 |

---

## 파라미터

### compare 엔드포인트

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `filename` | string | (필수) | 이미지 파일명 |
| `detections` | array | (필수) | YOLO 검출 결과 배열 |
| `img_width` | integer | 1000 | 이미지 너비 |
| `img_height` | integer | 1000 | 이미지 높이 |
| `iou_threshold` | number | 0.5 | IoU 매칭 임계값 (0.1-0.9) |
| `model_type` | string | bom_detector | 모델 타입 |
| `class_agnostic` | boolean | false | 클래스 무시 모드 |

### model_type 옵션

- `bom_detector`: BOM 검출 모델
- `engineering`: 기계도면 모델
- `pid_class_aware`: P&ID 분류 모델
- `pid_symbol`: P&ID 심볼 모델
- `custom`: 커스텀 모델

---

## 응답

```json
{
  "status": "success",
  "data": {
    "filename": "test_drawing.png",
    "has_ground_truth": true,
    "metrics": {
      "tp": 18,
      "fp": 2,
      "fn": 3,
      "precision": 90.0,
      "recall": 85.7,
      "f1_score": 87.8,
      "iou_threshold": 0.5
    },
    "gt_count": 21,
    "detection_count": 20
  }
}
```

---

## 사용 예시

```bash
curl -X POST http://localhost:5020/api/ground-truth/compare \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "drawing.png",
    "detections": [
      {"class_name": "valve", "confidence": 0.95, "bbox": {"x1": 100, "y1": 200, "x2": 150, "y2": 250}}
    ],
    "iou_threshold": 0.5,
    "model_type": "pid_class_aware"
  }'
```

---

**최종 수정**: 2026-01-17
