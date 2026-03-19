# AX POC — Codex Agent Instructions

> 기계 도면 자동 분석 및 제조 견적 시스템 | FastAPI + React 19 + YOLO v11 + eDOCr2 + Docker
> 이 파일은 Codex CLI가 읽는 프로젝트 규칙입니다. Claude Code의 CLAUDE.md와 동일한 규칙을 공유합니다.

---

## 프로젝트 구조

```
ax/poc/
├── blueprint-ai-bom/          # 핵심 BOM 추출 시스템
│   ├── backend/               # FastAPI (포트 5020)
│   │   ├── routers/analysis/  # 분석 API (dimension, core)
│   │   ├── services/          # 비즈니스 로직 (dimension_parser, merger 등)
│   │   └── schemas/           # Pydantic 스키마
│   └── frontend/              # React 19 + Vite (포트 5173)
├── gateway-api/               # API Gateway (포트 5050)
├── web-ui/                    # 메인 웹 UI (React 19 + Vite)
├── models/                    # ML 모델 서비스 (YOLO, eDOCr2 등)
├── docker-compose.yml         # 전체 서비스 오케스트레이션
└── .todo/                     # 작업 추적 (BMAD-Lite)
```

## API 서비스 레지스트리 (21개)

| 카테고리 | 서비스 | 포트 |
|---------|--------|------|
| Detection | YOLO v11 | 5005 |
| OCR | eDOCr2, PaddleOCR, EasyOCR, TrOCR, SuryaOCR, DocTR | 5002, 5008-5012 |
| Segmentation | SkinModel, SAM2 | 5003, 5006 |
| Preprocessing | Deskew, Denoiser | 5013, 5014 |
| Analysis | Blueprint AI BOM | 5020 |
| Visualization | Annotation | 5015 |
| AI | OpenAI Integration | 5030 |
| Orchestrator | Gateway API | 5050 |

---

## CRITICAL: 절대 금지 규칙

### 1. base64 이미지 전송 금지
```bash
# ❌ 금지
curl -d '{"image": "base64..."}'

# ✅ 필수 — multipart/form-data
curl -F "file=@image.png" http://localhost:5005/api/v1/detect
```

### 2. 파일 크기 제한
| 라인 수 | 조치 |
|---------|------|
| < 500줄 | ✅ 유지 |
| 500-1000줄 | ⚠️ 리팩토링 고려 |
| > 1000줄 | **즉시 분리** — 배럴 re-export 패턴 사용 |

### 3. 금지 패턴
- Mermaid 다이어그램 사용 → TSX 컴포넌트 (`FlowDiagram`, `SequenceDiagram`) 사용
- 존재하지 않는 API 파라미터 추정 → `api_specs/*.yaml` 확인 필수
- `confidence_threshold` 기본값은 **0.4** (0.5 아님) — `@AX:WARN`
- 마케팅 용어 사용 금지 (문서): "좋습니다", "강력합니다", "혁신적인", "완벽한"

---

## 코드 품질 기준

### Python (FastAPI)
- 타입 힌트 필수 (함수 시그니처 + 반환값)
- Pydantic v2 스키마 사용
- `ruff` 포매팅 준수
- E2E 테스트는 회귀 테스트와 분리: `pytest -m e2e`
- Python 구문 검증: `python3 -c "import ast; ast.parse(open(f).read())"`

### TypeScript (React 19)
- `npx tsc --noEmit` 에러 0
- ESLint 에러 0
- `npm run build` 성공 필수
- React 19 + Vite 환경

### 공통
- 함수당 30줄 이하 권장
- 3단 이상 중첩 금지
- console.log / print 디버깅 코드 제거 후 커밋
- 하드코딩 금지 (설정값은 환경변수 또는 config)

---

## 코드 주석 태그 (AX Tag)

| 태그 | 용도 | 예시 |
|------|------|------|
| `@AX:ANCHOR` | 핵심 진입점, 변경 시 영향 큼 | `// @AX:ANCHOR — 노드 타입 정의` |
| `@AX:WARN` | 주의 필요, 함정/부작용 있음 | `# @AX:WARN — confidence 기본값 0.4` |
| `@AX:TODO` | 향후 개선 필요 | `// @AX:TODO — 캐시 레이어 추가` |

---

## BlueprintFlow 노드 시스템

- 29개 노드 타입, 70+ 파라미터 (`web-ui/src/config/nodeDefinitions.ts`)
- 템플릿 파라미터는 반드시 `gateway-api/api_specs/*.yaml`과 동기화
- 금지 파라미터 (API 스펙에 없음): `extract_tolerances`, `analyze_gdt`, `detect_dimensions`

---

## 테스트 실행 규칙

```bash
# Frontend
cd web-ui && npm run test:run       # 단위 테스트
cd web-ui && npm run build          # 빌드 검증

# Backend (E2E 제외)
cd gateway-api && pytest            # 회귀 테스트
cd gateway-api && pytest -m e2e     # E2E만 (별도)

# Blueprint AI BOM
cd blueprint-ai-bom/backend && pytest

# Python 구문 검증 (빠른 체크)
python3 -c "import ast; ast.parse(open('파일경로').read())"
```

---

## 문서 작성 규칙

### Frontmatter 필수 필드
```yaml
title: 페이지 제목
description: 한 줄 설명
tags: [태그1, 태그2]  # 최소 2개
sidebar_position: 1
```

### H1 패턴
```markdown
# 한글 제목 (English Title)
> 한 줄 요약 (마케팅 문구 금지)
```

### 섹션 순서
Overview → 구조/아키텍처 → 상세 → 설정 → Related API → Related Docs

### 표 형식
- Type A: 이름 | 설명 | 비고
- Type B: 속성 | 타입 | 기본값 | 설명
- Type C: 엔드포인트 | 메서드 | 설명
- Type D: 항목 | 상태 | 비고

---

## Dimension Lab (OD/ID/W 실험)

현재 진행 중인 핵심 실험 영역:

### 10가지 분류 방법
1. `diameter_symbol` — Ø 기호 필터링
2. `dimension_type` — eDOCr2 타입 분류
3. `catalog` — ISO 355/JIS B 1512 카탈로그 매칭
4. `composite_signal` — 7-시그널 휴리스틱
5. `position_width` — 위치 기반 W 감지
6. `session_ref` — 세션명 파싱
7. `tolerance_fit` — 공차/끼워맞춤 분석
8. `value_ranking` — 크기 순위 (1st=OD, 2nd=ID, 3rd=W)
9. `heuristic` — 타입→접두사→위치→크기 폴백
10. `full_pipeline` — 전체 파이프라인 (프로덕션)

### 핵심 파일
- `backend/services/dimension_parser.py` — 10가지 방법 구현 (898줄)
- `backend/services/dimension_service.py` — 멀티 OCR 엔진 (427줄)
- `backend/routers/analysis/dimension_router.py` — API 라우터 (1046줄)
- `tests/eval/run_dimension_eval.py` — Eval runner
- `tests/eval/dimension_eval_cases.json` — GT 테스트 케이스 8개

### Eval 실행
```bash
python3 blueprint-ai-bom/tests/eval/run_dimension_eval.py
python3 blueprint-ai-bom/tests/eval/run_dimension_eval.py --benchmark /tmp/dimension_eval_baseline.json
```

---

## Docker 서비스

```bash
# 전체 시작
docker-compose up -d

# 단일 서비스 재빌드
docker-compose up -d --build <서비스명>

# 헬스체크
curl -s http://localhost:5050/api/v1/health
curl -s http://localhost:5020/health
```

서비스명 패턴: `blueprint-ai-bom-backend`, `gateway-api`, `web-ui` 등

---

## Prompt Control (Codex 교차검증용)

Codex가 Claude Code의 교차검증 요청을 받을 때:
- `goal + scope + stop_conditions + output_schema` 구조를 따름
- 기본 reasoning effort: `low` (아키텍처 결정, 모호한 버그, 위험 편집 시만 `medium`)
- 조기 종료: 하나의 추천이 명확히 우세하면 즉시 종료
- 출력: `decision`, `confidence`, `why`, `counter_risk`, `next_action`

---

## 작업 추적 (.todo/)

```
.todo/
├── ACTIVE.md     # 현재 Epic/Story
├── BACKLOG.md    # Epic 인덱스
├── COMPLETED.md  # 완료 아카이브
└── epics/{id}/   # EPIC.md + S01~S0N.md
```

---

**Synced with**: CLAUDE.md, .claude/rules/, .claude/skills/
**Last updated**: 2026-03-19
