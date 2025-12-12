# API 스펙 작성 컨벤션

## 1. 카테고리별 표준 출력

### OCR 카테고리
- 필수 출력 필드: `texts`, `full_text`
- 선택 출력 필드: `visualized_image`, `processing_time`
- 표준 타입: `TextResult[]`

### Detection 카테고리
- 필수 출력 필드: `detections`, `total_detections`
- 선택 출력 필드: `visualized_image`, `processing_time`
- 표준 타입: `DetectionResult[]`

## 2. 표준 타입 정의

### TextResult
```json
{
  "text": "string",
  "confidence": "number (0-1)",
  "bbox": "[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]"
}
```

### DetectionResult
```json
{
  "class_name": "string",
  "confidence": "number (0-1)",
  "bbox": "[x1, y1, x2, y2]",
  "class_id": "number"
}
```
