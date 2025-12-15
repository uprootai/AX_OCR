# Blueprint AI BOM

> **AI 기반 도면 분석 및 BOM 생성 솔루션**
> AX POC BlueprintFlow에서 Export되는 납품용 독립 실행 모듈

---

## 개요

```
도면 업로드 → YOLO 검출 → Human-in-the-Loop 검증 → BOM 생성 → Excel/PDF 출력
```

| 항목 | 값 |
|------|-----|
| **상태** | ✅ 구현 완료 (85%) |
| **프론트엔드** | http://localhost:3000 |
| **백엔드** | http://localhost:5020 |
| **검출 클래스** | 27개 산업용 전장 부품 |
| **출력 형식** | Excel, CSV, JSON (PDF 예정) |

---

## 빠른 시작

```bash
# Docker로 실행
docker-compose up -d

# 또는 개발 모드
cd backend && python api_server.py
cd frontend && npm run dev
```

---

## 프로젝트 구조

```
blueprint-ai-bom/
├── backend/                    # FastAPI 백엔드
│   ├── api_server.py           # 메인 서버
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── schemas/                # Pydantic 모델
│   │   ├── session.py
│   │   ├── detection.py
│   │   └── bom.py
│   ├── services/               # 비즈니스 로직
│   │   ├── session_service.py
│   │   ├── detection_service.py
│   │   └── bom_service.py
│   ├── routers/                # API 엔드포인트
│   │   ├── session_router.py
│   │   ├── detection_router.py
│   │   └── bom_router.py
│   └── tests/                  # 테스트 (15개)
│
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── App.tsx
│   │   ├── types/              # 타입 정의
│   │   ├── lib/api.ts          # API 클라이언트
│   │   ├── store/              # Zustand 스토어
│   │   ├── components/layout/  # 레이아웃
│   │   └── pages/              # 페이지 컴포넌트
│   │       ├── HomePage.tsx
│   │       ├── DetectionPage.tsx
│   │       ├── VerificationPage.tsx
│   │       └── BOMPage.tsx
│   ├── Dockerfile
│   └── nginx.conf
│
├── legacy/                     # 레거시 Streamlit (삭제 예정)
├── models/                     # YOLO 모델 (symlink)
├── docker-compose.yml
└── README.md
```

---

## 구현 상태

### ✅ 완료 (Day 1-11, 13)

| 영역 | 구현 내용 |
|------|----------|
| **Backend** | FastAPI, Services, Routers, 15개 테스트 통과 |
| **Frontend** | React 19 + TypeScript + Tailwind CSS v4 |
| **이미지 뷰어** | SVG 기반 바운딩 박스 오버레이 |
| **검증 UI** | 승인/반려/수정, 일괄 처리 |
| **BOM 페이지** | 테이블, 요약, Excel/CSV/JSON 내보내기 |
| **Docker** | docker-compose, Dockerfile (frontend + backend) |

### 🔄 진행 중 (Day 12)

| 작업 | 설명 |
|------|------|
| BlueprintFlow 연동 | AX POC 프로젝트와 통합 |
| 템플릿 Import/Export | 워크플로우 템플릿 지원 |

### ⏳ 대기 중

| 작업 | 설명 |
|------|------|
| 레거시 정리 | Streamlit 코드 삭제 (사용자 확인 후) |
| PDF 내보내기 | BOM PDF 출력 기능 |

---

## 27개 검출 클래스

| 카테고리 | 클래스 | 예시 모델 | 단가 |
|----------|--------|----------|------|
| 차단기 | CIRCUIT_BREAKER | BK63H 2P | 45,000원 |
| 변압기 | TRANSFORMER | MST600VA | 180,000원 |
| 스위치 | DISCONNECT_SWITCH | SW1 | 28,000원 |
| 버튼 | EMERGENCY_BUTTON | MRE-NR1R | 12,000원 |
| PLC CPU | PLC_CPU | 6ES7513-1AL01-0AB0 | 850,000원 |
| 터미널 | TERMINAL_BLOCK | ST4, ST2.5 | 8,500~12,000원 |
| 전원 | SWITCHING_POWER_SUPPLY | TRIO-PS-1AC-24DC | 85,000~120,000원 |
| DI 모듈 | PLC_DI | 6ES7221-1BH32-0XB0 | 150,000원 |
| DO 모듈 | PLC_DO | 6ES7222-1HH32-0XB0 | 180,000원 |
| AI 모듈 | PLC_AI | 6ES7234-4HE32-0XB0 | 280,000원 |
| AO 모듈 | PLC_AO | 6ES7232-4HD32-0XB0 | 320,000원 |
| 네트워크 | ETHERNET_SWITCH | EDS-208A | 95,000원 |
| HMI | HMI_PANEL | 6AV7240 | 480,000원 |
| 기타 | BUZZER, PILOT_LAMP, RELAY 등 | - | - |

---

## 개발 환경

### 레거시 (Streamlit - 참조용)

```bash
cd blueprint-ai-bom
pip install -r requirements.txt
streamlit run real_ai_app.py --server.port 8503
```

### 목표 (React + FastAPI)

```bash
# 백엔드
cd blueprint-ai-bom/backend
pip install -r requirements.txt
uvicorn api_server:app --port 5020

# 프론트엔드
cd blueprint-ai-bom/frontend
npm install
npm run dev
```

---

## Docker (납품용)

```bash
docker compose up -d
# http://localhost 접속
```

---

## 핵심 기능

### 1. AI 심볼 검출
- YOLOv11 모델 기반 27개 클래스 자동 검출
- 신뢰도 기반 필터링
- GPU/CPU 자동 감지

### 2. Human-in-the-Loop 검증
- 바운딩 박스 수정 (이동, 크기 조절)
- 클래스 변경
- 승인/반려 워크플로우
- 수동 추가

### 3. BOM 생성
- 검증된 검출 결과 집계
- 가격 정보 자동 매칭
- Excel/PDF 내보내기

---

## 성능 지표

| 항목 | 값 |
|------|-----|
| 검출 정확도 | 96% (YOLOv11 Nano) |
| 처리 속도 (GPU) | ~2-3초/페이지 |
| 처리 속도 (CPU) | ~8-10초/페이지 |
| 지원 해상도 | 최대 4K |
| 모델 크기 | 5.3MB (Nano) ~ 131MB (Large) |

---

## 관련 문서

| 문서 | 위치 |
|------|------|
| 통합 전략 | `../.todos/2025-12-14_integration_strategy.md` |
| Export 아키텍처 | `../.todos/2025-12-14_export_architecture.md` |
| AX POC 가이드 | `../CLAUDE.md` |
| 레거시 문서 | `./docs/` |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v3.0 | 2025-12-14 | AX POC 통합, React 전환 시작 |
| v2.0 | 2025-09-30 | 모듈러 아키텍처 (Streamlit) |
| v1.0 | 2025-09-01 | 초기 버전 (모놀리식) |

---

**Powered by AX POC BlueprintFlow + YOLOv11**
