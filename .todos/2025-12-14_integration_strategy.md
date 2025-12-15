# AX POC + DrawingBOMExtractor 통합 전략

> **작성일**: 2025-12-14
> **목적**: 두 프로젝트 통합 및 온프레미스 납품 아키텍처 설계
> **상태**: 기획 단계

---

## 현황 분석

### 프로젝트 비교

| 항목 | AX POC | DrawingBOMExtractor |
|------|--------|---------------------|
| **목적** | 워크플로우 빌더 + 다양한 AI API | BOM 추출 특화 |
| **프론트엔드** | React 19 + ReactFlow | Streamlit |
| **백엔드** | FastAPI + 19개 마이크로서비스 | 모놀리식 Python |
| **AI 모델** | YOLO, OCR 7종, 세그멘테이션 등 | YOLO v11 (27 클래스) |
| **강점** | 확장성, 모듈성, 성능 | Human-in-the-Loop UI |
| **약점** | 검증 UI 미구현 | 성능, 메모리, 확장성 |

### Streamlit의 한계

```
1. 성능 문제
   - 전체 페이지 리렌더링 (React의 Virtual DOM 없음)
   - 대용량 이미지 처리 시 브라우저 메모리 폭발
   - WebSocket 기반이라 동시 사용자 처리 비효율

2. 메모리 효율
   - session_state가 서버 메모리에 상주
   - 이미지/모델 캐싱이 프로세스별로 중복
   - 10명 동시 접속 시 GPU 메모리 부족

3. 기능 확장 제약
   - 커스텀 컴포넌트 제작 어려움
   - 복잡한 상태 관리 불가능
   - 드래그앤드롭, 캔버스 편집 등 고급 UI 제약
```

---

## 통합 전략: 3가지 옵션

### Option A: React로 완전 재작성 (권장)

```
┌─────────────────────────────────────────────────────────────┐
│                    통합 시스템 아키텍처                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              React 19 Frontend (AX POC)              │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │   │
│  │  │Blueprint  │ │ Dashboard │ │ BOM Verification  │  │   │
│  │  │Flow       │ │           │ │ (신규)            │  │   │
│  │  │Builder    │ │           │ │                   │  │   │
│  │  └───────────┘ └───────────┘ └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Gateway (8000)                  │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │   │
│  │  │Workflow   │ │ API Specs │ │ BOM Service       │  │   │
│  │  │Engine     │ │ (YAML)    │ │ (신규)            │  │   │
│  │  └───────────┘ └───────────┘ └───────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         ▼                 ▼                 ▼              │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐        │
│  │ YOLO API  │     │ OCR APIs  │     │ BOM API   │        │
│  │ (5005)    │     │(5002-5015)│     │ (신규)    │        │
│  └───────────┘     └───────────┘     └───────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**장점**:
- 성능 최적화 (Virtual DOM, 코드 스플리팅)
- 일관된 코드베이스
- 장기적 유지보수 용이
- 동시 사용자 처리 우수

**단점**:
- 개발 기간 길음 (3-4주)
- Streamlit UI 재구현 필요

**구현 범위**:
```
신규 개발:
1. web-ui/src/pages/verification/
   ├── VerificationPage.tsx      # 메인 페이지
   ├── BoundingBoxEditor.tsx     # 바운딩 박스 편집
   ├── ClassSelector.tsx         # 클래스 선택기
   ├── VotingPanel.tsx           # 앙상블 투표
   └── ApprovalControls.tsx      # 승인/반려 버튼

2. web-ui/src/components/canvas/
   ├── DrawableCanvas.tsx        # 캔버스 에디터
   ├── BoxOverlay.tsx            # 박스 오버레이
   └── ZoomPanControls.tsx       # 줌/팬 컨트롤

3. gateway-api/services/
   └── bom_service.py            # BOM 생성 로직 이전

4. models/bom-api/               # BOM 전용 API (선택)
```

---

### Option B: 하이브리드 (Streamlit 임베딩)

```
React App ──iframe──> Streamlit (검증 UI만)
```

**장점**: 빠른 구현 (1주)
**단점**:
- iframe 통신 복잡
- 두 시스템 유지보수
- 성능 문제 해결 안됨

---

### Option C: Streamlit 최적화 + API 분리

```
Streamlit UI ──HTTP──> FastAPI Gateway ──> 마이크로서비스
```

**장점**: 기존 코드 재사용
**단점**:
- 근본적 성능 문제 미해결
- 확장성 제한 지속

---

## 권장안: Option A 상세 계획

### Phase 1: BOM API 마이크로서비스화 (3일)

DrawingBOMExtractor의 핵심 로직을 API로 분리:

```python
# models/bom-api/api_server.py

@app.post("/process")
async def process_drawing(file: UploadFile):
    """도면 처리 및 검출"""
    return {"detections": [...], "image_id": "..."}

@app.post("/verify")
async def verify_detections(data: VerificationData):
    """검증 결과 저장"""
    return {"status": "saved", "corrections": [...]}

@app.post("/generate-bom")
async def generate_bom(data: BOMRequest):
    """BOM 생성 (Excel/PDF)"""
    return {"bom_url": "...", "total_cost": 1234567}

@app.post("/export/{format}")
async def export_bom(format: str, data: ExportRequest):
    """Excel/PDF 내보내기"""
    return FileResponse(...)
```

**이전할 코드**:
```
DrawingBOMExtractor/utils/
├── detection.py      → models/bom-api/services/detection_service.py
├── bom_generator.py  → models/bom-api/services/bom_service.py
├── file_handler.py   → 공통 유틸리티
└── ocr_utils.py      → OCR API와 통합
```

---

### Phase 2: React 검증 UI 구현 (7일)

```typescript
// web-ui/src/pages/verification/VerificationPage.tsx

const VerificationPage: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [selectedBox, setSelectedBox] = useState<number | null>(null);

  return (
    <div className="flex h-screen">
      {/* 좌측: 이미지 + 바운딩 박스 */}
      <div className="flex-1">
        <BoundingBoxEditor
          image={image}
          detections={detections}
          selectedBox={selectedBox}
          onBoxSelect={setSelectedBox}
          onBoxEdit={handleBoxEdit}
          onBoxAdd={handleBoxAdd}
          onBoxDelete={handleBoxDelete}
        />
      </div>

      {/* 우측: 검출 목록 + 클래스 편집 */}
      <div className="w-96">
        <DetectionList
          detections={detections}
          onApprove={handleApprove}
          onReject={handleReject}
          onClassChange={handleClassChange}
        />
        <VotingPanel models={models} />
        <ApprovalSummary stats={stats} />
      </div>
    </div>
  );
};
```

**필요 라이브러리**:
```json
{
  "react-konva": "^18.2.10",     // Canvas 렌더링
  "use-gesture": "^10.3.0",      // 드래그/줌 제스처
  "zustand": "^4.5.0"            // 상태 관리 (이미 사용중)
}
```

---

### Phase 3: BlueprintFlow 연동 (3일)

BlueprintFlow에서 생성한 워크플로우가 BOM 검증 시스템으로 연결:

```
BlueprintFlow 빌더
       │
       ▼
┌─────────────────────────┐
│ 워크플로우 템플릿 저장   │
│ (JSON/YAML)             │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ 템플릿 선택 UI          │
│ - 기계 도면 분석        │
│ - 전장 도면 BOM         │
│ - P&ID 분석             │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ 자동 실행 → 검증 UI     │
└─────────────────────────┘
```

**구현**:
```typescript
// 템플릿 실행 후 검증 페이지로 이동
const executeTemplate = async (templateId: string, file: File) => {
  const result = await workflowApi.execute(templateId, file);
  navigate(`/verification/${result.session_id}`);
};
```

---

### Phase 4: 온프레미스 패키징 (2일)

```yaml
# docker-compose.onpremise.yml

version: '3.8'
services:
  # 프론트엔드 (Nginx + React)
  web-ui:
    image: ax-poc/web-ui:${VERSION}
    ports:
      - "80:80"

  # API Gateway
  gateway-api:
    image: ax-poc/gateway-api:${VERSION}
    ports:
      - "8000:8000"

  # 핵심 AI 서비스만 포함
  yolo-api:
    image: ax-poc/yolo-api:${VERSION}
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  bom-api:
    image: ax-poc/bom-api:${VERSION}

  # 선택적 서비스
  edocr2-api:
    profiles: ["ocr"]

  knowledge-api:
    profiles: ["knowledge"]
```

**납품 구성**:
```
납품 패키지/
├── docker-compose.yml          # 메인 구성
├── docker-compose.override.yml # GPU/CPU 설정
├── .env.example                # 환경 변수 템플릿
├── images/                     # Docker 이미지 tar
│   ├── web-ui.tar
│   ├── gateway-api.tar
│   ├── yolo-api.tar
│   └── bom-api.tar
├── models/                     # 학습된 모델
│   └── yolo/best.pt
├── scripts/
│   ├── install.sh              # 설치 스크립트
│   ├── start.sh                # 시작 스크립트
│   └── backup.sh               # 백업 스크립트
└── docs/
    ├── INSTALL.md              # 설치 가이드
    ├── USER_MANUAL.md          # 사용자 매뉴얼
    └── ADMIN_GUIDE.md          # 관리자 가이드
```

---

## 일정 추정

| Phase | 작업 | 기간 | 담당 |
|-------|------|------|------|
| 1 | BOM API 마이크로서비스화 | 3일 | 백엔드 |
| 2 | React 검증 UI | 7일 | 프론트엔드 |
| 3 | BlueprintFlow 연동 | 3일 | 풀스택 |
| 4 | 온프레미스 패키징 | 2일 | DevOps |
| - | 테스트 및 버그 수정 | 3일 | QA |
| **합계** | | **18일** | |

---

## 데이터 흐름 (통합 후)

```
┌──────────────────────────────────────────────────────────────────┐
│                         사용자 워크플로우                          │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ 1. 템플릿 선택 │      │ 2. 도면 업로드 │      │ 3. 직접 빌드  │
│ (프리셋)      │      │              │      │ (BlueprintFlow)│
└───────────────┘      └───────────────┘      └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │  워크플로우 실행      │
                    │  (Pipeline Engine)    │
                    └───────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ YOLO 검출     │      │ OCR 추출      │      │ 기타 분석     │
│ (27 클래스)   │      │ (치수, 텍스트)│      │ (공차, P&ID)  │
└───────────────┘      └───────────────┘      └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                    ┌───────────────────────┐
                    │  검증 UI (React)      │
                    │  - 바운딩 박스 편집   │
                    │  - 클래스 수정        │
                    │  - 승인/반려          │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  BOM 생성             │
                    │  - Excel/PDF 출력    │
                    │  - 견적서 생성        │
                    └───────────────────────┘
```

---

## 마이그레이션 체크리스트

### DrawingBOMExtractor → AX POC

- [ ] `utils/detection.py` → `models/bom-api/services/`
- [ ] `utils/bom_generator.py` → `models/bom-api/services/`
- [ ] `utils/visualization.py` → `web-ui/src/components/canvas/`
- [ ] `classes_info_with_pricing.json` → `gateway-api/data/`
- [ ] `models/yolo/` → 기존 YOLO API 통합 또는 별도 유지
- [ ] Voting 앙상블 로직 → React 컴포넌트

### 재사용 가능한 자산

| 자산 | 위치 | 재사용 방법 |
|------|------|-------------|
| YOLO 모델 (v11n/l/x) | `models/yolo/` | 기존 YOLO API에 모델 추가 |
| 27개 클래스 정의 | `classes_info_with_pricing.json` | API 스펙으로 변환 |
| BOM 생성 로직 | `utils/bom_generator.py` | Python 서비스로 이전 |
| 가격 데이터베이스 | JSON | PostgreSQL 또는 YAML로 이전 |

---

## 의사결정 필요 사항

1. **모델 통합 방식**
   - [ ] A: 기존 YOLO API(5005)에 BOM 클래스 추가
   - [ ] B: 별도 BOM-YOLO API(5020) 신규 생성

2. **데이터 저장소**
   - [ ] A: 파일 기반 (JSON/YAML)
   - [ ] B: PostgreSQL 도입
   - [ ] C: SQLite (온프레미스 간소화)

3. **인증/권한**
   - [ ] A: 없음 (단일 사용자)
   - [ ] B: 기본 인증 (ID/PW)
   - [ ] C: SSO 연동 (기업 환경)

---

## 참고 자료

- AX POC 프로젝트: `/home/uproot/ax/poc/`
- DrawingBOMExtractor: `/home/uproot/panasia/DrawingBOMExtractor/`
- 기존 미완료 작업: `.todos/2025-12-06_techcross_meeting_analysis.md`
