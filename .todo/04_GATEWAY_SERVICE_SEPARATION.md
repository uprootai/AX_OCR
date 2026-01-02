# Gateway 서비스 분리 계획

> pid_overlay → pid-composer-api 분리와 같은 패턴으로
> 다른 Gateway 서비스도 분리 검토

---

## 분리 완료

### PID Overlay → PID Composer API
- **포트**: 5021
- **분리 이유**: 이미지 처리 로직 복잡, 별도 확장 필요
- **결과**: Gateway 코드 600줄+ 제거

---

## 분리 후보 서비스

### 1. VL Service (우선순위: HIGH)
**현재 위치**: `gateway-api/services/vl_service.py`
**분리 이유**:
- LLM API 호출 로직 복잡
- 멀티 프로바이더 지원 (OpenAI, Anthropic, Ollama)
- 프롬프트 관리 필요
- GPU 리소스 사용 가능

**예상 포트**: 5025 (vl-orchestrator-api)

```
models/vl-orchestrator-api/
├── api_server.py
├── services/
│   ├── openai_service.py
│   ├── anthropic_service.py
│   └── ollama_service.py
├── prompts/
│   └── pid_analysis.py
└── routers/
    └── vl_router.py
```

**작업 항목**:
- [ ] 현재 vl_service.py 분석
- [ ] 멀티 프로바이더 추상화
- [ ] 별도 마이크로서비스 생성
- [ ] Gateway에서 호출 패턴 변경

---

### 2. Ensemble Service (우선순위: MEDIUM)
**현재 위치**: `gateway-api/services/ensemble_service.py`
**분리 이유**:
- 다중 OCR 결과 병합 로직
- 가중 투표 알고리즘
- 독립적으로 테스트 가능

**예상 포트**: 5026 (ocr-ensemble-orchestrator-api)

```
models/ocr-ensemble-orchestrator-api/
├── api_server.py
├── services/
│   ├── voting_service.py
│   ├── merging_service.py
│   └── confidence_scorer.py
└── routers/
    └── ensemble_router.py
```

---

### 3. Quote Service (우선순위: LOW)
**현재 위치**: `gateway-api/services/quote_service.py`
**분리 이유**:
- 비즈니스 로직 분리
- 가격 정책 독립 관리
- 외부 ERP 연동 가능

**예상 포트**: 5027 (quote-api)

---

## 분리하지 않을 서비스

### OCR Service
**이유**: 단순 HTTP 호출 래퍼, 분리 가치 없음

### YOLO Service
**이유**: 단순 HTTP 호출 래퍼, 분리 가치 없음

### Tolerance Service
**이유**: 로직이 단순, skinmodel-api가 이미 분리됨

---

## 분리 패턴 가이드

### Step 1: 서비스 분석
```bash
# 코드 라인 수 확인
wc -l gateway-api/services/{service}_service.py

# 의존성 확인
grep -n "import\|from" gateway-api/services/{service}_service.py
```

### Step 2: 마이크로서비스 생성
1. `models/{service}-api/` 디렉토리 생성
2. FastAPI 앱 구조 생성
3. 기존 로직 이전
4. 테스트 작성

### Step 3: Gateway 수정
```python
# 기존
from services.{service}_service import some_function

# 변경
async def call_{service}_api(data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://{service}-api:{PORT}/api/v1/process",
            json=data
        )
        return response.json()
```

### Step 4: 통합
1. docker-compose.yml 추가
2. API 스펙 YAML 생성
3. nodeDefinitions 업데이트
4. CLAUDE.md 업데이트

---

## 분리 결정 기준

| 기준 | 분리 권장 | 유지 권장 |
|------|----------|----------|
| 코드 라인 | 200줄 이상 | 100줄 미만 |
| 외부 의존성 | 많음 (ML, API) | 적음 |
| 리소스 사용 | GPU/CPU 집중 | 경량 |
| 확장 필요성 | 독립 확장 필요 | Gateway와 동일 |
| 재사용성 | 다른 서비스에서 호출 | Gateway 전용 |

---

## 일정 및 우선순위

| 서비스 | 우선순위 | 예상 작업량 | 비고 |
|--------|----------|-------------|------|
| VL Orchestrator | P1 | 1일 | LLM 멀티 프로바이더 |
| OCR Ensemble Orchestrator | P2 | 0.5일 | 투표 로직 분리 |
| Quote API | P3 | 0.5일 | 비즈니스 로직 |

---

## Gateway 경량화 목표

| 항목 | 현재 | 목표 |
|------|------|------|
| services/ 파일 수 | 8개 | 4개 |
| 총 코드 라인 | ~2000줄 | ~1000줄 |
| 역할 | 오케스트레이션 + 비즈니스 로직 | 순수 오케스트레이션 |
