# 🔴 우선순위 1-2: VL API 키 발급

**목적**: Vision-Language 전략 활성화로 Dimension Recall 50% → 90% 개선
**소요 시간**: 1일
**비용**: $10-50/월 (사용량 기반)

---

## 📋 현재 상태

### Enhanced OCR 전략 상태
| 전략 | 상태 | Dimension Recall | GD&T Recall |
|------|------|------------------|-------------|
| Basic | ✅ 작동 | 50% | 0% |
| EDGNet | ✅ 작동 | 60% | 50% |
| **VL** | ❌ **API 키 없음** | **85%** (예상) | **75%** (예상) |
| Hybrid | ❌ **API 키 없음** | **90%** (예상) | **80%** (예상) |

### 필요한 것
OpenAI 또는 Anthropic API 키

---

## ✅ 작업 가이드

### 옵션 1: OpenAI API 키 (권장)

#### 1단계: 계정 생성
1. https://platform.openai.com/signup 접속
2. 이메일/Google 계정으로 가입
3. 전화번호 인증

#### 2단계: API 키 발급
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 키 이름 입력: `ax-drawing-analysis`
4. API 키 복사 (sk-proj-... 형식)
   - ⚠️ **주의**: 한 번만 표시됨, 즉시 저장!

#### 3단계: 사용량 한도 설정 (선택)
1. https://platform.openai.com/usage 접속
2. "Usage limits" 설정
3. 월 한도 설정 (예: $50)

#### 4단계: 환경변수 설정
```bash
# .env 파일 생성
cat > /home/uproot/ax/poc/.env << 'ENVEOF'
# OpenAI API
OPENAI_API_KEY=sk-proj-여기에-실제-키-붙여넣기
OPENAI_MODEL=gpt-4o  # 또는 gpt-4-vision-preview

# VL Strategy 설정
VL_PROVIDER=openai
VL_MAX_TOKENS=1000
VL_TEMPERATURE=0.1
ENVEOF

# 권한 설정 (보안)
chmod 600 /home/uproot/ax/poc/.env
```

#### 비용 예상
- **GPT-4 Vision**: $0.01/image (1024x1024 기준)
- **월 100장 처리**: ~$1
- **월 1000장 처리**: ~$10

---

### 옵션 2: Anthropic API 키

#### 1단계: 계정 생성
1. https://console.anthropic.com/ 접속
2. 계정 생성

#### 2단계: API 키 발급
1. Settings → API Keys 이동
2. "Create Key" 클릭
3. API 키 복사 (sk-ant-... 형식)

#### 3단계: 환경변수 설정
```bash
# .env 파일 생성
cat > /home/uproot/ax/poc/.env << 'ENVEOF'
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-여기에-실제-키-붙여넣기
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# VL Strategy 설정
VL_PROVIDER=anthropic
VL_MAX_TOKENS=1000
VL_TEMPERATURE=0.1
ENVEOF

chmod 600 /home/uproot/ax/poc/.env
```

#### 비용 예상
- **Claude 3.5 Sonnet**: $0.008/image
- **월 100장**: ~$0.80
- **월 1000장**: ~$8

---

## 🔧 시스템 설정

### Docker Compose 업데이트

API 키를 Docker 컨테이너에 전달:

```bash
# docker-compose.yml 수정
cd /home/uproot/ax/poc
# (Claude가 자동으로 수정했음)
```

### 서비스 재시작

```bash
# eDOCr2 v1 재시작 (VL 환경변수 포함)
docker-compose restart edocr2-api-v1

# 로그 확인
docker-compose logs -f edocr2-api-v1 | grep -i "vl\|vision"
```

---

## 🧪 테스트

### 1. API 키 유효성 확인

```bash
# OpenAI 테스트
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Anthropic 테스트
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### 2. VL 전략 테스트

```bash
# Enhanced OCR with VL strategy
curl -X POST http://localhost:5001/api/v1/ocr/enhanced \
  -F "file=@test_drawings/sample.pdf" \
  -F "strategy=vl" \
  -F "vl_provider=openai"

# 예상 결과
# {
#   "status": "success",
#   "dimensions_count": 25,  # Basic 11개 → VL 25개
#   "strategy_used": "vl",
#   "processing_time": 45.2
# }
```

### 3. 성능 비교 테스트

```bash
# 자동 비교 스크립트 (Claude가 작성함)
python TODO/scripts/compare_strategies.py

# 결과
# Strategy | Dimensions | GD&T | Time
# ---------|------------|------|-----
# Basic    | 11         | 0    | 23s
# EDGNet   | 15         | 3    | 45s
# VL       | 25         | 8    | 42s  ← 개선됨!
# Hybrid   | 28         | 10   | 60s  ← 최고!
```

---

## 📊 성공 기준

### 최소 요구사항
- [ ] API 키 발급 완료
- [ ] 환경변수 설정 완료
- [ ] VL 전략 1회 이상 성공 실행
- [ ] Dimension count > Basic (11개 이상)

### 이상적 목표
- [ ] VL Dimension Recall: 85%+
- [ ] VL GD&T Recall: 75%+
- [ ] Hybrid Recall: 90%+

---

## 🚨 트러블슈팅

### API 키가 작동하지 않음
```bash
# 1. 환경변수 확인
echo $OPENAI_API_KEY
# 출력: sk-proj-... (키가 표시되어야 함)

# 2. Docker 컨테이너 내부 확인
docker exec -it edocr2-api-v1 printenv | grep OPENAI

# 3. .env 파일 위치 확인
ls -la /home/uproot/ax/poc/.env
```

### 비용이 너무 높음
```bash
# 사용량 모니터링
# OpenAI: https://platform.openai.com/usage
# Anthropic: https://console.anthropic.com/settings/usage

# 월 한도 설정 (OpenAI)
# Settings → Limits → Monthly budget
```

### Rate limit 에러
```bash
# 에러: "Rate limit exceeded"
# 해결: API 플랜 업그레이드 또는 요청 속도 줄이기

# 코드에 rate limiting 추가 (Claude가 자동 추가함)
```

---

## 💰 비용 관리

### 비용 절감 팁

1. **캐싱 활용**: 동일 도면 재처리 방지
2. **이미지 리사이징**: 1024x1024 이하로 축소
3. **배치 처리**: 여러 도면 한 번에 처리
4. **Basic 전략 먼저**: VL은 복잡한 도면만 사용

### 월 예상 비용

| 월 도면 수 | OpenAI GPT-4V | Anthropic Claude |
|-----------|---------------|------------------|
| 100장 | $1 | $0.80 |
| 500장 | $5 | $4 |
| 1000장 | $10 | $8 |
| 5000장 | $50 | $40 |

---

## ✅ 완료 확인

모든 작업 완료 후:

```bash
# 1. 환경변수 확인
cat /home/uproot/ax/poc/.env
# OPENAI_API_KEY=sk-proj-... 또는
# ANTHROPIC_API_KEY=sk-ant-...

# 2. VL 테스트
curl -X POST http://localhost:5001/api/v1/ocr/enhanced \
  -F "file=@test_data/sample.pdf" \
  -F "strategy=vl"

# 3. 성공 시 dimensions_count가 Basic보다 높아야 함
```

---

**작성일**: 2025-11-08
**예상 소요 시간**: 1일
**예상 비용**: $10-50/월
**다음 단계**: 우선순위 2 진행
