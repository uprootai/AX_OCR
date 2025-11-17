# 도면 OCR 프로젝트 - Claude Skills

이 디렉토리에는 도면 OCR 및 제조 견적 자동화 시스템을 위한 커스텀 Skills가 포함되어 있습니다.

## 📚 사용 가능한 Skills

### 1. **doc-updater** - 문서 자동 업데이트
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

**언제 사용하나요?**
- 새로운 기능 추가 후
- 버그 수정 후
- 주요 리팩토링 완료 후
- 매주 금요일 정기 업데이트

---

### 2. **code-janitor** - 잔 오류 자동 수정
**용도**: 코드 스멜, 베스트 프랙티스 위반, 잔 오류를 자동으로 탐지 및 수정

**실행 방법**:
```
/skill code-janitor
```

**주요 기능**:
- Python: 타입 힌트, 미사용 import, 긴 함수, 하드코딩 값
- TypeScript: console.log, any 타입, useEffect 의존성, Key prop
- Docker: 미사용 이미지/컨테이너, 로그 크기, Health check
- 보안: 하드코딩 시크릿, SQL Injection, CORS 설정
- 성능: 동기 I/O, 불필요한 재계산, 메모리 누수

**언제 사용하나요?**
- PR 생성 전 (코드 리뷰 준비)
- 매일 아침 첫 작업 (하루 1회)
- 배포 전 최종 점검
- CI/CD 파이프라인에 통합

---

### 3. **ux-enhancer** - UI/UX 고도화
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
- **Phase 6**: 성능 최적화 (Skeleton, Lazy Loading)

**언제 사용하나요?**
- 신규 UI 컴포넌트 개발 시
- 사용자 피드백 반영 시
- 접근성 감사 후
- 주요 릴리스 전

---

## 🚀 빠른 시작

### Skill 실행하기

Claude Code 세션에서:

```
/skill doc-updater
/skill code-janitor
/skill ux-enhancer
```

### 여러 Skills 연속 실행

```bash
# 배포 전 체크리스트
1. /skill code-janitor  # 코드 품질 검사
2. /skill doc-updater   # 문서 업데이트
3. git add . && git commit -m "chore: Pre-deploy cleanup"
```

---

## 📋 권장 워크플로우

### 1. 일일 루틴 (매일 오전 9시)
```bash
/skill code-janitor --auto-fix
# → 코드 품질 보고서 확인
# → Critical 이슈 즉시 수정
```

### 2. 기능 개발 완료 후
```bash
# 1. 코드 정리
/skill code-janitor

# 2. 문서 업데이트
/skill doc-updater

# 3. PR 생성
git push origin feature/new-feature
```

### 3. UI 개선 프로젝트
```bash
# Phase별로 순차 실행
/skill ux-enhancer
# → Phase 1 완료 후 테스트
# → Phase 2 진행...
```

### 4. 릴리스 준비
```bash
# 1. 코드 품질 최종 점검
/skill code-janitor --strict

# 2. 문서 최종 업데이트
/skill doc-updater

# 3. CHANGELOG 확인
cat /tmp/test_results/CHANGELOG_$(date +%Y-%m-%d).md

# 4. 배포
docker-compose build && docker-compose up -d
```

---

## 🎯 각 Skill의 출력물

### doc-updater 출력
- `/tmp/test_results/CHANGELOG_YYYY-MM-DD.md`
- 업데이트된 `CLAUDE.md`
- 업데이트된 `README.md`
- 버전 번호 증가

### code-janitor 출력
- `/tmp/test_results/CODE_QUALITY_YYYY-MM-DD.md`
- 자동 수정된 코드 (git commit)
- Linting 보고서
- 성능 개선 제안

### ux-enhancer 출력
- 새로운 UI 컴포넌트 파일들
- 업데이트된 `TestGateway.tsx`
- 설치된 npm 패키지 목록
- Lighthouse 성능 보고서

---

## 💡 팁

### 1. Skill 조합 사용
```bash
# UI 개선 후 자동으로 문서화
/skill ux-enhancer && /skill doc-updater
```

### 2. 특정 서비스만 검사
```bash
# 추후 구현 예정
/skill code-janitor --service gateway-api
/skill doc-updater --file CLAUDE.md
```

### 3. Dry-run 모드
```bash
# 실제 변경 없이 미리보기
/skill code-janitor --dry-run
/skill doc-updater --preview
```

---

## 🔧 커스터마이징

각 Skill은 `.md` 파일이므로 프로젝트에 맞게 수정 가능합니다:

```bash
vim .claude/skills/code-janitor.md
# 검사 항목 추가/제거
# 자동 수정 규칙 변경
```

---

## 📊 예상 효과

| Skill | 시간 절감 | 품질 향상 |
|-------|----------|----------|
| **doc-updater** | 주 2시간 → 10분 (90% ↓) | 문서 최신성 100% |
| **code-janitor** | 리뷰 1시간 → 20분 (67% ↓) | 버그 50% ↓ |
| **ux-enhancer** | UI 개발 2주 → 1주 (50% ↓) | 사용성 점수 95+ |

---

## 🐛 문제 해결

### Skill이 인식 안될 때
```bash
# Skills 디렉토리 확인
ls -la /home/uproot/ax/poc/.claude/skills/

# 파일 권한 확인
chmod 644 /home/uproot/ax/poc/.claude/skills/*.md
```

### Skill 실행 오류
```bash
# 로그 확인
# Claude Code 세션에서 오류 메시지 확인
# 필요 시 Skill 파일의 문법 검사
```

---

**마지막 업데이트**: 2025-11-16
**버전**: 1.0.0
**작성자**: Claude Code
