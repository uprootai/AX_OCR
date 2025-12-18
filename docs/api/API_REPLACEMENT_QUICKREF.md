# API 교체 빠른 참조 카드

## YOLO API 교체 (5분 요약)

### 필수 파일 3개

```
models/my-detector-api/
├── api_server.py      # FastAPI 서버
├── Dockerfile         # 컨테이너 정의
└── requirements.txt   # 의존성
```

### 필수 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/detect` | POST | 검출 실행 |
| `/api/v1/health` | GET | 헬스체크 |

### 필수 응답 필드

```json
{
  "status": "success",
  "detections": [
    {
      "class_id": 0,
      "class_name": "클래스명",
      "confidence": 0.95,
      "bbox": {"x": 100, "y": 100, "width": 50, "height": 50}
    }
  ],
  "total_detections": 1,
  "processing_time": 0.5,
  "model_used": "모델명",
  "visualized_image": "base64_or_null"
}
```

### 필수 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `file` | File | - | 이미지 (필수) |
| `confidence` | float | 0.4 | 신뢰도 |
| `iou` | float | 0.5 | IoU 임계값 |
| `imgsz` | int | 1024 | 이미지 크기 |
| `model_type` | str | - | 모델 선택 |
| `visualize` | bool | true | 시각화 |

---

## PaddleOCR API 교체

### 필수 엔드포인트

| 엔드포인트 | 메서드 |
|-----------|--------|
| `/api/v1/ocr` | POST |
| `/api/v1/health` | GET |

### 필수 응답 필드

```json
{
  "status": "success",
  "detections": [
    {
      "text": "인식된 텍스트",
      "confidence": 0.98,
      "bbox": [[x1,y1], [x2,y2], [x3,y3], [x4,y4]],
      "position": {"x": 100, "y": 200, "width": 150, "height": 30}
    }
  ],
  "total_texts": 1,
  "processing_time": 0.5,
  "visualized_image": "base64_or_null"
}
```

---

## 배포 명령어

```bash
# 1. 빌드
docker-compose build my-detector-api

# 2. 실행
docker-compose up -d my-detector-api

# 3. 테스트
curl http://localhost:5005/api/v1/health

# 4. 검출 테스트
curl -X POST http://localhost:5005/api/v1/detect \
  -F "file=@test.jpg" \
  -F "confidence=0.4"
```

---

## 통합 체크리스트

- [ ] `/api/v1/health` 응답 `{"status": "healthy"}`
- [ ] `/api/v1/detect` 또는 `/api/v1/ocr` 동작
- [ ] `detections` 배열 반환
- [ ] `bbox` 형식 일치 (Detection: `{x,y,width,height}`)
- [ ] Docker 네트워크 `ax_poc_network` 연결
- [ ] 포트 충돌 없음

---

**상세 가이드**: [CUSTOM_API_GUIDE.md](./CUSTOM_API_GUIDE.md)
