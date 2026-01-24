# Blueprint AI BOM - Phase 2/3 프로젝트 아키텍처 설계

> **작성일**: 2026-01-24
> **상태**: 설계 중
> **목표**: 고객사별 프로젝트 관리 + 템플릿 기반 워크플로우

---

## 1. 개요

### 1.1 현재 문제점

```
현재: 도면 1장 = 빌더에서 워크플로우 구성 1회
      → 파나시아 도면 100장 = 같은 설정 100번 반복
```

### 1.2 목표 상태

```
Phase 3: 프로젝트 템플릿 1회 생성 (빌더)
         → 도면 N장 일괄 업로드 (BOM 대시보드)
         → 템플릿 자동 적용 → 세션 N개 자동 생성
```

---

## 2. 핵심 개념

### 2.1 엔티티 관계

```
┌─────────────┐
│   Project   │ ← 고객사/프로젝트 단위
├─────────────┤
│ project_id  │
│ name        │
│ customer    │
│ template_id │────┐
│ gt_folder   │    │
│ ref_folder  │    │
└─────────────┘    │
       │           │
       │ 1:N       │ 1:1
       ▼           ▼
┌─────────────┐  ┌─────────────┐
│   Session   │  │  Template   │ ← 빌더에서 생성
├─────────────┤  ├─────────────┤
│ session_id  │  │ template_id │
│ project_id  │──│ name        │
│ template_id │  │ model_type  │
│ filename    │  │ features[]  │
│ detections  │  │ parameters  │
│ ...         │  │ workflow    │ ← 노드/엣지 정보
└─────────────┘  └─────────────┘
```

### 2.2 용어 정의

| 용어 | 설명 | 예시 |
|------|------|------|
| **Project** | 고객사 또는 프로젝트 단위 | "파나시아 BWMS", "DSE Bearing" |
| **Template** | 빌더에서 생성한 워크플로우 템플릿 | "P&ID 심볼검출 + GT비교" |
| **Session** | 도면 1장의 분석 세션 | "drawing_001.png 분석" |

---

## 3. 스키마 설계

### 3.1 Project 스키마

```python
# backend/schemas/project.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    """프로젝트 생성 요청"""
    name: str = Field(..., description="프로젝트명", example="파나시아 BWMS")
    customer: str = Field(..., description="고객사명", example="파나시아")
    description: Optional[str] = Field(None, description="프로젝트 설명")
    default_template_id: Optional[str] = Field(None, description="기본 템플릿 ID")

class ProjectResponse(BaseModel):
    """프로젝트 응답"""
    project_id: str
    name: str
    customer: str
    description: Optional[str] = None
    default_template_id: Optional[str] = None

    # 폴더 경로
    gt_folder: Optional[str] = None          # GT 라벨 폴더
    reference_folder: Optional[str] = None   # 참조도면 폴더

    # 통계
    session_count: int = 0
    completed_count: int = 0

    # 메타
    created_at: datetime
    updated_at: datetime

class ProjectDetail(ProjectResponse):
    """프로젝트 상세 (세션 목록 포함)"""
    sessions: List[dict] = []  # SessionResponse 목록
    template: Optional[dict] = None  # TemplateResponse
```

### 3.2 Template 스키마

```python
# backend/schemas/template.py

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TemplateNode(BaseModel):
    """워크플로우 노드"""
    id: str
    type: str                    # "yolo", "edocr2", "skinmodel" 등
    position: Dict[str, float]   # {"x": 100, "y": 200}
    data: Dict[str, Any]         # 노드별 파라미터

class TemplateEdge(BaseModel):
    """워크플로우 엣지"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None

class TemplateCreate(BaseModel):
    """템플릿 생성 요청 (빌더에서 저장)"""
    name: str = Field(..., description="템플릿명", example="P&ID 심볼검출 템플릿")
    description: Optional[str] = None

    # 검출 설정
    model_type: str = Field(..., description="YOLO 모델 타입", example="pid_symbol")

    # 활성화된 기능
    features: List[str] = Field(
        default_factory=list,
        description="활성화된 기능 목록",
        example=["symbol_detection", "gt_comparison", "dimension_ocr"]
    )

    # 워크플로우 정의 (빌더에서 생성)
    nodes: List[TemplateNode] = Field(default_factory=list)
    edges: List[TemplateEdge] = Field(default_factory=list)

    # 각 노드별 파라미터 (옵션)
    node_parameters: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="노드 ID별 파라미터 오버라이드"
    )

class TemplateResponse(BaseModel):
    """템플릿 응답"""
    template_id: str
    name: str
    description: Optional[str] = None
    model_type: str
    features: List[str]

    # 워크플로우 요약
    node_count: int = 0
    edge_count: int = 0

    # 사용 통계
    usage_count: int = 0  # 이 템플릿으로 생성된 세션 수

    created_at: datetime
    updated_at: datetime

class TemplateDetail(TemplateResponse):
    """템플릿 상세 (워크플로우 포함)"""
    nodes: List[TemplateNode] = []
    edges: List[TemplateEdge] = []
    node_parameters: Dict[str, Dict[str, Any]] = {}
```

### 3.3 Session 스키마 확장

```python
# backend/schemas/session.py (확장)

class SessionCreate(BaseModel):
    """세션 생성 요청"""
    filename: str
    file_path: str
    drawing_type: DrawingType = DrawingType.AUTO

    # Phase 2 추가 필드
    project_id: Optional[str] = None      # 프로젝트 ID
    template_id: Optional[str] = None     # 템플릿 ID (없으면 프로젝트 기본값)

class SessionResponse(BaseModel):
    """세션 응답"""
    session_id: str
    filename: str
    file_path: str
    status: SessionStatus

    # Phase 2 추가 필드
    project_id: Optional[str] = None
    project_name: Optional[str] = None    # 조인된 프로젝트명
    template_id: Optional[str] = None
    template_name: Optional[str] = None   # 조인된 템플릿명
    model_type: Optional[str] = None      # 템플릿에서 상속

    # 기존 필드
    drawing_type: DrawingType = DrawingType.AUTO
    features: List[str] = []
    detection_count: int = 0
    # ...
```

---

## 4. API 엔드포인트 설계

### 4.1 Project API

```python
# backend/routers/project_router.py

@router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """프로젝트 생성"""
    pass

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(customer: Optional[str] = None):
    """프로젝트 목록 조회"""
    pass

@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str):
    """프로젝트 상세 조회 (세션 목록 포함)"""
    pass

@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, updates: ProjectUpdate):
    """프로젝트 수정"""
    pass

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, delete_sessions: bool = False):
    """프로젝트 삭제"""
    pass

@router.post("/projects/{project_id}/upload-batch")
async def upload_batch(
    project_id: str,
    files: List[UploadFile],
    template_id: Optional[str] = None  # 없으면 프로젝트 기본 템플릿
):
    """도면 일괄 업로드 → 세션 일괄 생성"""
    pass

@router.post("/projects/{project_id}/gt")
async def upload_project_gt(project_id: str, files: List[UploadFile]):
    """프로젝트 GT 일괄 업로드"""
    pass
```

### 4.2 Template API

```python
# backend/routers/template_router.py

@router.post("/templates", response_model=TemplateResponse)
async def create_template(template: TemplateCreate):
    """템플릿 생성 (빌더에서 호출)"""
    pass

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(model_type: Optional[str] = None):
    """템플릿 목록 조회"""
    pass

@router.get("/templates/{template_id}", response_model=TemplateDetail)
async def get_template(template_id: str):
    """템플릿 상세 조회 (워크플로우 포함)"""
    pass

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, updates: TemplateUpdate):
    """템플릿 수정"""
    pass

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """템플릿 삭제 (사용 중인 세션 있으면 경고)"""
    pass

@router.post("/templates/{template_id}/duplicate")
async def duplicate_template(template_id: str, new_name: str):
    """템플릿 복제"""
    pass
```

---

## 5. UI 변경점

### 5.1 BlueprintFlow Builder 변경

#### 현재 → Phase 3

```
현재:
┌─────────────────────────────────────┐
│  [실행]                              │
│  → 세션 생성 → BOM 페이지 이동        │
└─────────────────────────────────────┘

Phase 3:
┌─────────────────────────────────────┐
│  [실행]  [템플릿으로 저장]            │
│           ↓                         │
│     ┌─────────────────────┐         │
│     │ 템플릿명: [       ] │         │
│     │ 프로젝트: [선택  ▼] │         │
│     │ [저장] [취소]       │         │
│     └─────────────────────┘         │
└─────────────────────────────────────┘
```

#### 새로운 컴포넌트

```typescript
// frontend/src/components/SaveTemplateModal.tsx

interface SaveTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflow: {
    nodes: Node[];
    edges: Edge[];
  };
  onSave: (template: TemplateCreate) => Promise<void>;
}
```

### 5.2 Blueprint AI BOM 대시보드 변경

#### 새로운 페이지: 프로젝트 목록

```
┌─────────────────────────────────────────────────────────────────┐
│  📁 프로젝트 관리                              [+ 새 프로젝트]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 📁 파나시아 BWMS                                         │  │
│  │ 템플릿: P&ID 심볼검출 | 도면: 15장 | 완료: 12장          │  │
│  │ [열기] [설정] [삭제]                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 📁 DSE Bearing                                           │  │
│  │ 템플릿: 기계도면 분석 | 도면: 94장 | 완료: 0장           │  │
│  │ [열기] [설정] [삭제]                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 새로운 페이지: 프로젝트 상세

```
┌─────────────────────────────────────────────────────────────────┐
│  📁 파나시아 BWMS                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [📤 도면 업로드]  [🏷️ GT 관리]  [📚 참조도면]  [⚙️ 설정]       │
│                                                                 │
│  ── 진행 현황 ──                                                │
│  ┌─────────┬─────────┬─────────┬─────────┐                     │
│  │ 전체    │ 대기    │ 진행중  │ 완료    │                     │
│  │   15    │    3    │    2    │   10    │                     │
│  └─────────┴─────────┴─────────┴─────────┘                     │
│                                                                 │
│  ── 세션 목록 ──                                                │
│  ┌───┬────────────────┬──────────┬───────────┬────────┐        │
│  │ # │ 파일명          │ 상태     │ 검출/승인 │ 액션   │        │
│  ├───┼────────────────┼──────────┼───────────┼────────┤        │
│  │ 1 │ drawing_001.png│ ✅ 완료  │  25 / 23  │ [보기] │        │
│  │ 2 │ drawing_002.png│ 🔄 검증중│  18 / 10  │ [계속] │        │
│  │ 3 │ drawing_003.png│ ⏳ 대기  │   0 / 0   │ [시작] │        │
│  └───┴────────────────┴──────────┴───────────┴────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. 데이터 마이그레이션

### 6.1 기존 세션 처리

```python
# 마이그레이션 스크립트

def migrate_sessions_to_projects():
    """기존 세션을 프로젝트 구조로 마이그레이션"""

    # 1. 기본 프로젝트 생성 (미분류)
    default_project = create_project(name="미분류", customer="기타")

    # 2. 기존 세션에 project_id 할당
    for session in get_all_sessions():
        # 파일명 패턴으로 프로젝트 추정
        if "panasia" in session.filename.lower():
            project_id = "panasia"
        elif "dse" in session.filename.lower():
            project_id = "dsebearing"
        else:
            project_id = default_project.project_id

        update_session(session.session_id, {"project_id": project_id})
```

### 6.2 하위 호환성

```python
# project_id가 없는 세션도 정상 동작
class SessionCreate(BaseModel):
    project_id: Optional[str] = None  # Optional 유지
    template_id: Optional[str] = None
```

---

## 7. 구현 우선순위

### Phase 2A (기본 구조)
1. [ ] Project 스키마 및 서비스
2. [ ] Template 스키마 및 서비스
3. [ ] Session 스키마 확장
4. [ ] 기본 API 엔드포인트

### Phase 2B (빌더 통합)
5. [ ] 빌더: "템플릿으로 저장" 버튼
6. [ ] 빌더: 템플릿 목록 조회/불러오기

### Phase 3A (BOM 대시보드)
7. [ ] 프로젝트 목록 페이지
8. [ ] 프로젝트 상세 페이지
9. [ ] 도면 일괄 업로드

### Phase 3B (고급 기능)
10. [ ] 프로젝트별 GT 관리
11. [ ] 프로젝트별 참조도면 관리
12. [ ] 프로젝트 통계 대시보드

---

## 8. 참고

### 8.1 관련 파일

| 파일 | 역할 |
|------|------|
| `backend/schemas/session.py` | 세션 스키마 (확장 대상) |
| `backend/services/session_service.py` | 세션 서비스 (확장 대상) |
| `frontend/src/pages/WorkflowPage.tsx` | 워크플로우 페이지 |
| `web-ui/src/pages/blueprintflow/` | 빌더 페이지 |

### 8.2 의존성

- Phase 2는 현재 시스템과 독립적으로 추가 가능
- Phase 3는 Phase 2 완료 후 진행
- 하위 호환성 유지 (기존 세션 정상 동작)

---

*작성: Claude Code*
*최종 업데이트: 2026-01-24*
