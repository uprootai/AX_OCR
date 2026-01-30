# 백로그 (향후 작업)

> 마지막 업데이트: 2026-01-30
> 미래 작업 및 참조 문서

---

## 📊 현재 상태 요약

| 항목 | 값 |
|------|-----|
| **테스트** | 729개 (web-ui 304, gateway 425) |
| **빌드** | ✅ 15.04s |
| **ESLint** | 0 errors, 1 warning |
| **노드 정의** | 31개 |
| **API 서비스** | 21개 |

---

## P1: 단가 + UX + YOLO 확장 (2026-01-30 기준)

> ACTIVE.md의 확장 필요 분석 항목을 실행 가능한 작업으로 정리

### P1-1. BOM 프론트엔드 세션 단가 표시 [A-1]

**목표**: BOM 워크플로우 UI에서 세션별 커스텀 단가 적용 상태를 인지

| # | 작업 | 파일 |
|---|------|------|
| 1 | 세션 조회 시 pricing.json 존재 여부 반환 | `bom_router.py` (session 응답에 `has_pricing: bool` 추가) |
| 2 | BOM 결과 헤더에 "커스텀 단가 적용" 배지 표시 | `BOMResultsSection.tsx` |
| 3 | BOM UI에서 단가 파일 직접 업로드/제거 | `WorkflowPage.tsx` or 새 섹션 |

### P1-2. DetectionResultsSection 클래스 하이라이트 [B-1]

**목표**: 검증 단계에서도 클래스명 클릭 → 해당 검출만 강조

| # | 작업 | 파일 |
|---|------|------|
| 1 | `selectedClassName` state 추가 | `DetectionResultsSection.tsx` |
| 2 | 클래스 목록 클릭 핸들러 | `DetectionResultsSection.tsx` |
| 3 | Canvas 렌더링에 선택 상태 반영 (FinalResults 패턴 복제) | `DetectionResultsSection.tsx` |

### P1-3. data.yaml 방식 표준화 검토 [C-1]

**목표**: 커스텀 모델 클래스명 관리를 data.yaml 방식으로 통일

| # | 작업 | 파일 |
|---|------|------|
| 1 | model_registry.yaml 내 class_names 보유 모델 목록 확인 | `model_registry.yaml` |
| 2 | 학습 data.yaml이 존재하는 모델 식별 | `models/yolo-api/models/` |
| 3 | 해당 모델에 `data_yaml` 필드 추가 | `model_registry.yaml` |
| 4 | 불필요한 class_names 목록 제거 또는 폴백용 유지 | `model_registry.yaml` |

### P1-4. Docker 빌드 panasia_data.yaml 확인 [C-3]

| # | 작업 |
|---|------|
| 1 | `models/yolo-api/Dockerfile` 확인 (COPY 범위) |
| 2 | `.dockerignore` 에 `.yaml` 제외 패턴 없는지 확인 |
| 3 | `docker compose build yolo-api` 후 컨테이너 내부 확인 |

---

## P2: 중기 작업

### P2-1. 단가 API 확장 (GET/DELETE)

| 엔드포인트 | 동작 |
|-----------|------|
| `GET /bom/{session_id}/pricing` | 현재 적용된 단가 파일 내용 반환 |
| `DELETE /bom/{session_id}/pricing` | 세션 단가 제거, 글로벌 폴백 복원 |

### P2-2. 템플릿 실행 pricing_file 전달 검증

```
gateway-api/routers/workflow_router.py
  → execute_template(), execute_template_stream()
  → inputs가 그대로 전달되는지 E2E 테스트
```

### P2-3. BOM 테이블 ↔ 도면 하이라이트 연동

```
BOMResultsSection.tsx → onClassSelect callback
  → WorkflowPage.tsx → selectedClassName state lift
  → FinalResultsSection.tsx → selectedClassName prop
```

### P2-4. SAHI 모드 data.yaml class_names 호환

```
models/yolo-api/services/inference_service.py
  → SAHI AutoDetectionModel이 model.names를 상속하는지 확인
  → 필요 시 SAHI 추론 후 class_name 매핑 로직 추가
```

---

## P3: 장기 작업

| 작업 | 설명 |
|------|------|
| 시각화 기능 확장 | 공차 히트맵, BOM 연결선 등 |
| 템플릿 버전 관리 | 템플릿 히스토리 및 롤백 |
| ReferencePanel 리사이즈 → NodeDetailPanel 적용 | 동일 드래그 리사이즈 패턴 |
| FinalResultsSection 캔버스 다운로드 | 결과 이미지 PNG 저장 |
| 파일 첨부 상태 persist | GT/단가 파일 localStorage 저장 검토 |

---

## ✅ 완료된 백로그 항목

| 작업 | 완료일 | 상세 |
|------|--------|------|
| **빌더 단가 파일 업로드** | 2026-01-30 | 세션별 pricing 적용, 글로벌 폴백 |
| **첨부 파일 다운로드 버튼** | 2026-01-30 | 이미지/GT/단가 각각 다운로드 |
| **ReferencePanel 리사이즈/접기** | 2026-01-30 | 드래그 200~800px, masonry |
| **FinalResults 클래스 하이라이트** | 2026-01-30 | 클래스 클릭 → 파란색 강조 |
| **YOLO data.yaml 방식 전환** | 2026-01-30 | panasia 모델 적용 |
| **Self-contained Export 프론트엔드** | 2026-01-24 | Phase 2I 완료 |
| DSE Bearing 100점 | 2026-01-22 | 6 Phase 전체 완료 |
| Blueprint AI BOM Phase 2 | 2026-01-24 | 2A~2I 완료 |
| Self-contained Export (백엔드) | 2026-01-24 | 포트 오프셋 기능 포함 |
| MODEL_DEFAULTS 패턴 확장 | 2026-01-19 | 19개 API 적용 |

---

## 📅 로드맵

| 분기 | 작업 | 우선순위 | 상태 |
|------|------|----------|------|
| Q1 2026 | DSE Bearing 100점 | P1 | ✅ 완료 |
| Q1 2026 | Blueprint AI BOM Phase 2 | P1 | ✅ 완료 |
| Q1 2026 | 빌더 단가 + 다운로드 + UX | P1 | ✅ 완료 |
| Q1 2026 | 단가/하이라이트/data.yaml 확장 | P1 | ⏳ 진행 예정 |
| Q2 2026 | 시각화 기능 확장 | P3 | ⏳ 계획됨 |

---

## 📚 참조 문서

| 문서 | 위치 |
|------|------|
| 새 API 추가 가이드 | `.claude/skills/api-creation-guide.md` |
| 모듈화 가이드 | `.claude/skills/modularization-guide.md` |
| Phase 2 아키텍처 | `.todo/archive/BLUEPRINT_ARCHITECTURE_V2.md` |
| DSE Bearing 계획 | `.todo/archive/DSE_BEARING_100_PLAN.md` |

---

*마지막 업데이트: 2026-01-30*
