# Agent-Native Verification UI 설계

> **작성일**: 2026-02-19
> **상태**: 기획 (Planning)
> **목표**: Multimodal LLM Agent가 Human-in-the-Loop 검증을 자동 수행할 수 있는 전용 UI

---

## 1. 문제 정의

### 현재 상태

현재 검증 워크플로우는 **사람 전용 UI**에서 수행:

```
VerificationPage.tsx
┌───────────────────────────────────────────────────────────┐
│ [헤더 툴바] [모두승인] [모두반려] [BOM생성] [심볼참조]      │
│ ┌─────────────────────────┐ ┌──────────────────────────┐ │
│ │                         │ │ Detection #1  ☑ ☒        │ │
│ │   캔버스 (SVG 오버레이)  │ │ Detection #2  ☑ ☒        │ │
│ │   + 바운딩박스 전체 표시  │ │ Detection #3  ☑ ☒        │ │
│ │   + 선택 하이라이트      │ │ Detection #4  ☑ ☒        │ │
│ │                         │ │ ...                       │ │
│ └─────────────────────────┘ └──────────────────────────┘ │
│ [통계바] Total: 47 | Pending: 30 | Approved: 15 | ...     │
└───────────────────────────────────────────────────────────┘
```

**Agent가 이 UI를 처리하기 어려운 이유:**
1. 복잡한 레이아웃 — 캔버스 + 리스트 + 툴바 + 통계바 동시 존재
2. 작은 바운딩박스 — 스크린샷에서 개별 심볼 식별 어려움
3. 컨텍스트 스위칭 — 리스트 아이템 클릭 → 캔버스 이동 → 확인 → 다시 리스트
4. 동적 상태 — 승인/거부마다 UI가 실시간 변경
5. CSS 셀렉터 복잡 — 동적 생성 요소, 스크롤 위치 의존

### 핵심 질문

> "Agent가 한 장의 스크린샷을 보고 즉시 판단+행동할 수 있는 UI는?"

---

## 2. 대상 검증 작업

### 2a. 파나시아 MCP Panel (27 클래스)

| 검증 대상 | 예시 | 판단 기준 |
|-----------|------|-----------|
| 전기 부품 분류 | Circuit Breaker, SMPS, PLC CPU | 크롭 이미지 vs 참조 이미지 비교 |
| 바운딩박스 정확도 | 부품 전체가 박스 안에 있는지 | 시각적 확인 |
| 오탐 (False Positive) | 배경 노이즈가 부품으로 검출 | 크롭 이미지만으로 판단 가능 |

### 2b. P&ID 심볼 (32 클래스)

| 검증 대상 | 예시 | 판단 기준 |
|-----------|------|-----------|
| 밸브 분류 | Gate Valve vs Ball Valve vs Control Valve | 심볼 형태 비교 |
| 연결 정합성 | Valve → Pipe → Pump 연결 올바른지 | 공간 컨텍스트 필요 |
| 체크리스트 | BWMS-004: FMU-ECU 순서 | 메타데이터로 판단 가능 |

### 2c. 치수 도면 (동서기연 등)

| 검증 대상 | 예시 | 판단 기준 |
|-----------|------|-----------|
| 치수 검출 정확도 | "Ø120 +0.02/-0.01" | OCR 텍스트 vs 크롭 이미지 |
| 위치 정확도 | 치수선이 올바른 피처에 연결 | 시각적 확인 |
| 공차 해석 | H7/g6 → 기준 0/+25, 축 -9/-25 | 메타데이터로 판단 가능 |

---

## 3. 3-Level 아키텍처

### Level 1: API-Only Agent (시각 불필요)

```
Agent ←→ REST API (JSON in/out)

GET  /verification/queue/{session_id}     → 우선순위 정렬된 검증 큐
GET  /verification/stats/{session_id}     → 통계 (pending/approved/rejected)
POST /verification/verify/{session_id}    → 개별 승인/거부
POST /verification/auto-approve/{session_id} → 고신뢰 일괄 승인
POST /verification/bulk-approve/{session_id} → 선택 일괄 승인
```

**적합한 작업:**
- confidence >= 0.9 → 자동 승인 (이미 구현됨)
- 체크리스트 항목 (Pass/Fail은 rule 기반)
- 메타데이터만으로 판단 가능한 항목 (공차 해석, 태그 패턴 매칭)

**한계:**
- 실제 이미지를 보지 않으므로 오탐/미탐 판단 불가
- 바운딩박스 정확도 확인 불가

### Level 2: Visual Verification UI (팝업)

```
Agent → 팝업 페이지 열기 → 스크린샷 → Multimodal LLM 판단 → 버튼 클릭
```

**새로 만들 페이지: `/verification/agent`**

```
┌────────────────────────────────────────────────────────┐
│  검증 항목 [3/47]          class: Control Valve         │
│  confidence: 87%           priority: MEDIUM              │
│                                                          │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │                  │  │                              │  │
│  │   크롭 이미지     │  │   전체 도면 + 위치 표시      │  │
│  │   (검출 영역)     │  │   (빨간 박스 하이라이트)     │  │
│  │   400x400px      │  │   600x400px                  │  │
│  │                  │  │                              │  │
│  └──────────────────┘  └────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  참조 이미지: Control Valve                       │  │
│  │  [ref_img_1] [ref_img_2] [ref_img_3]             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────┐  ┌────────┐  ┌──────────────────────┐     │
│  │ ✅ 승인 │  │ ❌ 거부 │  │ 🔄 수정: [드롭다운 ▾] │     │
│  └────────┘  └────────┘  └──────────────────────┘     │
│                                                          │
│  [◀ 이전]                              [다음 ▶] [건너뛰기]│
└────────────────────────────────────────────────────────┘
```

**설계 원칙:**
1. **한 번에 하나** — 한 항목만 표시, 순차 처리
2. **큰 이미지** — 크롭 400x400, 전체 600x400 (스크린샷에서 명확히 보임)
3. **참조 이미지 나란히** — "이 크롭이 정말 Control Valve인가?" 비교 가능
4. **3개 큰 버튼** — 승인/거부/수정, 명확한 CSS selector
5. **진행률 표시** — "[3/47]"로 현재 위치 명확
6. **키보드 단축키** — `A`=승인, `R`=거부, `S`=건너뛰기, `→`=다음

**CSS Selector 설계 (Agent-friendly):**
```html
<button data-action="approve" id="btn-approve">승인</button>
<button data-action="reject" id="btn-reject">거부</button>
<select data-action="modify" id="select-modify">
  <option value="Gate Valve">Gate Valve</option>
  ...
</select>
<button data-action="next" id="btn-next">다음</button>
<button data-action="skip" id="btn-skip">건너뛰기</button>
```

### Level 3: Hybrid Agent (최적)

```python
# Agent 의사결정 흐름
for item in verification_queue:
    if item.confidence >= 0.9:
        # Level 1: API로 자동 승인 (시각 불필요)
        api.auto_approve(session_id)

    elif item.priority == "CRITICAL" or item.confidence < 0.7:
        # Level 2: 팝업에서 시각 검증
        navigate_to(f"/verification/agent?session={sid}&item={item.id}")
        screenshot = take_screenshot()
        decision = llm.analyze(screenshot, "이 크롭이 {class_name}인가?")
        click(decision.button)

    else:
        # Level 1: 메타데이터 기반 판단
        if item.has_reference_match:
            api.approve(session_id, item.id)
        else:
            # Level 2로 에스컬레이션
            navigate_to_visual_verification(item)
```

---

## 4. 구현 상세

### 4a. 백엔드 변경

#### 새 API 엔드포인트

```
# 기존 verification_router.py에 추가

GET /verification/agent/queue/{session_id}
  → 응답: Agent-optimized 큐 (크롭 이미지 URL + 참조 이미지 URL 포함)

GET /verification/agent/item/{session_id}/{detection_id}
  → 응답: 단일 항목 상세 (크롭 base64 + 전체 도면 base64 with highlight)

POST /verification/agent/decide/{session_id}/{detection_id}
  → 요청: { action: "approve"|"reject"|"modify", modified_class?: string }
  → 응답: { success, next_item_id, remaining_count }
```

#### 크롭 이미지 서비스

```python
# services/crop_service.py (신규)

class CropService:
    def get_detection_crop(self, session_id, detection_id, padding=20):
        """검출 영역 크롭 이미지 생성 (400x400 리사이즈)"""

    def get_context_image(self, session_id, detection_id, highlight=True):
        """전체 도면에서 검출 위치를 빨간 박스로 표시한 축소 이미지"""

    def get_reference_images(self, class_name, max_count=3):
        """클래스별 참조 이미지 반환 (class_examples/ 폴더)"""
```

### 4b. 프론트엔드 변경

#### 새 페이지: AgentVerificationPage

```
blueprint-ai-bom/frontend/src/pages/AgentVerificationPage.tsx
```

**라우트**: `/verification/agent?session={sid}&item={detection_id}`

**핵심 특성:**
- 최소 UI — 불필요한 네비게이션, 사이드바 없음
- 고정 레이아웃 — 스크린샷마다 동일한 위치에 동일한 요소
- 큰 요소 — 버튼 최소 60px 높이, 이미지 최소 400px
- 시맨틱 HTML — `data-*` 속성으로 Agent가 요소 식별 용이
- 자동 진행 — 승인/거부 후 자동으로 다음 항목 로드

**컴포넌트 구조:**
```
AgentVerificationPage
├── ProgressHeader          # [3/47] + confidence + priority badge
├── ImageComparison
│   ├── CropImage           # 검출 크롭 (400x400)
│   └── ContextImage        # 전체 도면 + 하이라이트 (600x400)
├── ReferencePanel          # 참조 이미지 3개 나란히
├── ActionButtons           # 승인/거부/수정 (큰 버튼)
└── NavigationFooter        # 이전/다음/건너뛰기
```

### 4c. P&ID 전용 뷰 (파나시아 BWMS)

P&ID 검증은 추가 정보가 필요:

```
┌────────────────────────────────────────────────────────┐
│  [밸브 검증 2/12]          tag: BWV-101                 │
│  type: Gate Valve          confidence: 92%              │
│                                                          │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │  크롭: 밸브 심볼  │  │  전체 P&ID + 위치 표시     │  │
│  └──────────────────┘  └────────────────────────────┘  │
│                                                          │
│  연결 정보:                                              │
│  ├─ 상류: Pump P-101 (process line, solid)              │
│  └─ 하류: Tank T-201 (process line, solid)              │
│                                                          │
│  체크리스트:                                             │
│  ├─ BWMS-004: FMU-ECU 순서 → ✅ Pass                   │
│  └─ BWMS-008: ECS 밸브 위치 → ⚠️ Warning               │
│                                                          │
│  ┌────────┐  ┌────────┐  ┌──────────────────────┐     │
│  │ ✅ 승인 │  │ ❌ 거부 │  │ 🔄 수정: [밸브 유형 ▾] │     │
│  └────────┘  └────────┘  └──────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

**추가 정보:**
- 연결 그래프 (상류/하류 심볼)
- 관련 체크리스트 항목 (해당 밸브에 영향 받는 rule)
- 태그 번호 + 밸브 유형 (텍스트로 명시)

### 4d. 치수 도면 전용 뷰 (동서기연 등)

```
┌────────────────────────────────────────────────────────┐
│  [치수 검증 15/51]         confidence: 78%              │
│                                                          │
│  ┌──────────────────┐  ┌────────────────────────────┐  │
│  │  크롭: 치수선     │  │  전체 도면 + 위치 표시     │  │
│  │  "Ø120 +0.02/-0.01"│ │                            │  │
│  └──────────────────┘  └────────────────────────────┘  │
│                                                          │
│  OCR 결과:                                               │
│  ├─ 값: 120.0 mm                                        │
│  ├─ 공차: +0.02 / -0.01                                 │
│  ├─ 타입: diameter                                       │
│  └─ GD&T: ⊕ 0.05 (위치도)                               │
│                                                          │
│  ┌────────┐  ┌────────┐  ┌──────────────────────┐     │
│  │ ✅ 승인 │  │ ❌ 거부 │  │ ✏️ 값 수정: [    ] │     │
│  └────────┘  └────────┘  └──────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

---

## 5. Agent 통합 패턴

### 5a. Playwright 기반 Agent

```python
# Agent 실행 예시 (Playwright MCP 사용)

async def verify_session(session_id: str):
    # Step 1: API로 통계 확인
    stats = await api_get(f"/verification/stats/{session_id}")
    print(f"Pending: {stats['pending']}, Total: {stats['total']}")

    # Step 2: 고신뢰 자동 승인 (Level 1)
    if stats['auto_approve_candidates'] > 0:
        await api_post(f"/verification/auto-approve/{session_id}")

    # Step 3: 나머지를 시각 검증 (Level 2)
    await navigate(f"http://localhost:3000/verification/agent?session={session_id}")

    while True:
        screenshot = await take_screenshot()

        # Multimodal LLM에게 판단 요청
        decision = await llm.analyze(
            image=screenshot,
            prompt="""이 검증 화면을 보고 판단하세요:
            1. 왼쪽 크롭 이미지가 표시된 클래스({class_name})에 해당하는지
            2. 오른쪽 참조 이미지와 비교하여 일치하는지
            3. 바운딩박스가 대상을 정확히 감싸는지

            응답: APPROVE / REJECT / SKIP (판단 불가시)"""
        )

        if decision == "APPROVE":
            await click("#btn-approve")
        elif decision == "REJECT":
            await click("#btn-reject")
        else:
            await click("#btn-skip")

        # 진행률 확인
        progress = await get_text("#progress-indicator")
        if "완료" in progress:
            break
```

### 5b. MCP Tool 기반 Agent (향후)

```python
# 전용 MCP Tool로 래핑 가능

tools = [
    {
        "name": "verification_get_next",
        "description": "다음 검증 항목 가져오기 (크롭 이미지 + 참조 이미지 포함)",
        "parameters": {"session_id": "string"}
    },
    {
        "name": "verification_decide",
        "description": "검증 항목에 대해 승인/거부/수정 결정",
        "parameters": {
            "session_id": "string",
            "detection_id": "string",
            "action": "approve|reject|modify",
            "modified_class": "string (optional)"
        }
    }
]
```

---

## 6. 구현 단계

### Phase 1: 백엔드 API 확장 (1일)

| 작업 | 파일 | 설명 |
|------|------|------|
| 크롭 서비스 | `services/crop_service.py` (신규) | 크롭 이미지 + 컨텍스트 이미지 생성 |
| Agent 큐 API | `routers/verification_router.py` | 크롭/참조 URL 포함한 큐 응답 |
| Agent 결정 API | `routers/verification_router.py` | 결정 + 자동 다음 항목 반환 |

### Phase 2: Agent 전용 프론트엔드 (2일)

| 작업 | 파일 | 설명 |
|------|------|------|
| 페이지 생성 | `pages/AgentVerificationPage.tsx` (신규) | 최소 UI 검증 페이지 |
| 라우팅 | `App.tsx` | `/verification/agent` 라우트 추가 |
| 이미지 컴포넌트 | `components/agent/` (신규) | CropImage, ContextImage, ReferencePanel |
| 액션 버튼 | `components/agent/ActionButtons.tsx` | 큰 버튼 + 키보드 단축키 |

### Phase 3: Agent 파이프라인 (1일)

| 작업 | 파일 | 설명 |
|------|------|------|
| Playwright 스크립트 | `scripts/agent_verify.py` (신규) | 자동 검증 스크립트 |
| 파나시아 테스트 | 수동 테스트 | MCP Panel 27클래스 검증 E2E |

### Phase 4: P&ID/치수 전용 뷰 (1일)

| 작업 | 파일 | 설명 |
|------|------|------|
| P&ID 연결 뷰 | `AgentVerificationPage.tsx` | 연결 정보 + 체크리스트 표시 |
| 치수 전용 뷰 | `AgentVerificationPage.tsx` | OCR 결과 + 공차 표시 |
| 뷰 자동 전환 | 자동 | drawing_type에 따라 적절한 뷰 표시 |

---

## 7. 기대 효과

### 정량적

| 지표 | 현재 (수동) | Level 1 (API) | Level 2 (팝업) | Level 3 (하이브리드) |
|------|------------|---------------|----------------|---------------------|
| 파나시아 27심볼 | ~10분 | ~10초 | ~2분 | ~30초 |
| 동서기연 51치수/세션 | ~8분 | ~5초 | ~3분 | ~1분 |
| P&ID 47심볼 | ~15분 | ~15초 | ~4분 | ~1.5분 |
| Agent 정확도 | N/A | ~70% (시각 없음) | ~95% (시각) | ~95% |

### 정성적

1. **Agent Scalability** — 세션 수가 100+로 늘어도 Agent가 자동 처리
2. **일관된 품질** — 사람의 피로/실수 없이 일관된 기준으로 검증
3. **Active Learning 데이터** — Agent의 승인/거부 패턴을 학습 데이터로 활용
4. **24시간 운영** — 야간에도 Agent가 검증 수행, 아침에 결과만 확인

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| LLM 오판 (False Approve) | 불량 부품 포함 | confidence < 0.7 항목은 반드시 사람 검증, Agent 결과에 "agent_verified" 플래그 |
| LLM 비용 (토큰) | 스크린샷당 ~1000 토큰 | Level 1으로 90%+ 자동 승인 후 나머지만 Level 2 |
| UI 변경 시 Agent 깨짐 | 셀렉터/레이아웃 불일치 | data-* 속성 기반 셀렉터, 레이아웃 고정 |
| 크롭만으로 판단 불가 | 공간 맥락 부족 | 전체 도면 컨텍스트 이미지 함께 제공 |

---

## 9. 연관 시스템

| 시스템 | 관계 |
|--------|------|
| `VerificationPage.tsx` (기존) | 사람용 UI, 유지. Agent UI는 별도 |
| `VerificationQueue.tsx` (기존) | Active Learning 큐 로직 재사용 |
| `active_learning_service.py` | 우선순위 로직 재사용 |
| `verification_router.py` | 기존 API 확장 |
| `class_examples/`, `class_examples_pid/` | 참조 이미지 소스 |
| BlueprintFlow VerificationQueue 노드 | Gateway executor로 Agent 워크플로우 트리거 가능 |

---

## 10. 설계 결정 (확정)

| # | 질문 | 결정 | 근거 |
|---|------|------|------|
| 1 | Agent 결과 신뢰 수준 | **사람 최종 확인** | Agent는 추천자 역할. "agent_verified" 플래그로 구분, 사람이 최종 확정. 거부/수정 건만 집중 리뷰하면 되므로 사람의 부담은 크게 줄어듦 |
| 2 | 수정(Modify) 범위 | **승인 + 거부 + 수정 모두 가능** | Agent가 클래스 변경까지 수행. 바운딩박스 미세 조정은 드롭다운 선택 수준으로 단순화 |
| 3 | 검증 단위 | **세션 단위** | 한 세션(도면 1장) 검증 완료 → 다음 세션. 프로젝트 전체를 한번에 돌리되 세션 경계는 유지 |
| 4 | Agent 모델 | **Sonnet 기본** | 시각 인식 충분, 비용 효율적. CRITICAL 항목도 Sonnet으로 처리 (사람이 최종 확인하므로) |
| 5 | Agent 인터페이스 | **MCP Tool + Playwright 둘 다** | MCP Tool 기본 (빠름), 시각 확인 필요시 Playwright로 에스컬레이션 |

### 결정에 따른 워크플로우

```
[Agent 실행]
    │
    ├─ MCP Tool: GET /agent/queue/{session_id}
    │   → 크롭 이미지 + 참조 이미지 + 메타데이터를 직접 수신
    │   → Sonnet이 이미지 분석 후 승인/거부/수정 결정
    │   → MCP Tool: POST /agent/decide (결과 저장, flag: agent_verified)
    │
    ├─ 판단 불가 시 → Playwright로 에스컬레이션
    │   → 브라우저에서 /verification/agent 페이지 열기
    │   → 스크린샷 기반 시각 검증
    │
    └─ 세션 완료 → 다음 세션으로 이동

[사람 리뷰]
    │
    ├─ Agent 결과 대시보드 확인
    │   → agent_verified 항목 중 거부/수정 건만 집중 리뷰
    │   → 승인 건은 빠르게 스캔 후 최종 확정
    │
    └─ 최종 확정 → BOM 생성 진행
```

### 사람 리뷰 UI 고려사항

Agent가 처리한 결과를 사람이 효율적으로 검토할 수 있는 뷰 필요:
- Agent 승인 건: 썸네일 격자로 한눈에 스캔 (이상 없으면 일괄 확정)
- Agent 거부 건: 거부 사유와 함께 나열 (사람이 동의/복원 결정)
- Agent 수정 건: 원본 클래스 vs 수정 클래스 비교 (사람이 확인)
- 통계: Agent 정확도 추적 (시간이 지날수록 신뢰도 데이터 축적)

---

*이 문서는 구현 전 기획 단계입니다. Phase 1부터 순차 진행합니다.*
