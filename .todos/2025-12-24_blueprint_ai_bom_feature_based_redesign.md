# Blueprint AI BOM 기능 중심 재설계

> **목표**: 불명확한 "도면 타입" 선택 → 명확한 "기능 선택" 방식으로 전환
> **작성일**: 2025-12-24
> **상태**: ✅ 완료 (v2 - 단순화)

---

## 현재 진행 상황 (2025-12-24 17:50 업데이트)

### 🎉 v2 단순화 완료 - drawing_type 완전 제거!

| Phase | 작업 | 파일 | 상태 |
|-------|------|------|------|
| **Phase 1** | **features 파라미터 추가 (checkboxGroup)** | inputNodes.ts | ✅ 완료 |
| **Phase 1** | **checkboxGroup 타입 정의** | types.ts | ✅ 완료 |
| **Phase 1** | **Builder UI에 체크박스 렌더링** | NodeDetailPanel.tsx | ✅ 완료 |
| **Phase 1** | **프리셋 선택 시 features 자동 설정** | NodeDetailPanel.tsx | ✅ 완료 |
| Phase 2 | features 파이프라인 패스스루 | 17개 executor | ✅ 완료 |
| Phase 3 | BOM Executor features 수신 | bom_executor.py | ✅ 완료 |
| Phase 3 | 세션 API features 파라미터 | session_router.py | ✅ 완료 |
| Phase 3 | 세션 스키마 features 필드 | session.py (backend) | ✅ 완료 |
| Phase 3 | 세션 서비스 features 저장 | session_service.py | ✅ 완료 |
| Phase 4 | getSectionVisibility 함수 수정 | WorkflowPage.tsx | ✅ 완료 |
| Phase 4 | effectiveFeatures useMemo | WorkflowPage.tsx | ✅ 완료 |
| Phase 4 | Session 타입 features 필드 | types/index.ts (frontend) | ✅ 완료 |

### 선택 작업 (보류)

| Phase | 작업 | 파일 | 상태 |
|-------|------|------|------|
| Phase 2 (선택) | GT 노드 추가 | groundtruth.yaml, gt_executor.py | ⏸️ 보류 |

---

## 상세 체크리스트

### Phase 1: Builder UI - features 선택 UI ✅ 완료

#### 1.1 inputNodes.ts 수정
- [x] `features` 파라미터 추가 (type: 'checkboxGroup')
- [x] 프리셋(drawing_type) 변경 시 features 기본값 연동 (linkedTo 속성)
- [x] `BOM_FEATURES` 상수를 파라미터 options으로 활용

#### 1.2 types.ts 수정
- [x] `CheckboxOption` 인터페이스 추가
- [x] `NodeParameter.type`에 'checkboxGroup' 추가
- [x] `linkedTo` 속성 추가 (파라미터 연동용)

#### 1.3 NodeDetailPanel.tsx 수정
- [x] `checkboxGroup` 파라미터 타입 렌더링
- [x] drawing_type 변경 시 features 자동 업데이트 로직 (handleParameterChange)
- [x] 체크박스 UI 렌더링 (아이콘, 힌트, 활성화 수 표시)

#### 1.3 예상 UI
```
ImageInput 노드 파라미터:
┌─────────────────────────────────────┐
│ 📐 도면 타입 (프리셋)               │
│ [치수 도면 ▼]                       │
├─────────────────────────────────────┤
│ 🔧 활성화 기능                      │
│ ☑ 📏 치수 OCR                      │
│ ☑ ✅ 치수 검증                      │
│ ☑ 📊 GT 비교                       │
│ ☐ 🎯 심볼 검출 (YOLO 필요)          │
│ ☐ 📋 BOM 생성                      │
│ ☐ 📐 GD&T 파싱                     │
└─────────────────────────────────────┘
```

### Phase 2: 파이프라인 패스스루 ✅ 완료

- [x] imageinput_executor.py: PRESET_FEATURES 매핑, features 출력
- [x] 17개 executor: features 패스스루 코드 추가
- [x] bom_executor.py: inputs에서 features 우선 수신

### Phase 3: BOM Backend ✅ 완료

- [x] session_router.py: features 쿼리 파라미터
- [x] session_service.py: features 파라미터 저장
- [x] session.py (schemas): features 필드 추가

### Phase 4: 세션 UI 동적 구성 ✅ 완료

- [x] WorkflowPage.tsx: getSectionVisibility(type, features) 수정
- [x] WorkflowPage.tsx: effectiveFeatures useMemo 추가
- [x] types/index.ts: Session 인터페이스 features 필드
- [x] DRAWING_TYPE_SECTIONS: features 없을 때 폴백으로 유지 (하위 호환)

---

## 다음 단계

1. **Phase 1 구현** - Builder UI에 features 체크박스 추가
2. 테스트 및 검증
3. (선택) Phase 2 GT 노드

---

## 파일 변경 요약

### 완료된 변경 (32개 파일)

```
gateway-api/blueprintflow/executors/
├── imageinput_executor.py    # PRESET_FEATURES, features 출력
├── bom_executor.py           # features 수신, 세션 생성 시 전달
├── yolo_executor.py          # features 패스스루
├── edocr2_executor.py        # features 패스스루
├── ... (14개 더)             # features 패스스루

blueprint-ai-bom/backend/
├── routers/session_router.py # features 쿼리 파라미터
├── services/session_service.py # features 저장
├── schemas/session.py        # features 필드

blueprint-ai-bom/frontend/src/
├── pages/WorkflowPage.tsx    # getSectionVisibility, effectiveFeatures
├── types/index.ts            # Session.features 필드

web-ui/src/config/nodes/
├── inputNodes.ts             # features 파라미터 (checkboxGroup)
├── types.ts                  # CheckboxOption, checkboxGroup 타입

web-ui/src/components/blueprintflow/
├── NodeDetailPanel.tsx       # checkboxGroup 렌더링, drawing_type→features 연동
```
