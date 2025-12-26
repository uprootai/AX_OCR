# Git 변경사항 요약

> 생성일: 2025-12-26
> 기준 커밋: 94d5f77 (feat: Blueprint AI BOM v9.0)

---

## 변경 상태

```
M  blueprint-ai-bom/backend/api_server.py         # 수정됨 (staged)
 D blueprint-ai-bom/backend/routers/analysis_router.py  # 삭제됨 (unstaged)
 M blueprint-ai-bom/frontend/src/pages/WorkflowPage.tsx # 수정됨 (unstaged)
?? apply-company/                                  # 새 디렉토리 (untracked)
?? blueprint-ai-bom/backend/routers/analysis/      # 새 패키지 (untracked)
?? blueprint-ai-bom/backend/routers/longterm_router.py  # 새 파일 (untracked)
?? blueprint-ai-bom/backend/routers/midterm_router.py   # 새 파일 (untracked)
?? blueprint-ai-bom/frontend/src/pages/workflow/   # 새 디렉토리 (untracked)
```

---

## 주요 변경 내용

### 1. Backend: Analysis Router 모듈화

**기존 (1 파일)**:
```
routers/analysis_router.py  (~2,800 lines)
```

**변경 후 (5 파일 패키지 + 2 라우터)**:
```
routers/analysis/
├── __init__.py           # 패키지 export
├── core_router.py        # 프리셋, 옵션, 분석 실행
├── dimension_router.py   # 치수 관리 API
├── line_router.py        # 선 검출, 연결성 분석
├── region_router.py      # 영역 분할
└── gdt_router.py         # GD&T 파싱, 표제란 OCR

routers/midterm_router.py   # 중기 로드맵 (용접, 거칠기, 수량, 벌룬)
routers/longterm_router.py  # 장기 로드맵 (영역, 노트, 리비전, VLM)
```

### 2. Frontend: WorkflowPage 컴포넌트 분리

**기존 (1 파일)**:
```
pages/WorkflowPage.tsx  (~5,000 lines)
```

**변경 후 (모듈화)**:
```
pages/workflow/
├── index.ts                 # export
├── components/
│   ├── DetectionRow.tsx     # 검출 결과 행
│   ├── ImageModal.tsx       # 이미지 모달
│   └── WorkflowSidebar.tsx  # 사이드바
├── sections/
│   ├── ActiveFeaturesSection.tsx    # 활성화된 기능 배지
│   ├── BOMSection.tsx              # BOM 생성 섹션
│   ├── ConnectivitySection.tsx     # P&ID 연결성
│   ├── DetectionResultsSection.tsx # 심볼 검출 결과
│   ├── DimensionSection.tsx        # 치수 OCR
│   ├── DrawingInfoSection.tsx      # 도면 정보
│   ├── FinalResultsSection.tsx     # 최종 결과
│   ├── GDTSection.tsx              # GD&T 파싱
│   ├── LineDetectionSection.tsx    # 선 검출
│   ├── LongTermSection.tsx         # 장기 로드맵 섹션
│   ├── MidTermSection.tsx          # 중기 로드맵 섹션
│   ├── ReferenceDrawingSection.tsx # 참조 도면
│   ├── RelationSection.tsx         # 관계 분석
│   ├── SymbolVerificationSection.tsx # 심볼 검증
│   ├── TitleBlockSection.tsx       # 표제란 OCR
│   └── VLMClassificationSection.tsx # VLM 분류
├── config/                  # 설정
├── hooks/                   # 커스텀 훅
└── types/                   # TypeScript 타입
```

### 3. api_server.py 변경

```python
# 이전
from routers.analysis_router import router as analysis_router_api
app.include_router(analysis_router_api, tags=["Analysis"])

# 이후
from routers.analysis import core_router, dimension_router, line_router, region_router, gdt_router
app.include_router(core_router, tags=["Analysis Core"])
app.include_router(dimension_router, tags=["Dimensions"])
app.include_router(line_router, tags=["Lines & Connectivity"])
app.include_router(region_router, tags=["Regions"])
app.include_router(gdt_router, tags=["GD&T & Title Block"])
app.include_router(midterm_router_api, tags=["Mid-term Features"])
app.include_router(longterm_router_api, tags=["Long-term Features"])
```

---

## 커밋 준비 작업

### Step 1: 삭제된 파일 처리
```bash
cd /home/uproot/ax/poc/blueprint-ai-bom
git rm backend/routers/analysis_router.py
```

### Step 2: 신규 파일 추가
```bash
git add backend/routers/analysis/
git add backend/routers/midterm_router.py
git add backend/routers/longterm_router.py
git add frontend/src/pages/workflow/
```

### Step 3: 수정된 파일 추가
```bash
git add backend/api_server.py
git add backend/routers/__init__.py
git add frontend/src/pages/WorkflowPage.tsx
```

### Step 4: 커밋
```bash
git commit -m "refactor: Analysis router 모듈화 및 WorkflowPage 컴포넌트 분리

- analysis_router.py → analysis/ 패키지로 분할 (5개 모듈)
- midterm_router.py, longterm_router.py 추가 (로드맵 기능)
- WorkflowPage.tsx → workflow/ 디렉토리로 분리 (17개 섹션)
- 코드 가독성 및 유지보수성 향상

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 주의사항

1. **apply-company/** 디렉토리는 별도 프로젝트로 보임 - 이번 커밋에서 제외
2. **routers/__init__.py** 업데이트 필요 (midterm/longterm router export 추가)
3. **features 일관성 문제**는 별도 커밋으로 처리 권장

---

**작성자**: Claude Code (Opus 4.5)
