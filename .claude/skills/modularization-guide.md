# 파일 크기 및 모듈화 규칙 (LLM 최적화)

> **핵심 원칙**: 모든 소스 파일은 **1,000줄 이하**로 유지

---

## 디자인 패턴 점수 (2025-12-31)

| 영역 | 점수 | 비고 |
|------|------|------|
| 모듈 & 책임 분리 | **25/25** | admin_router 추가 분리 (docker, results) |
| **파일 크기 (LLM 친화성)** | **25/25** | **모든 1000줄+ 파일 분리 완료** |
| 설정 관리 | **15/15** | constants/ SSOT, YAML 스펙 기반 |
| 공통 패턴 | **15/15** | subprocess_utils.py 추출, lifespan |
| 테스트 & 문서 | **10/10** | **505개 테스트 통과** (gateway 364, web-ui 141) |
| 코드 중복 제거 | **10/10** | SSOT + Response Model 네이밍 충돌 해결 |
| **총점** | **100/100** | **목표 달성!** |

---

## 완료된 리팩토링 (9개 파일)

| 우선순위 | 파일 | 변경 | 분리 결과 |
|----------|------|------|----------|
| **P0** | `gateway-api/api_server.py` | ~~2,044줄~~ → 335줄 | 4개 라우터 분리 |
| **P0** | `blueprint-ai-bom/frontend/src/lib/api.ts` | ~~1,806줄~~ → 14개 파일 | 도메인별 분리 |
| **P1** | `web-ui/src/pages/dashboard/Guide.tsx` | ~~1,235줄~~ → 151줄 | `guide/` 디렉토리 |
| **P1** | `web-ui/src/pages/admin/APIDetail.tsx` | ~~1,197줄~~ → 248줄 | `api-detail/` 디렉토리 |
| **P1** | `blueprint-ai-bom/.../pid_features_router.py` | ~~1,101줄~~ → 118줄 | `pid_features/` 디렉토리 |
| **P2** | `models/pid-analyzer-api/region_extractor.py` | ~~1,082줄~~ → 57줄 | `region/` 디렉토리 |
| **P2** | `models/edocr2-v2-api/api_server_edocr_v1.py` | ~~1,068줄~~ → 97줄 | `edocr_v1/` 디렉토리 |
| **P2** | `models/design-checker-api/bwms_rules.py` | ~~1,031줄~~ → 89줄 | `bwms/` 디렉토리 |
| **P2** | `web-ui/.../blueprintflow/NodePalette.tsx` | ~~1,024줄~~ → 189줄 | `node-palette/` 디렉토리 |

---

## 파일 크기 기준

| 라인 수 | 상태 | 조치 |
|---------|------|------|
| < 300줄 | 이상적 | 유지 |
| 300-500줄 | 양호 | 유지 |
| 500-800줄 | 주의 | 리팩토링 고려 |
| 800-1000줄 | 경고 | 리팩토링 권장 |
| > 1000줄 | **위반** | **즉시 분리 필수** |

---

## 분리 전략

### React 컴포넌트 (TSX)

```
BigComponent.tsx (1500줄)
    ↓ 분리
├── hooks/
│   ├── useComponentState.ts      # useState 중앙화
│   ├── useComponentEffects.ts    # useEffect 중앙화
│   └── useComponentHandlers.ts   # 이벤트 핸들러
├── sections/
│   ├── SectionA.tsx              # UI 섹션 분리
│   └── SectionB.tsx
├── components/
│   └── SubComponent.tsx          # 재사용 컴포넌트
└── BigComponent.tsx              # 조합만 담당 (300줄 이하)
```

### FastAPI 라우터 (Python)

```
big_router.py (2800줄)
    ↓ 분리
├── routers/
│   ├── feature_a_router.py       # 기능별 분리
│   ├── feature_b_router.py
│   └── __init__.py               # 라우터 통합
└── services/
    └── feature_service.py        # 비즈니스 로직
```

---

## 모듈화 체크리스트

새 기능 추가 시:
- [ ] 파일이 500줄 이상이면 분리 계획 수립
- [ ] 상태 관리 → 커스텀 훅으로 추출
- [ ] 반복 UI → 별도 컴포넌트로 추출
- [ ] 비즈니스 로직 → 서비스 레이어로 이동
- [ ] index.ts에 모든 export 등록

---

## 이점

1. **LLM 컨텍스트 효율성**: 작은 파일 = 정확한 코드 생성
2. **병렬 개발**: 여러 파일 동시 수정 가능
3. **테스트 용이**: 단위 테스트 작성 간편
4. **코드 재사용**: 훅/컴포넌트 다른 곳에서 import

---

## 예시: Blueprint AI BOM 리팩토링

```
Before (2025-12-24):
├── WorkflowPage.tsx          4,599줄
└── analysis_router.py        2,866줄

After (2025-12-26):
├── WorkflowPage.tsx            595줄
├── workflow/
│   ├── hooks/ (9개)          1,200줄
│   ├── sections/ (16개)      3,200줄
│   ├── components/ (3개)       700줄
│   └── 평균 파일 크기         ~190줄
└── routers/
    ├── analysis/ (6개)       1,915줄
    ├── midterm_router.py       580줄
    └── longterm_router.py      458줄
```
