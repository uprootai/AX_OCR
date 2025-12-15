# Blueprint AI BOM - 구현 로드맵

> **목표**: Streamlit → React + FastAPI 전환
> **총 예상 기간**: 13일

---

## Phase 1: 백엔드 API 분리 (3일)

### Day 1: 프로젝트 구조 생성

```bash
# 디렉토리 구조 생성
mkdir -p backend/{services,routers,schemas}
mkdir -p frontend/src/{pages,components,hooks,store,types}
mkdir -p config
mkdir -p legacy
```

**작업 목록**:
- [ ] `backend/` 디렉토리 구조 생성
- [ ] `backend/requirements.txt` 작성
- [ ] `backend/api_server.py` 기본 FastAPI 앱 생성
- [ ] 레거시 코드를 `legacy/`로 이동

### Day 2: 검출 서비스 분리

**소스**: `utils/detection.py` (442 LOC)

```python
# backend/services/detection_service.py

class DetectionService:
    async def detect(self, image: bytes, config: DetectionConfig) -> list[Detection]:
        """YOLO 검출 실행"""
        pass

    async def validate_detections(self, detections: list[Detection]) -> list[Detection]:
        """중복 제거 및 NMS"""
        pass
```

**API 엔드포인트**:
```python
# backend/routers/detection_router.py

@router.post("/detect")
async def detect_symbols(file: UploadFile, config: DetectionConfig):
    pass

@router.post("/detect/batch")
async def detect_batch(files: list[UploadFile], config: DetectionConfig):
    pass
```

### Day 3: BOM 서비스 분리

**소스**: `utils/bom_generator.py` (138 LOC)

```python
# backend/services/bom_service.py

class BOMService:
    async def create_bom(self, detections: list[Detection]) -> BOMData:
        """검증된 검출 결과로 BOM 생성"""
        pass

    async def export_excel(self, bom: BOMData) -> bytes:
        """Excel 파일 생성"""
        pass

    async def export_pdf(self, bom: BOMData) -> bytes:
        """PDF 보고서 생성"""
        pass
```

**API 엔드포인트**:
```python
# backend/routers/bom_router.py

@router.post("/bom/create")
async def create_bom(session_id: str):
    pass

@router.get("/bom/export/{format}")
async def export_bom(session_id: str, format: str):
    pass
```

---

## Phase 2: React 프론트엔드 (7일)

### Day 4-5: 프로젝트 설정 및 기본 구조

```bash
cd blueprint-ai-bom
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-konva konva @use-gesture/react zustand axios tailwindcss
```

**작업 목록**:
- [ ] Vite + React + TypeScript 프로젝트 생성
- [ ] TailwindCSS 설정
- [ ] 라우팅 설정 (react-router-dom)
- [ ] API 클라이언트 설정 (axios)
- [ ] Zustand 스토어 기본 구조

**파일 구조**:
```
frontend/src/
├── pages/
│   ├── Upload.tsx
│   ├── Processing.tsx
│   ├── Verification.tsx
│   └── Results.tsx
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   └── Layout.tsx
│   ├── upload/
│   │   └── FileDropZone.tsx
│   └── common/
│       ├── Button.tsx
│       └── Loading.tsx
├── store/
│   └── sessionStore.ts
├── lib/
│   └── api.ts
└── types/
    └── index.ts
```

### Day 6-7: 이미지 뷰어 + 바운딩 박스

**소스**: `utils/visualization.py`, `utils/ui_verification.py`

**컴포넌트**:
```typescript
// frontend/src/components/verification/ImageViewer.tsx
- Konva Stage + Layer
- 이미지 로드 및 표시
- 줌/팬 기능

// frontend/src/components/verification/BoundingBox.tsx
- 개별 바운딩 박스 렌더링
- 선택 상태 표시
- 드래그 핸들러

// frontend/src/components/verification/BoxEditor.tsx
- 박스 이동
- 박스 크기 조절
- 새 박스 추가
```

**작업 목록**:
- [ ] `ImageViewer.tsx` - Konva 기반 이미지 뷰어
- [ ] `BoundingBox.tsx` - 개별 박스 컴포넌트
- [ ] `BoxEditor.tsx` - 박스 편집 로직
- [ ] `useBoxSelection.ts` - 선택 상태 관리 훅
- [ ] `useBoxDrag.ts` - 드래그 로직 훅

### Day 8-9: 검출 목록 + 승인/반려

**소스**: `utils/ui_verification.py` (1,053 LOC)

**컴포넌트**:
```typescript
// frontend/src/components/verification/DetectionList.tsx
- 검출 항목 목록 표시
- 필터링 (전체/승인/반려/수정)
- 진행률 표시

// frontend/src/components/verification/DetectionCard.tsx
- 개별 검출 카드
- 승인/반려 버튼
- 클래스 선택기

// frontend/src/components/verification/ClassSelector.tsx
- 27개 클래스 드롭다운
- 검색 기능
- 최근 사용 목록
```

**작업 목록**:
- [ ] `DetectionList.tsx` - 검출 목록
- [ ] `DetectionCard.tsx` - 개별 카드
- [ ] `ClassSelector.tsx` - 클래스 선택
- [ ] `ApprovalButtons.tsx` - 승인/반려 버튼
- [ ] `useVerificationStore.ts` - 검증 상태 관리

### Day 10: BOM 결과 페이지

**소스**: `utils/ui_bom.py` (139 LOC)

**컴포넌트**:
```typescript
// frontend/src/pages/Results.tsx
- BOM 테이블
- 총 금액 표시
- Export 버튼

// frontend/src/components/bom/BOMTable.tsx
- 품목별 수량/단가/합계
- 정렬/필터링

// frontend/src/components/bom/ExportButtons.tsx
- Excel 다운로드
- PDF 다운로드
```

**작업 목록**:
- [ ] `Results.tsx` - 결과 페이지
- [ ] `BOMTable.tsx` - BOM 테이블
- [ ] `ExportButtons.tsx` - 내보내기 버튼
- [ ] `SummaryCard.tsx` - 요약 카드

---

## Phase 3: 통합 및 테스트 (3일)

### Day 11: API 연동

**작업 목록**:
- [ ] 프론트엔드 ↔ 백엔드 API 연동
- [ ] 파일 업로드 플로우 테스트
- [ ] 검출 → 검증 → BOM 전체 플로우 테스트

### Day 12: BlueprintFlow 연동

**작업 목록**:
- [ ] 템플릿 JSON 스키마 정의
- [ ] 템플릿 로더 구현
- [ ] AX POC에서 호출 테스트

### Day 13: Docker 패키징

**작업 목록**:
- [ ] `Dockerfile` (frontend)
- [ ] `Dockerfile` (backend)
- [ ] `docker-compose.yml` 작성
- [ ] 전체 테스트

---

## 체크리스트

### 백엔드 API

- [ ] `POST /api/upload` - 파일 업로드
- [ ] `POST /api/detect` - 검출 실행
- [ ] `GET /api/session/{id}` - 세션 조회
- [ ] `PUT /api/verification/{id}` - 검증 결과 저장
- [ ] `POST /api/bom/create` - BOM 생성
- [ ] `GET /api/bom/export/excel` - Excel 내보내기
- [ ] `GET /api/bom/export/pdf` - PDF 내보내기

### 프론트엔드 페이지

- [ ] `/` - 업로드 페이지
- [ ] `/processing/:sessionId` - 처리 중 상태
- [ ] `/verification/:sessionId` - 검증 페이지
- [ ] `/results/:sessionId` - 결과 페이지

### 컴포넌트

- [ ] `FileDropZone` - 파일 드래그앤드롭
- [ ] `ImageViewer` - Konva 이미지 뷰어
- [ ] `BoundingBox` - 바운딩 박스
- [ ] `BoxEditor` - 박스 편집
- [ ] `DetectionList` - 검출 목록
- [ ] `DetectionCard` - 개별 카드
- [ ] `ClassSelector` - 클래스 선택
- [ ] `ApprovalButtons` - 승인/반려
- [ ] `BOMTable` - BOM 테이블
- [ ] `ExportButtons` - 내보내기

---

## 참고 자료

### 레거시 코드 매핑

| Streamlit | React | 비고 |
|-----------|-------|------|
| `st.file_uploader` | `FileDropZone` | react-dropzone |
| `st.image` | `ImageViewer` | react-konva |
| `st_drawable_canvas` | `BoxEditor` | konva Transformer |
| `st.dataframe` | `BOMTable` | 직접 구현 또는 tanstack-table |
| `st.download_button` | `ExportButtons` | Blob + anchor |

### 상태 관리

```typescript
// store/sessionStore.ts
interface SessionState {
  sessionId: string | null;
  image: string | null;
  detections: Detection[];
  verificationStatus: Record<string, 'pending' | 'approved' | 'rejected' | 'modified'>;
  modifiedClasses: Record<string, string>;
  bom: BOMData | null;
}
```
