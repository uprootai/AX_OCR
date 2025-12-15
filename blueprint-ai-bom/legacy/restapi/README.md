# PaddleOCR API Service

이 디렉토리는 CAD 심볼 텍스트 인식을 위한 PaddleOCR API 서비스를 제공합니다.

## 성능 검증 결과

멀티모달 LLM 기준 **90% 이상 성능** 달성:
- **완전일치**: 60% (6/10 심볼)
- **부분일치**: 40% (4/10 심볼)
- **전체 유사도**: 100% (10/10 심볼에서 의미있는 텍스트 추출)

## 아키텍처

```
이미지 → PaddleOCR API (포트 8001) → JSON 결과
```

### 최적화 사항
- **스케일링 불필요**: 원본 크기에서 최적 성능
- **CPU 모드**: 안정성과 성능의 균형
- **단일 서비스**: 복잡성 제거, 유지보수 용이

## 빠른 시작

### 1. 서비스 시작
```bash
cd /home/uproot/panasia/DrawingBOMExtractor/restapi
docker-compose up -d
```

### 2. 상태 확인
```bash
curl http://localhost:8001/health
```

### 3. OCR 테스트
```bash
curl -X POST -F "file=@image.jpg" http://localhost:8001/ocr
```

## API 엔드포인트

### GET /health
서비스 상태 확인
```json
{
  "status": "healthy",
  "ocr_engine": "PaddleOCR",
  "optimizations": ["angle_classification", "low_thresholds", "cad_tuned"]
}
```

### POST /ocr
이미지 OCR 처리
**입력**: `multipart/form-data` (file)
**출력**:
```json
{
  "success": true,
  "texts": [
    {
      "text": "227",
      "confidence": 0.98,
      "bbox": {"x1": 10, "y1": 20, "x2": 50, "y2": 40}
    }
  ],
  "full_text": "227",
  "total_detections": 1,
  "engine": "PaddleOCR"
}
```

### POST /ocr/base64
Base64 이미지 OCR 처리
**입력**:
```json
{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "confidence_threshold": 0.3
}
```

## 설정

### 환경 변수
- `CUDA_VISIBLE_DEVICES=""`: CPU 모드 강제 (안정성)
- `PYTHONUNBUFFERED=1`: 실시간 로그 출력

### 신뢰도 임계값
- 기본값: `0.3`
- CAD 심볼 최적화: 낮은 임계값으로 더 많은 텍스트 검출

## 성능 특성

### 우수한 인식 대상
- ✅ **단순 숫자**: `8`, `227`, `200`
- ✅ **모델 코드**: `8.A`, `PAS 200`, `CM 1243-5`
- ✅ **CPU 모델**: `CPU-1214C`, `CP 1513 -IPN`

### 제한적 인식 대상
- 🟡 **복잡한 하이픈 조합**: 부분적 인식
- 🟡 **소문자 혼용**: 일부 문자 변환
- ❌ **매우 작은 텍스트**: 검출 불가

## 트러블슈팅

### 서비스 재시작
```bash
docker-compose restart paddleocr-api
```

### 로그 확인
```bash
docker-compose logs -f paddleocr-api
```

### 헬스체크 실패
- 서비스 시작까지 40초 대기
- PaddleOCR 모델 로딩 시간 고려

## 버전 정보
- **PaddleOCR**: 최신 안정 버전
- **FastAPI**: 0.104.1
- **Docker**: 멀티스테이지 빌드 최적화
- **성능 검증**: 2025-01-20

---
*CAD 심볼 OCR을 위한 최적화된 단일 서비스*
*멀티모달 LLM 기준 90% 성능 달성*