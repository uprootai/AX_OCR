# UX 개선: Toast 알림 및 로딩 오버레이 시스템 적용

> 작성일: 2026-01-01
> 상태: 진행 중 (P0 완료)
> 관련 커밋: APIStatusMonitor.tsx, useAPIDetail.ts 변경

---

## 1. 완료된 작업

### 1.1 APIStatusMonitor.tsx 변경 사항 (P0 - 완료)

| 항목 | 이전 | 이후 |
|------|------|------|
| 확인 대화상자 | `confirm()` 사용 | 제거 (바로 실행) |
| 결과 알림 | `alert()` 사용 | `Toast` 컴포넌트 |
| 로딩 상태 | 버튼만 disabled | 전역 로딩 오버레이 + 진행 바 |
| 에러 처리 | 단순 메시지 | Axios 에러 상세 분류 |
| 개별 API 제어 | 없음 | Stop/Start 버튼 추가 |
| Toast 지속시간 | - | 성공: 10초, 에러: 15초 |

**추가된 인터페이스**:
```typescript
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface LoadingState {
  isLoading: boolean;
  action: 'stop' | 'start' | null;
  target: string;
  progress: { current: number; total: number } | null;
}
```

**새로운 함수**:
- `showToast(message, type)` - Toast 표시 헬퍼
- `handleSingleAPIAction(api, action)` - 개별 API Start/Stop

**CategoryCard/APICard 새 Props**:
```typescript
// CategoryCard
onSingleApiAction: (api: APIInfo, action: 'stop' | 'start') => void;
singleApiActionLoading: string | null;
isGlobalLoading: boolean;

// APICard
onAction: (api: APIInfo, action: 'stop' | 'start') => void;
isActionLoading: boolean;
isGlobalLoading: boolean;
```

---

### 1.2 useAPIDetail.ts 변경 사항 (P0 - 완료)

| 항목 | 이전 | 이후 |
|------|------|------|
| API Key 삭제 | `confirm()` 사용 | 바로 실행 + Toast |
| Docker 작업 확인 | `window.confirm()` | 바로 실행 + Loading 오버레이 |
| Docker 작업 결과 | `alert()` | Toast (success/error) |
| 설정 저장 확인 | `window.confirm()` | 바로 실행 + 자동 컨테이너 적용 |
| 설정 저장 결과 | `alert()` | Toast (success/warning/error) |
| 에러 처리 | 단순 메시지 | Axios 에러 상세 분류 |

**추가된 인터페이스 (export)**:
```typescript
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

export interface LoadingState {
  isLoading: boolean;
  action: 'stop' | 'start' | 'restart' | 'save' | 'delete' | null;
  target: string;
}
```

**새로운 상태/함수**:
```typescript
// 상태
const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });
const [globalLoading, setGlobalLoading] = useState<LoadingState>({
  isLoading: false,
  action: null,
  target: '',
});

// 함수
const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {...}, []);
const hideToast = useCallback(() => {...}, []);
```

**Hook 반환값 추가**:
```typescript
return {
  // ... 기존 반환값
  toast,
  globalLoading,
  hideToast,
};
```

---

### 1.3 APIDetail.tsx 변경 사항 (P0 - 완료)

**새로운 임포트**:
```typescript
import Toast from '../../components/ui/Toast';
import { Loader2, StopCircle, PlayCircle, RotateCw, Trash2 } from 'lucide-react';
```

**새로운 상태 구조 분해**:
```typescript
const {
  // ... 기존
  toast,
  globalLoading,
  hideToast,
} = useAPIDetail(apiId);
```

**추가된 UI**:
- 전역 로딩 오버레이 (액션별 아이콘: stop/start/restart/save/delete)
- Toast 알림 컴포넌트

---

### 1.4 api-detail/index.ts 변경 사항 (P0 - 완료)

**추가된 타입 export**:
```typescript
export type {
  ToastState,
  LoadingState,
} from './hooks/useAPIDetail';
```

---

## 2. 미완료 작업: 동일 패턴 적용 필요

### 2.1 APIStatusMonitor.tsx 내 잔여 작업 (1개)

| 라인 | 현재 코드 | 변경 권장 |
|------|----------|----------|
| 91 | `confirm('이 API를 목록에서 삭제')` | Undo 가능 Toast 또는 확인 모달 |

**참고**: 개별 API 삭제는 복구 가능(자동 검색)하므로 바로 실행 후 Undo Toast 사용 권장

---

### 2.2 Dashboard.tsx (대시보드 메인) - P1 ✅ 완료

**파일**: `web-ui/src/pages/dashboard/Dashboard.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 61 | 세션 삭제 확인 | confirm() 제거, 바로 실행 |
| 71 | 세션 삭제 실패 | Toast (error) |
| 75 | 세션 삭제 에러 | Toast (error) + 상세 메시지 |
| 84 | 삭제할 세션 없음 | Toast (info) |
| 88 | 전체 삭제 확인 | confirm() 제거, 바로 실행 |
| 98 | 전체 삭제 성공 | Toast (success) |
| 100 | 전체 삭제 실패 | Toast (error) |
| 104 | 전체 삭제 에러 | Toast (error) + 상세 메시지 |
| 200 | API 추가 성공 | Toast (success) |
| 202 | API 이미 등록 | Toast (info) |
| 207 | API 검색 실패 | Toast (error) |
| 460 | API 삭제 확인 | confirm() 제거, 바로 실행 + Toast |

**총 12개 변경 완료** (+42줄, -18줄)

---

### 2.3 BlueprintFlowBuilder.tsx - P1 ✅ 완료

**파일**: `web-ui/src/pages/blueprintflow/BlueprintFlowBuilder.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 274 | 워크플로우 저장 성공 | Toast (success) |
| 278 | 워크플로우 저장 실패 | Toast (error) + 상세 메시지 |
| - | Toast 렌더링 | 추가됨 |

**총 2개 변경 완료** (+29줄, -2줄)

---

### 2.4 BlueprintFlowList.tsx - P1 ✅ 완료

**파일**: `web-ui/src/pages/blueprintflow/BlueprintFlowList.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 77 | 워크플로우 로드 실패 | Toast (error) |
| 82 | 워크플로우 삭제 확인 | confirm() 제거, 바로 실행 |
| 86 | 워크플로우 삭제 성공 | Toast (success) |
| 90 | 워크플로우 삭제 실패 | Toast (error) |
| 105 | 워크플로우 복제 성공 | Toast (success) |
| 109 | 워크플로우 복제 실패 | Toast (error) |
| - | Toast 렌더링 | 추가됨 |

**총 4개 변경 완료** (+20줄)

---

### 2.5 Admin.tsx - P2 ✅ 완료

**파일**: `web-ui/src/pages/admin/Admin.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 129 | 백업 성공 | Toast (success) |
| 133 | 백업 실패 | Toast (error) + 상세 메시지 |
| 160 | 복원 확인 | confirm() 유지 (위험 작업) |
| 172 | 복원 완료 | Toast (success) + 자동 새로고침 1초 |
| 177 | 복원 실패 | Toast (error) + 상세 메시지 |
| 188 | 초기화 확인 | confirm() 유지 (위험 작업) |
| 191 | 초기화 완료 | Toast (success) + 자동 새로고침 1초 |
| - | Toast 렌더링 | 추가됨 |

**총 5개 변경 완료** (+25줄) - confirm()은 위험 작업이므로 유지

---

### 2.6 YOLOModelManager.tsx - P2 ✅ 완료

**파일**: `web-ui/src/components/admin/YOLOModelManager.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 92 | 모델 삭제 확인 | confirm() 제거, 바로 실행 |
| 96 | 모델 삭제 성공 | Toast (success) |
| 100 | 모델 삭제 실패 | Toast (error) + 상세 메시지 |
| 115 | 모델 업데이트 성공 | Toast (success) |
| 119 | 모델 업데이트 실패 | Toast (error) + 상세 메시지 |
| 133 | 파일 업로드 성공 | Toast (success) |
| 137 | 파일 업로드 실패 | Toast (error) + 상세 메시지 |
| 365 | 필수 필드 누락 | Toast (warning) |
| 387 | 모델 추가 성공 | Toast (success) |
| 392 | 모델 추가 실패 | Toast (error) + 상세 메시지 |
| - | AddModelForm에 showToast props | 전달됨 |
| - | Toast 렌더링 | 추가됨 |

**총 7개 변경 완료** (+35줄)

---

### 2.7 ExecutionStatusPanel.tsx - P2 ✅ 완료

**파일**: `web-ui/src/pages/blueprintflow/components/ExecutionStatusPanel.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | Toast import, useCallback | 추가됨 |
| 960 | UIActionDisplay에 toast 상태 | 추가됨 |
| 964 | showToast 헬퍼 | 추가됨 |
| 968 | handleDeleteSession 함수 | 추출됨 |
| 971 | 세션 삭제 확인 | confirm() 제거, 바로 실행 |
| 972 | 세션 삭제 성공 | Toast (success) |
| 974 | 세션 삭제 실패 | Toast (error) |
| - | Toast 렌더링 | 추가됨 |

**총 3개 변경 완료** (+25줄)

---

### 2.8 ContainerManager.tsx - P2 ✅ 완료

**파일**: `web-ui/src/components/dashboard/ContainerManager.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 82 | 컨테이너 작업 성공 | Toast (success) 추가 |
| 85 | 컨테이너 작업 실패 | Toast (error) + 상세 메시지 |
| 89 | 컨테이너 작업 에러 | Toast (error) + 상세 메시지 |
| - | Toast 렌더링 | 추가됨 |

**총 2개 변경 + 성공 Toast 추가 완료** (+22줄)

---

### 2.9 useContainerStatus.ts - P2 ✅ 완료

**파일**: `web-ui/src/pages/blueprintflow/hooks/useContainerStatus.ts`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | UseContainerStatusOptions | onShowToast 콜백 옵션 추가 |
| 87 | 컨테이너 시작 실패 | onShowToast?.() 콜백 (error) |
| 98 | 노드 없음 경고 | onShowToast?.() 콜백 (warning) |
| 103 | 이미지 없음 경고 | onShowToast?.() 콜백 (warning) |

**BlueprintFlowBuilder.tsx 업데이트**:
- useContainerStatus 훅에 onShowToast 콜백 전달

**총 3개 변경 완료** (+콜백 인터페이스)

---

### 2.10 useImageUpload.ts - P3 ✅ 완료

**파일**: `web-ui/src/pages/blueprintflow/hooks/useImageUpload.ts`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | UseImageUploadOptions | onShowToast 콜백 옵션 추가 |
| 27 | 이미지 파일 아님 | onShowToast?.() 콜백 (warning) |
| 50 | 이미지 파일 아님 | onShowToast?.() 콜백 (warning) |
| 85 | 샘플 이미지 로드 실패 | onShowToast?.() 콜백 (error) |

**BlueprintFlowBuilder.tsx 업데이트**:
- useImageUpload 훅에 onShowToast 콜백 전달

**총 3개 변경 완료** (+콜백 인터페이스)

---

### 2.11 ErrorBoundary.tsx - P3 ✅ 완료

**파일**: `web-ui/src/components/ErrorBoundary.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | State 인터페이스 | toast 상태 추가 |
| - | showToast/hideToast | 클래스 메서드 추가 |
| 113 | 클립보드 복사 성공 | Toast (success) |
| 114 | 클립보드 복사 실패 | Toast (error) |
| 207-215 | Toast 렌더링 | Toast 컴포넌트 추가 |

**총 2개 변경 완료** (+클래스 메서드, +Toast 렌더링)

---

### 2.12 ResultActions.tsx - P3 ✅ 완료

**파일**: `web-ui/src/components/results/ResultActions.tsx`

| 라인 | 기능 | 변경 내용 |
|------|------|----------|
| - | ToastState 인터페이스 | 추가됨 |
| - | toast 상태, showToast 헬퍼 | 추가됨 |
| 61 | 치수 데이터 없음 | Toast (warning) |
| 102 | 클립보드 복사 실패 | Toast (error) |
| 147-155 | Toast 렌더링 | Toast 컴포넌트 추가 |

**총 2개 변경 완료** (+Toast 인터페이스, +렌더링)

---

## 3. Blueprint AI BOM (별도 프로젝트) - P4

**주의**: 별도 프로젝트이므로 독립적으로 Toast 시스템 구현 필요

| 파일 | confirm/alert 수 |
|------|------------------|
| WorkflowPage.tsx | 2 |
| DetectionRow.tsx | 1 |
| SymbolVerificationSection.tsx | 3 |
| WorkflowSidebar.tsx | 2 |
| HomePage.tsx | 1 |
| RelationList.tsx | 1 |
| APIKeySettings.tsx | 1 |

**총 11개 변경 필요**

---

## 4. 구현 가이드라인

### 4.1 Toast 사용 규칙

```typescript
// Success: 작업 완료 (10초)
showToast('✓ 저장되었습니다', 'success');

// Error: 작업 실패 (15초, 상세 에러 포함)
showToast(`✗ 저장 실패\n${errorMessage}`, 'error');

// Warning: 부분 성공 또는 주의
showToast('⚠️ 일부 항목만 처리되었습니다', 'warning');

// Info: 정보 전달
showToast('ℹ️ 변경 사항이 없습니다', 'info');
```

### 4.2 Axios 에러 상세 분류 패턴

```typescript
let errorMsg = '알 수 없는 오류';
if (axios.isAxiosError(error)) {
  if (error.code === 'ECONNABORTED') {
    errorMsg = '시간 초과 (30초)';
  } else if (error.response) {
    errorMsg = `HTTP ${error.response.status}: ${error.response.data?.detail || error.response.statusText}`;
  } else if (error.request) {
    errorMsg = '서버 응답 없음 - Gateway API 확인 필요';
  }
} else if (error instanceof Error) {
  errorMsg = error.message;
}
```

### 4.3 confirm() 대체 전략

| 상황 | 권장 방법 |
|------|----------|
| 단순 삭제 (복구 가능) | **제거** - 바로 실행 후 Toast |
| 단순 삭제 (복구 불가) | **Undo Toast** 또는 확인 모달 |
| 위험 작업 (전체 삭제, 초기화) | **확인 모달** 유지 |
| 데이터 손실 가능성 | **확인 모달** 유지 |

### 4.4 로딩 오버레이 적용 기준

| 상황 | 적용 여부 |
|------|----------|
| 3초 이상 소요 예상 | 적용 |
| 백그라운드 작업 방지 필요 | 적용 |
| Docker 컨테이너 조작 | 적용 |
| 즉시 완료되는 작업 | 미적용 |

---

## 5. 작업 우선순위 요약

| 우선순위 | 파일 | 변경 수 | 상태 |
|----------|------|---------|------|
| **P0** | APIStatusMonitor.tsx | 다수 | ✅ 완료 |
| **P0** | useAPIDetail.ts | 다수 | ✅ 완료 |
| **P0** | APIDetail.tsx | 다수 | ✅ 완료 |
| **P1** | Dashboard.tsx | 12 | ✅ 완료 |
| **P1** | BlueprintFlowBuilder.tsx | 2 | ✅ 완료 |
| **P1** | BlueprintFlowList.tsx | 4 | ✅ 완료 |
| **P2** | Admin.tsx | 5 | ✅ 완료 |
| **P2** | YOLOModelManager.tsx | 7 | ✅ 완료 |
| **P2** | ExecutionStatusPanel.tsx | 3 | ✅ 완료 |
| **P2** | ContainerManager.tsx | 2 | ✅ 완료 |
| **P2** | useContainerStatus.ts | 3 | ✅ 완료 |
| **P3** | useImageUpload.ts | 3 | ✅ 완료 |
| **P3** | ErrorBoundary.tsx | 2 | ✅ 완료 |
| **P3** | ResultActions.tsx | 2 | ✅ 완료 |
| P4 | Blueprint AI BOM (7개 파일) | 11 | 대기 |

**총계**: P0 완료, **P1 전체 완료**, **P2 전체 완료**, **P3 전체 완료**, P4 대기 (~11개 변경 필요)

---

## 6. 공통 컴포넌트 추출 작업

### 6.1 LoadingOverlay 컴포넌트 추출 (권장)

**현재**: APIStatusMonitor.tsx, APIDetail.tsx 내부에 중복 구현

**추출 필요**:
```typescript
// web-ui/src/components/ui/LoadingOverlay.tsx
interface LoadingOverlayProps {
  isLoading: boolean;
  action?: 'stop' | 'start' | 'restart' | 'delete' | 'save' | string;
  target?: string;
  progress?: { current: number; total: number };
  message?: string;
}
```

### 6.2 ConfirmModal 컴포넌트 생성 (권장)

**필요한 이유**: 위험 작업에 여전히 확인 필요

```typescript
// web-ui/src/components/ui/ConfirmModal.tsx
interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  onConfirm: () => void;
  onCancel: () => void;
}
```

---

## 7. 테스트 필요 사항

- [x] Toast가 스크롤 위치와 관계없이 표시되는지 확인
- [x] 로딩 오버레이가 다른 작업을 차단하는지 확인
- [x] 에러 발생 시 적절한 메시지가 표시되는지 확인
- [x] Toast 지속 시간 확인 (성공: 10초, 에러: 15초)
- [ ] 다크 모드에서 Toast/LoadingOverlay 스타일 확인
- [ ] 병렬 Toast 표시 시 동작 확인
- [ ] 키보드 접근성 (ESC로 Toast 닫기)

---

## 8. 변경 내역

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-01 | 최초 작성 (APIStatusMonitor.tsx 분석) |
| 2026-01-01 | P0 완료: useAPIDetail.ts, APIDetail.tsx 변경 |
| 2026-01-01 | 전체 파일 재스캔, 변경 필요 목록 업데이트 |
| 2026-01-01 | P1 완료: Dashboard.tsx (12개 변경, +42/-18줄) |
| 2026-01-01 | P1 완료: BlueprintFlowBuilder.tsx (2개 변경, +29/-2줄) |
| 2026-01-01 | P1 완료: BlueprintFlowList.tsx (4개 변경, +20줄) |
| 2026-01-01 | P2 완료: Admin.tsx (5개 변경, +25줄, confirm 유지) |
| 2026-01-01 | P2 완료: YOLOModelManager.tsx (7개 변경, +35줄) |
| 2026-01-01 | P2 완료: ExecutionStatusPanel.tsx (3개 변경, +25줄) |
| 2026-01-01 | P2 완료: ContainerManager.tsx (2개 변경, +22줄) |
| 2026-01-01 | P2 완료: useContainerStatus.ts (3개 변경, 콜백 패턴) |
| 2026-01-01 | P3 완료: useImageUpload.ts (3개 변경, 콜백 패턴) |
| 2026-01-01 | P3 완료: ErrorBoundary.tsx (2개 변경, 클래스 컴포넌트) |
| 2026-01-01 | P3 완료: ResultActions.tsx (2개 변경) - **P3 전체 완료** |

---

## 9. ⚠️ 크리티컬 이슈 발견

### 9.1 .gitignore가 ResultActions.tsx 차단 중

**문제**: `.gitignore` 43번 줄의 `**/results/*` 패턴이 소스 코드 차단

```bash
$ git check-ignore -v web-ui/src/components/results/ResultActions.tsx
.gitignore:43:**/results/*    web-ui/src/components/results/ResultActions.tsx
```

**해결 필요**:
```gitignore
# .gitignore 수정
**/results/*
!web-ui/src/components/results/*
```

**상세 분석**: [TOAST_MIGRATION_ANALYSIS.md](./TOAST_MIGRATION_ANALYSIS.md) 참조

---

**작성자**: Claude Code
**마지막 업데이트**: 2026-01-01
