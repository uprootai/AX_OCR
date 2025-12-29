---
name: doc-updater
description: Automatically tracks project changes and updates relevant documentation including CLAUDE.md, README, CHANGELOG, and API docs
allowed-tools: [read, glob, grep, bash]
---

# Documentation Updater Skill

**목적**: 프로젝트 변경 사항을 자동으로 추적하고 관련 문서를 업데이트

## 작업 단계

### 1. 변경 사항 분석
- 최근 수정된 파일 탐지 (git diff 또는 파일 타임스탬프)
- 변경된 API 엔드포인트, 함수 시그니처 파악
- 새로운 기능, 버그 수정, 성능 개선 분류

### 2. 영향 받는 문서 식별
다음 문서들을 체크:
- `/home/uproot/ax/poc/CLAUDE.md` - LLM 가이드
- `/home/uproot/ax/poc/README.md` - 프로젝트 개요
- `/home/uproot/ax/poc/web-ui/README.md` - 프론트엔드 문서
- `/tmp/test_results/*.md` - 테스트 및 수정 보고서
- API 문서 (OpenAPI/Swagger)

### 3. 자동 업데이트 항목

#### CLAUDE.md 업데이트
- **최근 구현 내역** 섹션 (line 228-236)
  - 날짜를 오늘로 업데이트
  - 작업 목록에 새 항목 추가
- **주요 파일 요약** 섹션 (line 209-226)
  - 라인 수 변경 반영
  - 새 함수 추가 시 목록 업데이트
- **성능 메트릭** 섹션 (line 172-180)
  - 벤치마크 결과 반영
  - 목표 대비 현재값 업데이트

#### 버전 관리
- 마지막 업데이트 날짜 자동 갱신
- 버전 번호 증가 (Semantic Versioning)
  - Patch: 버그 수정, 문서 업데이트
  - Minor: 새 기능 추가
  - Major: Breaking changes

### 4. 변경 로그 생성
`/tmp/test_results/CHANGELOG_YYYY-MM-DD.md` 형식으로 생성:

```markdown
# 변경 로그 - YYYY-MM-DD

## Added (추가)
- [Feature] YOLO 시각화 이미지 Base64 인코딩 지원
- [UI] TestGateway에 시각화 카드 추가

## Changed (변경)
- [API] DetectionResponse에 visualized_image 필드 추가
- [Type] AnalysisResult에 yolo_results 타입 정의

## Fixed (수정)
- [Bug] 시각화 옵션 체크해도 이미지 표시 안되던 문제
- [Bug] Skin Model 비숫자 값 파싱 오류

## Performance (성능)
- [Improve] Base64 인코딩 오버헤드: +10ms (무시 가능)

## Documentation (문서)
- CLAUDE.md 업데이트: 시각화 기능 추가
- VISUALIZATION_FIX_REPORT.md 생성
```

### 5. 실행 방법

**자동 모드** (git hook 활용):
```bash
# .git/hooks/post-commit에 추가
#!/bin/bash
echo "Updating documentation..."
claude skill doc-updater
```

**수동 모드**:
```bash
# Claude Code에서
/skill doc-updater
```

### 6. 체크리스트

수행할 작업:
- [ ] 최근 7일 내 수정된 Python/TypeScript 파일 탐지
- [ ] 함수 시그니처 변경 확인 (Pydantic 모델, API 엔드포인트)
- [ ] CLAUDE.md 최근 구현 내역 업데이트
- [ ] 버전 번호 및 날짜 갱신
- [ ] CHANGELOG 생성
- [ ] README.md의 Features 섹션 업데이트 (새 기능 추가 시)
- [ ] API 문서 자동 생성 (FastAPI → OpenAPI JSON)
- [ ] **Dashboard 설정 동기화 검사** (아래 섹션 참조)

### 6-1. Dashboard 설정 동기화 검사 (신규 API 추가 시)

신규 API 추가 후 Dashboard 설정 파일이 누락되면 "API를 찾을 수 없습니다" 오류가 발생합니다.

**검사 대상 파일**:
```
gateway-api/api_specs/*.yaml                      # API 스펙 (기준)
web-ui/src/components/monitoring/APIStatusMonitor.tsx  # Dashboard 모니터링
web-ui/src/pages/admin/APIDetail.tsx                   # Dashboard 설정 페이지
```

**검사 방법**:
1. `api_specs/` 폴더의 YAML 파일에서 API ID 목록 추출
2. `APIStatusMonitor.tsx`의 `DEFAULT_APIS` 배열과 비교
3. `APIDetail.tsx`의 `DEFAULT_APIS`, `HYPERPARAM_DEFINITIONS`, `DEFAULT_HYPERPARAMS`와 비교
4. 누락된 API가 있으면 경고 출력

**예시 경고**:
```
⚠️ Dashboard 동기화 필요:
- API 'new_api'가 api_specs/new-api.yaml에 정의되었지만:
  - APIDetail.tsx의 DEFAULT_APIS에 없음
  - APIDetail.tsx의 HYPERPARAM_DEFINITIONS에 없음
```

### 7. 스마트 기능

#### A. 중복 방지
- 이미 문서화된 항목은 스킵
- 날짜별로 변경 로그 병합

#### B. 우선순위 판단
Breaking changes > 새 기능 > 버그 수정 > 문서 업데이트

#### C. 링크 자동 생성
- 파일명:라인번호 형식으로 참조 생성
- 관련 이슈/PR 번호 자동 링크

## 예상 효과

- ✅ 문서가 항상 최신 상태 유지
- ✅ 팀원들이 변경 사항을 쉽게 파악
- ✅ LLM이 정확한 컨텍스트로 작업 가능
- ✅ 수동 문서 작업 시간 90% 절감
