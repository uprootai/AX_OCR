# 도면 OCR 프로젝트 - Claude Skills

이 디렉토리에는 도면 OCR 및 제조 견적 자동화 시스템을 위한 커스텀 Skills가 포함되어 있습니다.

## 📚 사용 가능한 Skills (5개)

### 1. **feature-implementer** - 단계별 기능 구현 ⭐ NEW
**용도**: 계획 문서 기반 단계별 기능 구현 및 리스크 관리

**자동 적용**: 다음 요청 시 자동 적용됨
- "새 기능 구현해줘"
- "이 계획대로 구현해줘"
- ".todos/에 있는 계획 실행해줘"

**주요 기능**:
- 계획 문서 파싱 및 진행 상태 추적
- 단계별 실행 (Phase-by-Phase)
- 각 단계 완료 후 사용자 승인 요청
- Quality Gate 검증 (빌드, 테스트, 린트)
- 리스크 평가 (🟢Low/🟡Medium/🟠High/🔴Critical)
- Git 추적 파일 삭제 → 일반 확인 (복구 가능)
- Git 미추적/DB 삭제 → 명시적 확인 (복구 불가)
- Git 자동 커밋 생성
- 중단 후 재개 가능

---

### 2. **workflow-optimizer** - 워크플로우 최적화
**용도**: 도면 유형 분석 및 최적 BlueprintFlow 파이프라인 자동 추천

**실행 방법**:
```
/skill workflow-optimizer
```

**주요 기능**:
- 도면 특성 분석 (심볼 종류, 텍스트 밀도, 복잡도)
- 요구사항 파악 (속도 vs 정확도, 특정 정보 추출 목표)
- 최적 YOLO 모델 + 후처리 조합 추천
  - **Scenario A**: 기계 부품 (symbol-detector + CropAndScale + eDOCr2)
  - **Scenario B**: 용접 도면 (symbol-detector + BackgroundRemoval + eDOCr2)
  - **Scenario C**: GD&T 공차 (gdt-detector + Loop + SkinModel)
  - **Scenario D**: 텍스트 단순 (Skip YOLO + EDGNet + eDOCr2)
  - **Scenario E**: 영문 도면 (text-region + PaddleOCR + VL)
- 예상 성능 메트릭 제공 (처리 시간, 정확도, 메모리)
- BlueprintFlow 템플릿 자동 생성

**시나리오별 예상 성능**:
| 시나리오 | 속도 | 정확도 | 적합한 도면 |
|---------|------|--------|------------|
| A. 기계 부품 | ⚡⚡ (2.5초) | 92% | 베어링, 기어, 샤프트 |
| B. 용접 도면 | ⚡⚡⚡ (1.2초) | 90% | 용접 기호 7가지 |
| C. GD&T 공차 | ⚡ (3.5초) | 85% | 기하공차 분석 |
| D. 텍스트 단순 | ⚡⚡⚡⚡ (0.8초) | 80% | 주석/메모만 |
| E. 영문 도면 | ⚡ (4.0초) | 90% | 해외 제조사 |

---

### 3. **doc-updater** - 문서 자동 업데이트
**용도**: 코드 변경 사항을 추적하고 프로젝트 문서를 자동으로 업데이트

**실행 방법**:
```
/skill doc-updater
```

**주요 기능**:
- 최근 변경된 파일 자동 탐지
- CLAUDE.md 최근 구현 내역 업데이트
- 버전 번호 및 날짜 자동 갱신
- CHANGELOG 생성
- API 문서 자동 생성
- **Dashboard 설정 파일 동기화 검사** (신규 API 누락 감지)

**언제 사용하나요?**
- 새로운 기능 추가 후
- 새 API 추가 후 (Dashboard 설정 파일 검사)
- 버그 수정 후
- 주요 리팩토링 완료 후

---

### 4. **code-janitor** - 잔 오류 자동 수정
**용도**: 코드 스멜, 베스트 프랙티스 위반, 잔 오류를 자동으로 탐지 및 수정

**실행 방법**:
```
/skill code-janitor
/skill code-janitor --auto-fix
```

**주요 기능**:
- Python: 타입 힌트, 미사용 import, 긴 함수, 하드코딩 값
- TypeScript: console.log, any 타입, useEffect 의존성, Key prop
- Docker: 미사용 이미지/컨테이너, 로그 크기, Health check
- 보안: 하드코딩 시크릿, SQL Injection, CORS 설정
- 성능: 동기 I/O, 불필요한 재계산, 메모리 누수

**언제 사용하나요?**
- PR 생성 전 (코드 리뷰 준비)
- 매일 아침 첫 작업
- 배포 전 최종 점검

---

### 5. **ux-enhancer** - UI/UX 고도화
**용도**: 2025년 엔터프라이즈 UI/UX 베스트 프랙티스 적용

**실행 방법**:
```
/skill ux-enhancer
```

**주요 기능**:
- **Phase 1**: 파일 업로드 UX (드래그 앤 드롭, 진행률, 미리보기)
- **Phase 2**: 분석 진행 상태 시각화 (단계별 진행률, 예상 시간)
- **Phase 3**: 결과 시각화 (인터랙티브 차트, 다운로드)
- **Phase 4**: 접근성 (WCAG 2.1 AA, 키보드 네비게이션, ARIA)
- **Phase 5**: 다크모드 지원
- **Phase 6**: 에러 처리 & Graceful Degradation
- **Phase 7**: 성능 최적화 (Skeleton, Lazy Loading)

---

## 🚀 자동 적용 방식

스킬은 요청 내용에 따라 **자동으로 적용**됩니다:

| 요청 예시 | 적용되는 스킬 |
|-----------|--------------|
| "새 기능 구현해줘" | feature-implementer |
| "이 도면 분석해줘" | workflow-optimizer |
| "문서 업데이트해줘" | doc-updater |
| "코드 정리해줘" | code-janitor |
| "UI 개선해줘" | ux-enhancer |

### 권장 워크플로우

#### 새 기능 구현 시
```
1. 계획 문서 작성 (.todos/에)
2. "이 계획대로 구현해줘" → 자동으로 단계별 진행
3. 각 Phase 완료 후 Quality Gate 검증
4. 자동 Git 커밋
```

#### 새 도면 유형 분석 시
```
1. "이 도면 최적 파이프라인 추천해줘"
2. BlueprintFlow에서 추천 템플릿 적용
3. 테스트 후 성능 확인
```

#### 배포 준비 시
```
1. "코드 품질 검사해줘"
2. "문서 업데이트해줘"
3. 커밋 & 푸시
```

---

## 📁 Templates

변경 요약 템플릿 사용 가능:
```
.claude/templates/change-summary-template.md
```

기능 구현 시 자동으로 생성되는 변경 요약:
- 파일 변경 목록 (Created/Modified/Deleted)
- 리스크 레벨별 분류
- Quality Gate 결과
- Git 커밋 정보

---

## 📊 예상 효과

| Skill | 시간 절감 | 품질 향상 |
|-------|----------|----------|
| **feature-implementer** | 구현 40% ↓ | 리스크 사전 인지 |
| **workflow-optimizer** | 파이프라인 선택 80% ↓ | 정확도 +10% |
| **doc-updater** | 문서화 90% ↓ | 최신성 100% |
| **code-janitor** | 리뷰 67% ↓ | 버그 50% ↓ |
| **ux-enhancer** | UI 개발 50% ↓ | 사용성 95+ |

---

## 🔧 리스크 레벨 가이드

| 레벨 | 아이콘 | 조건 | 요구 사항 |
|------|--------|------|----------|
| Low | 🟢 | 새 파일, 문서, 테스트 | 자동 진행 |
| Medium | 🟡 | 기존 코드 수정, 설정 변경 | 사용자 승인 |
| High | 🟠 | DB 변경, API 변경, 의존성 | 상세 검토 |
| Critical | 🔴 | 파일 삭제, Breaking changes | 명시적 확인 |

---

**마지막 업데이트**: 2025-12-23
**버전**: 2.0.0
**작성자**: Claude Code
