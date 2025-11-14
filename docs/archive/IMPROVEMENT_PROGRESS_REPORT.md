# 📊 개선 작업 진행 현황

**생성 일시**: 2025-11-08
**평가 점수**: 82/100점 (A-) → 목표: 90/100점 (A)

---

## ✅ 완료된 작업 (자동화)

### 우선순위 1
- [x] **eDOCr2 v2 복구**: 정상 작동 확인 (port 5002, GPU 사용)
- [x] **TODO 구조**: 6개 가이드 문서 작성
  - PRIORITY_1_GDT_DRAWINGS.md
  - PRIORITY_1_VL_API_KEYS.md
  - PRIORITY_2_SKIN_MODEL_DATA.md
  - PRIORITY_2_SECURITY_POLICY.md
  - PRIORITY_3_GPU_SETUP.md
  - PRIORITY_3_PRODUCTION.md

### 준비 완료
- [x] VL 전략 구조 (.env 템플릿)
- [x] 테스트 스크립트 구조
- [x] 보안 설정 템플릿
- [x] GPU 설정 가이드

---

## 🔴 사용자 작업 필요 (우선순위 1 - 1-2주)

### 1. GD&T 도면 수집 📁
**목적**: GD&T Recall 0% → 75%

**작업**:
```bash
# 1. 도면 수집 (10개 이상)
mkdir -p /home/uproot/ax/poc/test_data/gdt_drawings
cp /path/to/gdt/drawings/*.pdf /home/uproot/ax/poc/test_data/gdt_drawings/

# 2. 가이드 참고
cat TODO/PRIORITY_1_GDT_DRAWINGS.md
```

**예상 시간**: 2-3일
**성공 기준**: GD&T 심볼 명확한 도면 10개 이상

---

### 2. VL API 키 발급 🔑
**목적**: Dimension Recall 50% → 90%

**작업**:
```bash
# 1. OpenAI 또는 Anthropic API 키 발급
# 가이드: TODO/PRIORITY_1_VL_API_KEYS.md

# 2. .env 파일 생성
cat > /home/uproot/ax/poc/.env << 'ENV'
OPENAI_API_KEY=sk-proj-여기에-실제-키-입력
OPENAI_MODEL=gpt-4o
VL_PROVIDER=openai
ENV

chmod 600 /home/uproot/ax/poc/.env

# 3. Docker 재시작
docker-compose restart edocr2-api-v1
```

**예상 시간**: 1일
**예상 비용**: $10-50/월
**성공 기준**: VL 전략 테스트 성공

---

## 🟡 사용자 작업 필요 (우선순위 2 - 2-4주)

### 3. Skin Model 학습 데이터 📊
**작업**: TODO/PRIORITY_2_SKIN_MODEL_DATA.md 참조
**예상 시간**: 2-4주
**필요 데이터**: 레이블링된 도면 1,000개 이상

### 4. 보안 정책 결정 🔒
**작업**: TODO/PRIORITY_2_SECURITY_POLICY.md 참조
**예상 시간**: 1-2일
**결정 사항**: 인증 방식, Rate limit, CORS, HTTPS

---

## 🟢 사용자 작업 필요 (우선순위 3 - 1-2개월)

### 5. GPU 하드웨어 설정 🖥️
**작업**: TODO/PRIORITY_3_GPU_SETUP.md 참조
**예상 시간**: 1-2일
**효과**: 처리 시간 3-4배 향상 (45초 → 12초)

### 6. 프로덕션 배포 🚀
**작업**: TODO/PRIORITY_3_PRODUCTION.md 참조
**예상 시간**: 3-5일
**목표**: 99.9% Uptime

---

## 📈 예상 점수 향상

| 작업 완료 후 | 점수 | 등급 | 주요 개선 |
|-------------|------|------|----------|
| **현재** | 82점 | A- | - |
| **우선순위 1 완료** | 88점 | A | GD&T 75%, Dim 90% |
| **우선순위 2 완료** | 92점 | A | 보안, Skin Model |
| **우선순위 3 완료** | 95점 | A+ | GPU, 모니터링 |

---

## 🎯 빠른 시작 가이드

### 1단계: 우선순위 1 시작 (즉시)

```bash
# GD&T 도면 확인
ls /home/uproot/ax/reference/02.\ 수요처\ 및\ 도메인\ 자료/2.\ 도면\(샘플\)/

# 가이드 열기
cat TODO/PRIORITY_1_GDT_DRAWINGS.md
cat TODO/PRIORITY_1_VL_API_KEYS.md
```

### 2단계: API 키 발급 (1일)

1. https://platform.openai.com/api-keys 접속
2. API 키 발급
3. .env 파일 생성 (위 참조)
4. 서비스 재시작

### 3단계: 테스트 (즉시)

```bash
# VL 전략 테스트
curl -X POST http://localhost:5001/api/v1/ocr/enhanced \
  -F "file=@test.pdf" \
  -F "strategy=vl"

# 결과 확인
# dimensions_count > 11 이면 성공!
```

---

## 📞 지원

### 문서 위치
- 전체 TODO: `/home/uproot/ax/poc/TODO/`
- 가이드: `/home/uproot/ax/poc/TODO/PRIORITY_*.md`
- 스크립트: `/home/uproot/ax/poc/TODO/scripts/`

### 질문/이슈
각 TODO 파일 내 "트러블슈팅" 섹션 참조

---

**다음 단계**: 우선순위 1 작업 시작 → GD&T 도면 수집 + VL API 키 발급
