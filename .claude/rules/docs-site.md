---
paths:
  - "docs-site/**"
---

# 문서 사이트 규칙

## 코드 변경 시 문서 동기화 필수

| 변경 유형 | 업데이트 대상 |
|----------|-------------|
| 새 API 서비스 추가 | `docs-site/docs/system-overview/` + `devops/` |
| 새 노드 타입 추가 | `docs-site/docs/blueprintflow/node-catalog.md` |
| 파이프라인 흐름 변경 | `docs-site/docs/analysis-pipeline/` 다이어그램 |
| 새 검증 레벨 추가 | `docs-site/docs/agent-verification/` |
| Docker 서비스 변경 | `docs-site/docs/devops/docker-compose.md` |
| 프론트엔드 라우트 추가 | `docs-site/docs/frontend/routing.md` |

## 빌드 확인

```bash
cd docs-site && npm run build
```

## 다이어그램 전략 (IMPORTANT: Mermaid 사용 금지)

**Mermaid 대신 커스텀 React TSX 컴포넌트 사용** (번들 0, 다크모드 자동, 완전 제어)

| 컴포넌트 | 용도 | 파일 |
|----------|------|------|
| `<FlowDiagram>` | 플로우차트 (LR/TD), 상태 다이어그램 | `src/components/diagrams/FlowDiagram.tsx` |
| `<SequenceDiagram>` | 시퀀스 다이어그램 (API 흐름) | `src/components/diagrams/SequenceDiagram.tsx` |

- 글로벌 등록: `src/theme/MDXComponents.tsx` → import 불필요
- 다크모드: `color-mix(in srgb, color 55%, var(--ifm-background-color))` 자동 적용
- **새 다이어그램 추가 시**: Mermaid 블록 대신 TSX 컴포넌트 사용

**상세 가이드**: `.claude/skills/diagram-strategy.md`

## 문서 작성 표준 (E05-S01)

### Frontmatter 필수 필드
- `sidebar_position`, `title`, `description` 필수
- `tags` 권장 (분류: architecture, yolo, ocr, frontend, customer, api 등)

### 페이지 헤더 표준
- H1 바로 아래에 **blockquote 요약** 필수
- 예: `> 이 페이지가 무엇을 설명하는지 한 문장으로 요약`

### 섹션 순서 표준
1. `## 개요` 또는 `## 접속 방법` (필수)
2. `## 구조` 또는 `## 탭 구성` (선택)
3. `## 상세 설명` (필수)
4. `## 설정` 또는 `## 환경변수` (선택)
5. `## 관련 API` (API 연동 시 필수)
6. `## 관련 문서` (필수)

### 표준 표 형식 (4종)
- **Type A**: `| URL | 권한 | 설명 |` — 접속 정보
- **Type B**: `| 경로 | 페이지 | 설명 | 가이드 |` — 라우트 맵
- **Type C**: `| 탭 | 설명 | 주요 동작 |` — 탭/기능
- **Type D**: `| 기능 | 설명 |` — 기능 목록

### 문체 규칙
- 건조한 운영/개발 문체 (마케팅 문체 금지)
- 숫자 명시: "52개 라우트" ✅, "다양한 라우트" ❌
- 추측 금지: 코드/라우트/컴포넌트 실제 확인 후 작성

### Anchor 기반 복합 문서
- 하나의 페이지에 여러 기능: `## 섹션명 {#anchor-id}` 사용
- 다른 문서에서 `[링크텍스트](/docs/page#anchor-id)` 로 참조
