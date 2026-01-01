# Toast 마이그레이션 분석 및 향후 작업

> 작성일: 2026-01-01
> 상태: 분석 완료, 향후 작업 대기
> 관련 커밋: 미커밋 상태 (15개 파일 수정됨)

---

## 1. 현재 변경 사항 요약

### 1.1 수정된 파일 (15개, +745줄/-125줄)

| 파일 | 변경 | 설명 |
|------|------|------|
| ErrorBoundary.tsx | +36줄 | 클래스 컴포넌트 Toast 패턴 |
| YOLOModelManager.tsx | +50줄 | Toast + props 전달 패턴 |
| ContainerManager.tsx | +34줄 | Toast 패턴 + 성공 메시지 추가 |
| APIStatusMonitor.tsx | +263줄 | Toast + Loading overlay + 개별 API 제어 |
| APIDetail.tsx | +68줄 | Toast/Loading 렌더링 |
| Admin.tsx | +42줄 | Toast (위험 작업 confirm 유지) |
| useAPIDetail.ts | +155줄 | Toast/Loading export |
| api-detail/index.ts | +2줄 | 타입 export |
| BlueprintFlowBuilder.tsx | +36줄 | Toast + 훅 콜백 전달 |
| BlueprintFlowList.tsx | +41줄 | Toast 패턴 |
| ExecutionStatusPanel.tsx | +49줄 | UIActionDisplay 내 Toast |
| useContainerStatus.ts | +13줄 | onShowToast 콜백 옵션 |
| useImageUpload.ts | +19줄 | onShowToast 콜백 옵션 |
| Dashboard.tsx | +60줄 | Toast 패턴 |

### 1.2 적용된 패턴 유형

| 패턴 | 적용 대상 | 설명 |
|------|----------|------|
| **직접 상태 관리** | 함수형 컴포넌트 | useState + showToast 헬퍼 |
| **콜백 주입** | 커스텀 훅 | onShowToast 옵션 파라미터 |
| **클래스 메서드** | 클래스 컴포넌트 | this.showToast 메서드 |
| **Props 전달** | 자식 컴포넌트 | showToast props 전달 |

---

## 2. ⚠️ 크리티컬 이슈

### 2.1 .gitignore가 소스 코드 차단 중

**문제**: `.gitignore` 43번 줄의 `**/results/*` 패턴이 `web-ui/src/components/results/ResultActions.tsx`를 차단

```bash
# 현재 상태
$ git check-ignore -v web-ui/src/components/results/ResultActions.tsx
.gitignore:43:**/results/*    web-ui/src/components/results/ResultActions.tsx
```

**영향**:
- ResultActions.tsx의 Toast 변경 사항이 커밋되지 않음
- 이 파일이 이미 배포/사용 중인 경우 심각한 문제

**해결 방법**:
```gitignore
# .gitignore 수정 필요
# 변경 전:
**/results/*

# 변경 후 (옵션 1 - 특정 경로 제외):
**/results/*
!web-ui/src/components/results/*

# 변경 후 (옵션 2 - 패턴 변경):
**/test-results/*
**/playwright-results/*
```

**우선순위**: P0 (즉시 수정 필요)

---

## 3. 코드 중복 및 개선 필요 사항

### 3.1 ToastState 인터페이스 중복 (11개 파일)

현재 동일한 인터페이스가 11개 파일에 중복 정의됨:

```typescript
// 11개 파일에서 동일하게 정의됨
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}
```

**중복 파일 목록**:
1. `pages/admin/Admin.tsx`
2. `pages/admin/api-detail/hooks/useAPIDetail.ts` (export됨)
3. `components/ErrorBoundary.tsx`
4. `components/admin/YOLOModelManager.tsx`
5. `components/results/ResultActions.tsx`
6. `pages/dashboard/Dashboard.tsx`
7. `components/dashboard/ContainerManager.tsx`
8. `components/monitoring/APIStatusMonitor.tsx`
9. `pages/blueprintflow/BlueprintFlowList.tsx`
10. `pages/blueprintflow/components/ExecutionStatusPanel.tsx`
11. `pages/blueprintflow/BlueprintFlowBuilder.tsx`

**권장 해결책**:
```typescript
// web-ui/src/types/toast.ts (신규 생성)
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

export type ToastType = ToastState['type'];
```

**우선순위**: P2 (리팩토링)

### 3.2 showToast 헬퍼 중복 (10개 파일)

```typescript
// 10개 파일에서 동일한 패턴
const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
  setToast({ show: true, message, type });
}, []);
```

**미사용 기존 훅 발견**:
- `web-ui/src/hooks/useToast.tsx` - 이미 존재하지만 사용되지 않음
- 다중 Toast 지원, ToastContainer 컴포넌트 제공

**권장 해결책**: 기존 useToast 훅 활용 또는 확장

**우선순위**: P2 (리팩토링)

### 3.3 LoadingState 인터페이스 중복 (2개 파일)

```typescript
// 2개 파일에서 유사하게 정의됨
interface LoadingState {
  isLoading: boolean;
  action: 'stop' | 'start' | 'restart' | 'save' | 'delete' | null;
  target: string;
  progress?: { current: number; total: number } | null;
}
```

**중복 파일**:
1. `pages/admin/api-detail/hooks/useAPIDetail.ts`
2. `components/monitoring/APIStatusMonitor.tsx`

**우선순위**: P3 (향후 리팩토링)

---

## 4. 남은 confirm() 호출 (3개)

### 4.1 의도적으로 유지된 confirm (2개)

| 파일 | 라인 | 기능 | 이유 |
|------|------|------|------|
| Admin.tsx | 160 | 설정 복원 | 위험 작업 - 되돌릴 수 없음 |
| Admin.tsx | 188 | 기본값 초기화 | 위험 작업 - 되돌릴 수 없음 |

**상태**: 의도적 유지 (ConfirmModal 컴포넌트로 대체 권장)

### 4.2 변경 가능한 confirm (1개)

| 파일 | 라인 | 기능 | 권장 조치 |
|------|------|------|----------|
| APIStatusMonitor.tsx | 91 | API 목록 삭제 | 바로 실행 + Undo Toast |

**이유**: API는 자동 검색으로 다시 추가 가능 (복구 가능한 작업)

**우선순위**: P3 (선택적 개선)

---

## 5. 일관성 검토

### 5.1 Toast Duration 차이

| 컴포넌트 | 성공 | 에러 | 비고 |
|----------|------|------|------|
| 대부분 | 10초 | 15초 | 표준 |
| useToast.tsx | 3초 | 3초 | 기본값이 다름 |

**권장**: 모든 컴포넌트에서 동일한 duration 사용

### 5.2 Toast 아이콘 패턴

모든 Toast 메시지가 일관된 아이콘 패턴 사용:
- 성공: `✓`
- 에러: `✗`
- 경고: `⚠️`
- 정보: `ℹ️`

**상태**: ✅ 일관됨

---

## 6. 향후 작업 우선순위

### P0 - 즉시 수정 필요

| 작업 | 파일 | 설명 |
|------|------|------|
| .gitignore 수정 | `.gitignore` | `**/results/*` 패턴이 소스 코드 차단 중 |
| git add 강제 | `ResultActions.tsx` | `git add -f` 또는 .gitignore 수정 후 add |

### P1 - 커밋 전 검증

| 작업 | 설명 |
|------|------|
| 빌드 검증 | `npm run build` 성공 확인 |
| ESLint 검증 | `npm run lint` 에러 없음 확인 |
| 테스트 실행 | `npm run test:run` 통과 확인 |

### P2 - 리팩토링 (선택적)

| 작업 | 파일 | 설명 |
|------|------|------|
| ToastState 추출 | `types/toast.ts` | 공통 타입 파일 생성 |
| useToast 활용 | 전체 | 기존 훅 활용 또는 확장 |
| LoadingOverlay 추출 | `components/ui/` | 공통 컴포넌트 생성 |

### P3 - 선택적 개선

| 작업 | 파일 | 설명 |
|------|------|------|
| APIStatusMonitor confirm 제거 | `APIStatusMonitor.tsx:91` | Undo Toast로 대체 |
| ConfirmModal 컴포넌트 | `components/ui/` | 위험 작업용 모달 |

### P4 - Blueprint AI BOM

| 파일 | 변경 수 | 상태 |
|------|---------|------|
| WorkflowPage.tsx | 2 | 대기 |
| DetectionRow.tsx | 1 | 대기 |
| SymbolVerificationSection.tsx | 3 | 대기 |
| WorkflowSidebar.tsx | 2 | 대기 |
| HomePage.tsx | 1 | 대기 |
| RelationList.tsx | 1 | 대기 |
| APIKeySettings.tsx | 1 | 대기 |

**총 11개 변경 필요**

---

## 7. 권장 커밋 순서

### 7.1 첫 번째 커밋 (현재 변경 사항)

```bash
# 1. .gitignore 수정 먼저
# 2. 모든 파일 스테이징
git add .todo/
git add web-ui/src/

# 3. 커밋
git commit -m "feat(web-ui): Toast 알림 시스템 전면 적용

- alert() → Toast 컴포넌트 전환 (15개 파일)
- confirm() 제거 (복구 가능 작업만)
- 커스텀 훅에 onShowToast 콜백 패턴 적용
- 클래스 컴포넌트 Toast 지원
- Loading overlay 및 개별 API 제어 추가

변경 파일:
- ErrorBoundary, YOLOModelManager, ContainerManager
- APIStatusMonitor, APIDetail, Admin
- useAPIDetail, api-detail/index
- BlueprintFlowBuilder, BlueprintFlowList
- ExecutionStatusPanel, useContainerStatus
- useImageUpload, Dashboard
- ResultActions (신규 추가)

🤖 Generated with Claude Code"
```

### 7.2 후속 커밋 (리팩토링)

```bash
# P2 리팩토링
git commit -m "refactor(web-ui): ToastState 공통 타입 추출

- types/toast.ts 생성
- 11개 파일에서 중복 인터페이스 제거
- useToast 훅 활용 검토

🤖 Generated with Claude Code"
```

---

## 8. 체크리스트

### 커밋 전 필수 확인

- [ ] .gitignore에서 `**/results/*` 패턴 수정
- [ ] `git add -f web-ui/src/components/results/ResultActions.tsx` 실행
- [ ] `npm run build` 성공
- [ ] `npm run lint` 에러 없음
- [ ] `npm run test:run` 통과

### 리팩토링 검토

- [ ] ToastState 공통 타입 추출 여부 결정
- [ ] useToast 훅 활용 여부 결정
- [ ] LoadingOverlay 공통 컴포넌트 추출 여부 결정
- [ ] ConfirmModal 컴포넌트 생성 여부 결정

---

## 9. 변경 내역

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-01 | 최초 분석 작성, 15개 파일 변경 사항 문서화 |

---

**작성자**: Claude Code
**마지막 업데이트**: 2026-01-01
