---
description: Test individual API endpoints with various scenarios
---

# API 테스트 가이드

## 핵심 원칙: Multipart 우선

**❌ 절대 금지**: base64 인코딩으로 이미지 전송
```bash
# 금지 - 쉘 인자 길이 제한 초과, +33% 용량 증가
curl -d '{"image": "data:image/png;base64,iVBORw0KGgo..."}'
```

**✅ 필수 사용**: multipart/form-data로 파일 직접 전송
```bash
# 권장 - 빠르고 안정적
curl -F "file=@image.png" http://localhost:5005/api/v1/detect
```

| 방식 | 속도 | 안정성 | 용량 |
|------|------|--------|------|
| base64 JSON | 느림 | 쉘 제한 오류 | +33% |
| **multipart** | **빠름** | **안정** | **원본** |

---

## Claude Code 테스트 방법 (우선순위)

### 1. Playwright HTTP (권장)

```
mcp__playwright__playwright_post:
  url: http://localhost:5005/api/v1/detect
  value: '{"file": "@/path/to/image.png"}'  # multipart 자동 처리
```

### 2. curl with multipart (빠른 테스트)

Claude가 직접 실행 가능 (5초 이내 응답 API만):
```bash
curl -s -F "file=@image.png" http://localhost:5005/api/v1/detect
```

### 3. 사용자 직접 실행 (ML 추론)

ML 추론처럼 오래 걸리는 작업은 명령어만 제공:
```
"다음 명령어를 터미널에서 실행해주세요:"
```

## API별 테스트 명령어 (모두 multipart 방식)

### YOLO API (Port 5005)
```bash
curl -F "file=@test.jpg" -F "conf_threshold=0.25" -F "visualize=true" \
  http://localhost:5005/api/v1/detect
```

### eDOCr2 v2 (Port 5002)
```bash
curl -F "file=@test.jpg" http://localhost:5002/api/v2/ocr
```

### PaddleOCR (Port 5006)
```bash
curl -F "file=@test.jpg" -F "lang=en" http://localhost:5006/api/v1/ocr
```

### Table Detector (Port 5022)
```bash
curl -F "file=@test.jpg" http://localhost:5022/api/v1/analyze
```

### Workflow 실행 (Port 8000) - multipart
```bash
curl -F "file=@test.jpg" \
  -F 'workflow={"nodes":[{"id":"n1","type":"yolo","parameters":{}}],"edges":[]}' \
  http://localhost:8000/api/v1/workflow/execute
```

### Gateway Process (Port 8000)
```bash
curl -F "file=@test.jpg" -F "pipeline_mode=speed" -F "use_ocr=true" \
  http://localhost:8000/api/v1/process
```

## Claude가 직접 실행 가능한 것

```bash
# 헬스체크 (< 1초)
curl -s http://localhost:5005/health
curl -s http://localhost:5002/health
curl -s http://localhost:8000/health

# 로그 확인
docker logs yolo-api --tail 50
docker logs edocr2-v2-api --tail 50

# 컨테이너 상태
docker ps | grep -E "yolo|edocr2|paddle"
```

## 체크리스트

- [ ] Status code 200
- [ ] Response structure 확인
- [ ] Processing time 적정 범위
- [ ] 에러 로그 없음
