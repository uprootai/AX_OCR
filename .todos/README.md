# .todos - 작업 추적 디렉토리

> AX POC 프로젝트의 작업 기록 및 미완료 작업 관리
> **최종 업데이트**: 2025-12-24

---

## 현재 상태 요약

### 완료된 작업 (2025-12-23)

| 작업 | 상태 | 비고 |
|------|------|------|
| Blueprint AI BOM v2 통합 | ✅ 완료 | Phase 1-7 모두 완료 |
| GD&T 파서 (Phase 7) | ✅ 완료 | 데이텀 검출 수정 완료 |
| 이미지 크기 저장 | ✅ 완료 | 세션 업로드 시 자동 추출 |
| Implementation Guide | ✅ 완료 | 파일 삭제됨 (구현 완료) |
| TypedDict 타입 변환 | ✅ 완료 | 16개 타입 정의, 5개 서비스 적용 |
| Export 스크립트 | ✅ 완료 | 납품 패키지 자동 생성 |
| 단위 테스트 추가 | ✅ 완료 | 27개 테스트 통과 |
| Active Learning 검증 큐 | ✅ 완료 | 백엔드 + API + 프론트엔드 UI |
| **Feedback Loop Pipeline (v8.0)** | ✅ 완료 | YOLO 재학습 데이터셋 내보내기 |
| **온프레미스 배포 (v8.0)** | ✅ 완료 | docker-compose.onprem.yml |
| **ESLint Fast Refresh 수정** | ✅ 완료 | 6개 컴포넌트 수정 |

---

## 남은 파일 및 진행 계획

### 1. `2025-12-19_blueprint_ai_bom_expansion_proposal.md`

**상태**: 기획 검토 단계 | **우선순위**: 중간

| 항목 | 내용 | 진행 상태 |
|------|------|----------|
| VLM 자동 분류 | GPT-4V/Claude로 도면 타입 자동 분류 | 📋 검토 중 |
| GNN 기반 관계 분석 | 그래프 신경망으로 부품 관계 학습 | 📋 연구 단계 |
| Active Learning | 저신뢰 검출 우선 검증 큐 | ✅ 완료 |
| 피드백 루프 | 검증 → 모델 재학습 파이프라인 | 📋 향후 계획 |

**다음 단계**:
1. VLM API 비용 분석 (GPT-4V vs Claude 3.5)
2. 파일럿 테스트 (10개 도면)
3. ROI 검토 후 구현 결정

---

### 2. `2025-12-14_export_architecture.md`

**상태**: 핵심 구현 완료 | **우선순위**: 중간

| 항목 | 내용 | 진행 상태 |
|------|------|----------|
| Export 스크립트 | `scripts/export/export_package.py` | ✅ 완료 |
| 템플릿 Export | 워크플로우 + 설정 패키징 | ✅ 완료 |
| Docker 설정 생성 | docker-compose.yml 자동 생성 | ✅ 완료 |
| 설치/시작 스크립트 | install.sh, start.sh, stop.sh | ✅ 완료 |
| 문서 자동 생성 | INSTALL.md, USER_MANUAL.md | ✅ 완료 |
| 프론트엔드 모듈 분리 | builder/runtime/verification 분리 | 📋 향후 |

**사용법**:
```bash
python scripts/export/export_package.py --customer "고객명" --output ./export
```

---

### 3. `2025-12-14_integration_strategy.md`

**상태**: 대부분 완료 | **우선순위**: 낮음

| 항목 | 내용 | 진행 상태 |
|------|------|----------|
| React 재작성 | Streamlit → React 마이그레이션 | ✅ 완료 |
| BOM Verification UI | 검증 페이지 구현 | ✅ 완료 |
| 성능 최적화 | Virtual DOM, 코드 스플리팅 | ✅ 완료 |

**남은 작업**: 없음 (참조용으로 보관)

---

## 향후 작업 우선순위

### 🔴 높음 (다음 스프린트)

1. ~~**verification_router.py 리팩토링**~~ - ✅ 완료 (schemas 분리, response_model 추가)
2. ~~**verificationApi 프론트엔드 추가**~~ - ✅ 완료 (api.ts에 10개 함수 추가)
3. **MCP Panel 도면 대량 테스트** - 다양한 검출 케이스 검증
4. **프론트엔드 UI 안정화** - 버그 수정 및 UX 개선
5. **GD&T 검출 정확도 개선** - 더 많은 데이텀 패턴 추가

### 🟡 중간 (2주 이내)

1. **온프레미스 패키징 테스트** - 실제 고객사 환경 검증
2. **VLM 파일럿 테스트** - expansion_proposal 검증

### 🟢 낮음 (향후 검토)

1. **GNN 기반 관계 분석** - 연구 단계
2. ~~**피드백 루프**~~ - ✅ v8.0에서 구현 완료 (`/feedback/*` API)
3. **VLM 자동 분류** - GPT-4V/Claude 비용 분석 후 결정
4. **프론트엔드 Feedback UI** - 관리자 페이지에 내보내기 UI 추가 (선택)

---

## 서비스 상태 (2025-12-23)

| 서비스 | 포트 | 상태 |
|--------|------|------|
| Blueprint AI BOM Backend | 5020 | ✅ healthy |
| Blueprint AI BOM Frontend | 3001 | ✅ running |
| YOLO | 5005 | ✅ GPU |
| eDOCr2 | 5002 | ✅ healthy |
| Gateway | 8000 | ✅ running |

---

## Active Learning 검증 큐 (구현 완료)

### 우선순위 분류
| 우선순위 | 조건 | 설명 |
|---------|------|------|
| CRITICAL | 신뢰도 < 0.7 | 즉시 확인 필요 (빨간색) |
| HIGH | 심볼 연결 없음 | 연결 확인 필요 (주황색) |
| MEDIUM | 신뢰도 0.7-0.9 | 검토 권장 (노란색) |
| LOW | 신뢰도 ≥ 0.9 | 자동 승인 후보 (초록색) |

### API 엔드포인트
```
# Active Learning (검증)
GET  /verification/queue/{session_id}        # 검증 큐 조회
GET  /verification/stats/{session_id}        # 검증 통계
POST /verification/verify/{session_id}       # 단일 항목 검증
POST /verification/bulk-approve/{session_id} # 일괄 승인
POST /verification/auto-approve/{session_id} # 자동 승인 (≥0.9)
GET  /verification/training-data             # 재학습 데이터

# Feedback Loop (v8.0)
GET  /feedback/stats                         # 피드백 통계
GET  /feedback/sessions                      # 검증 완료 세션 목록
POST /feedback/export/yolo                   # YOLO 데이터셋 내보내기
GET  /feedback/exports                       # 내보내기 목록
GET  /feedback/health                        # 서비스 상태
```

### 관련 파일
- `backend/services/active_learning_service.py`
- `backend/routers/verification_router.py`
- `frontend/src/components/VerificationQueue.tsx`
- `backend/services/feedback_pipeline.py` (v8.0)
- `backend/routers/feedback_router.py` (v8.0)

---

## 파일 관리 규칙

1. 완료된 구현 가이드는 삭제 (코드에 반영됨)
2. 향후 계획 문서는 유지
3. 작업 전 README 업데이트

---

## 일관성 점검 문서

새 기능 구현 후 아래 문서를 참조하여 코드베이스 전체 일관성을 확보하세요:

| 파일 | 용도 | 상태 |
|------|------|------|
| [`2025-12-23_v8_consistency_checklist.md`](./2025-12-23_v8_consistency_checklist.md) | v8.0 버전 불일치 및 권장 수정 사항 | ✅ 완료 |
| [`2025-12-24_v8_post_commit_tasks.md`](./2025-12-24_v8_post_commit_tasks.md) | v8.0 커밋 후 일관성 작업 (verification_router 리팩토링 등) | 🔄 진행 중 |

### 버전 관리 주의사항
새 버전 릴리즈 시 반드시 업데이트해야 할 파일:
- `blueprint-ai-bom/README.md` - 메인 README 버전
- `gateway-api/api_specs/blueprint-ai-bom.yaml` - API 스펙 버전
- `blueprint-ai-bom/docs/README.md` - 문서 버전
- `.todos/README.md` - 작업 추적 버전
