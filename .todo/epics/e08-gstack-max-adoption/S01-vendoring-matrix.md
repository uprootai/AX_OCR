# S01: gstack 소스 기준점 + AX 채택 매트릭스 고정

> **Epic**: E08 — Gstack 운영체계 최대 도입
> **상태**: ✅ Done
> **예상**: 1.5d

---

## 설명

외부 `gstack` 기준 소스를 AX 저장소에서 재현 가능한 기준점으로 고정한다.
최대 도입안의 출발점은 upstream 기능 목록이 아니라, AX 저장소에 이미 존재하는 `.claude/commands`, `.claude/hooks`, `web-ui/playwright`, `.github/workflows`, `.todo`와 어떻게 맞물리는지까지 포함한 채택 매트릭스를 만드는 것이다.

산출물은 두 가지다.

1. `gstack` 소스를 특정 커밋으로 고정한 레퍼런스 스냅샷 또는 벤더 디렉터리
2. 모듈별 채택 매트릭스
   - 27개 스킬 전체에 대해 `Adopt / Adapt / Rewrite / Defer`
   - 기존 AX 표면과의 연결 위치
   - 선행 의존성
   - blocker

## 완료 조건

- [x] `gstack` 기준 커밋 해시가 문서에 명시된다.
- [x] AX 관점의 채택/수정/재작성/보류 매트릭스가 27개 스킬 전체에 대해 작성된다.
- [x] `.claude/commands`, `.claude/hooks`, `web-ui/playwright.config.ts`, `.github/workflows/*`, `.gitignore`와의 충돌 지점이 정리된다.
- [x] 도입 범위별 담당 저장소 경로와 선행 의존성이 정리된다.
- [x] 직접 벤더링하지 않을 경우에도 재현 가능한 clone/pin 절차가 문서화된다.

## 변경 범위

| 파일 | 작업 |
|------|------|
| `third_party/gstack/` | 신규 또는 대안 경로 정의 |
| `.todo/epics/e08-gstack-max-adoption/EPIC.md` | 참조 커밋 링크 보강 |
| `.todo/epics/e08-gstack-max-adoption/adoption-matrix.md` | 신규 |
| `.todo/decisions/` | 필요 시 ADR 신규 |
| `.gitignore` | `.gstack` 계열 경로 정책 검토 |

## 에이전트 지시

```text
이 Story를 구현하세요.
- 목표: gstack 기준 소스를 AX 저장소에서 추적 가능한 기준점으로 고정
- 산출물: 벤더 스냅샷 또는 pin 문서 + adoption matrix
- 필수 분석 경로: .claude/commands, .claude/hooks, .claude/settings.local.json, web-ui/playwright.config.ts, web-ui/e2e, blueprint-ai-bom/frontend, .github/workflows, .gitignore
- 주의: "검토만 한 상태"로 끝내지 말고, 이후 Story가 참조할 기준 커밋과 AX 연결 위치까지 명시
- 완료 시: 이 파일의 상태를 ✅ Done으로 변경
```

## 구현 노트

- 검토 기준 로컬 스냅샷은 `/tmp/gstack-review`에 이미 존재한다.
- 현재 pin 기준 upstream은 `https://github.com/garrytan/gstack.git@9eb74debd50b9fdc83b7b9f2061339cb54ed2210`이다.
- 로컬 clone `/home/uproot/ax/git-source/gstack`는 dirty change 없이 clean 상태였다.
- 현재 저장소는 루트 `CLAUDE.md`가 없으므로 deploy/doc 계열 스킬은 단순 채택이 불가능하다.
- `.gstack/`는 repo-local ignored artifact 루트로 고정했다.
- 안전 훅 관련 결함은 S05에서 별도 처리한다.

## 재현 절차

```bash
git clone https://github.com/garrytan/gstack.git /home/uproot/ax/git-source/gstack
cd /home/uproot/ax/git-source/gstack
git checkout 9eb74debd50b9fdc83b7b9f2061339cb54ed2210
```
