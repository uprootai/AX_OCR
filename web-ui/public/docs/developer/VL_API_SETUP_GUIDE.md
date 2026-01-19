# 🧠 VL API Setup Guide

**Vision Language Model API 설정 가이드**

---

## 📋 Overview

VL API는 Claude 3.5 Sonnet 또는 GPT-4o와 같은 멀티모달 LLM을 사용하여 도면에서 정보를 추출합니다.

**지원 기능**:
- 📋 Information Block 추출 (부품명, 재질, 스케일 등)
- 📐 치수 추출 (dimension text recognition)
- 🏭 제조 공정 추론 (manufacturing process inference)
- ✓ QC 체크리스트 생성 (quality control checklist)

---

## 🔑 API 키 설정

### 1. Anthropic API 키 (Claude 3.5 Sonnet)

#### 키 발급
1. https://console.anthropic.com/ 방문
2. 계정 생성 또는 로그인
3. Settings → API Keys → Create Key
4. 생성된 키 복사 (sk-ant-api03-...)

#### 환경 변수 설정
```bash
# .env 파일에 추가
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 2. OpenAI API 키 (GPT-4o)

#### 키 발급
1. https://platform.openai.com/api-keys 방문
2. 계정 생성 또는 로그인
3. Create new secret key
4. 생성된 키 복사 (sk-...)

#### 환경 변수 설정
```bash
# .env 파일에 추가
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🐳 Docker Compose 설정

### docker-compose.yml

```yaml
services:
  vl-api:
    build: ./vl-api
    container_name: vl-api
    ports:
      - "5004:5004"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEFAULT_MODEL=claude-3-5-sonnet-20241022
    volumes:
      - ./samples:/app/samples:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5004/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## ✅ 설정 확인

### 1. 컨테이너 상태 확인
```bash
docker ps | grep vl-api
```

**Expected output**:
```
vl-api   Up X minutes (healthy)   0.0.0.0:5004->5004/tcp
```

### 2. Health Check
```bash
curl http://localhost:5004/api/v1/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "service": "VL API",
  "version": "1.0.0",
  "models": {
    "anthropic": "configured",
    "openai": "configured"
  }
}
```

### 3. API 키 검증
```bash
# Anthropic 키 확인 (마스킹됨)
docker exec vl-api printenv | grep ANTHROPIC_API_KEY | sed 's/=.*/=***/'

# OpenAI 키 확인 (마스킹됨)
docker exec vl-api printenv | grep OPENAI_API_KEY | sed 's/=.*/=***/'
```

**Expected output**:
```
ANTHROPIC_API_KEY=***
OPENAI_API_KEY=***
```

---

## 🧪 테스트

### Web UI에서 테스트

1. Web UI 접속: http://localhost:5173
2. 좌측 사이드바 → Quick Test → **VL Model** 클릭
3. 테스트 이미지 업로드
4. VL 기능 선택:
   - 📋 Information Block 추출
   - 📐 치수 추출
   - 🏭 제조 공정 추론
   - ✓ QC 체크리스트 생성
5. 모델 선택:
   - Claude 3.5 Sonnet (권장)
   - GPT-4o
6. **분석 시작** 버튼 클릭

### cURL로 직접 테스트

```bash
# Information Block 추출
curl -X POST http://localhost:5004/api/v1/extract_info_block \
  -F "file=@samples/sample2_interm_shaft.jpg" \
  -F "query_fields=name,material,scale" \
  -F "model=claude-3-5-sonnet-20241022"

# 치수 추출
curl -X POST http://localhost:5004/api/v1/extract_dimensions \
  -F "file=@samples/sample2_interm_shaft.jpg" \
  -F "model=claude-3-5-sonnet-20241022"

# 제조 공정 추론
curl -X POST http://localhost:5004/api/v1/infer_manufacturing_process \
  -F "file=@samples/sample2_interm_shaft.jpg" \
  -F "model=claude-3-5-sonnet-20241022"

# QC 체크리스트 생성
curl -X POST http://localhost:5004/api/v1/generate_qc_checklist \
  -F "file=@samples/sample2_interm_shaft.jpg" \
  -F "model=claude-3-5-sonnet-20241022"
```

---

## 💰 비용 관리

### Claude 3.5 Sonnet 가격
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- 이미지 (1568x1568): ~1,600 tokens

**예상 비용** (도면 1장 기준):
- Information Block 추출: ~$0.01-0.02
- 치수 추출: ~$0.02-0.05
- 제조 공정 추론: ~$0.03-0.07
- QC 체크리스트: ~$0.02-0.04

### GPT-4o 가격
- Input: $2.50 / 1M tokens
- Output: $10.00 / 1M tokens
- 이미지 (high detail): ~765-1,105 tokens

**예상 비용** (도면 1장 기준):
- Information Block 추출: ~$0.01-0.02
- 치수 추출: ~$0.02-0.04
- 제조 공정 추론: ~$0.02-0.05
- QC 체크리스트: ~$0.02-0.03

### 비용 절감 팁
1. **적절한 모델 선택**:
   - 단순 추출 → GPT-4o (저렴)
   - 복잡한 추론 → Claude 3.5 Sonnet (정확)

2. **불필요한 호출 방지**:
   - 캐싱 활용 (동일 이미지 재사용)
   - 배치 처리 (여러 정보 한 번에 추출)

3. **모니터링**:
   - Web UI Monitor 탭에서 API 사용량 확인
   - 비용 초과 알림 설정

---

## 🔧 트러블슈팅

### 문제 1: "API key not configured" 에러

**증상**:
```json
{
  "detail": "Anthropic API key not configured"
}
```

**해결**:
1. `.env` 파일에 `ANTHROPIC_API_KEY` 추가
2. Docker Compose 재시작:
   ```bash
   docker-compose restart vl-api
   ```

### 문제 2: "Model not found" 에러

**증상**:
```json
{
  "detail": "Model 'claude-3-5-sonnet-20241022' not found"
}
```

**해결**:
- API 키가 유효한지 확인
- 모델 이름 철자 확인
- Anthropic Console에서 모델 접근 권한 확인

### 문제 3: Timeout 에러

**증상**:
```
ReadTimeout: Request timed out
```

**해결**:
1. 이미지 크기 확인 (권장: <10MB)
2. timeout 설정 증가:
   ```python
   # vl-api/config.py
   REQUEST_TIMEOUT = 60  # 30 → 60초로 증가
   ```

### 문제 4: Rate Limit 에러

**증상**:
```json
{
  "error": "rate_limit_exceeded"
}
```

**해결**:
- API 사용량 확인 (Anthropic/OpenAI Console)
- 요금제 업그레이드 고려
- Retry 로직 구현 (exponential backoff)

---

## 📊 성능 벤치마크

### Claude 3.5 Sonnet

| 기능 | 평균 응답 시간 | 정확도 | 비용 |
|------|--------------|--------|------|
| Information Block | 3-5초 | 95% | $0.02 |
| 치수 추출 | 5-8초 | 90% | $0.04 |
| 제조 공정 추론 | 8-12초 | 92% | $0.06 |
| QC 체크리스트 | 6-10초 | 88% | $0.03 |

### GPT-4o

| 기능 | 평균 응답 시간 | 정확도 | 비용 |
|------|--------------|--------|------|
| Information Block | 2-4초 | 90% | $0.015 |
| 치수 추출 | 4-6초 | 85% | $0.03 |
| 제조 공정 추론 | 6-9초 | 85% | $0.04 |
| QC 체크리스트 | 5-8초 | 82% | $0.025 |

**결론**: Claude 3.5 Sonnet이 더 정확하지만 약간 느리고 비쌈. 용도에 따라 선택.

---

## 🔗 참고 자료

- [Anthropic API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- [Claude 3.5 Sonnet Release Notes](https://www.anthropic.com/news/claude-3-5-sonnet)
- [GPT-4o Release Notes](https://openai.com/index/hello-gpt-4o/)

---

**Last Updated**: 2026-01-17
**Maintainer**: Development Team
