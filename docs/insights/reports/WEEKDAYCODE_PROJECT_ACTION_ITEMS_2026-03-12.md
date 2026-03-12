# WeekdayCode 기반 프로젝트 적용 액션 아이템

기준 문서:

- `docs/insights/reports/WEEKDAYCODE_VIDEO_DETAILED_KEY_POINTS_2026-03-12.md`

목적:

- WeekdayCode 27개 영상에서 반복된 운영 철학을 현재 프로젝트에 바로 적용 가능한 실행 항목으로 압축한다.
- 일반론이 아니라 현재 저장소 구조와 이미 도입된 Claude Code / Codex 운영 자산을 기준으로 우선순위를 정한다.
- "무엇을 더 만들까"보다 "무엇을 더 안전하고 싸고 오래 굴러가게 할까"에 초점을 둔다.

## 1. 이 문서의 전제

- WeekdayCode의 반복 메시지는 `생성`보다 `검증`, `유행`보다 `운영`, `과장된 바이브 코딩`보다 `테스트 가능한 구조`에 가깝다.
- 따라서 이 프로젝트의 추가 작업도 새 에이전트를 무한히 붙이는 방향보다, `검증`, `라우팅`, `보안 경계`, `운영 기록`을 강화하는 쪽이 맞다.
- 이미 이 저장소에는 Claude Code 운영층이 상당 부분 정리되어 있다.
- 예를 들어 `.claude/skills/prompt-orchestration-guide.md`, `.claude/commands/codex-cross-check.md`, `.claude/hooks/pre-compact.sh`, `.claude/commands/handoff.md` 같은 자산은 이미 존재한다.
- 반대로 백엔드 실행층과 평가 데이터 축적은 상대적으로 더 강화할 여지가 있다.

## 2. 현재 상태에서 바로 읽히는 강점

### 2.1 프롬프트 운영층은 이미 기반이 있다

- Claude Code와 Codex를 함께 쓰기 위한 `XML contract`, `early stop`, `private think scratchpad`, `Reflector/Curator` 흐름이 이미 문서화되어 있다.
- 즉, 프롬프트 엔지니어링 관점의 1차 뼈대는 이미 들어가 있다.
- 이 덕분에 지금부터는 "새 프롬프트 발명"보다 "운영 데이터를 쌓고 약한 고리를 보강"하는 단계로 넘어가는 편이 맞다.

### 2.2 테스트 자산은 생각보다 넓게 깔려 있다

- `gateway-api/tests/` 아래에 실행기, 라우터, 스키마, 파이프라인 테스트가 다수 존재한다.
- `web-ui` 쪽도 Vitest 기반 테스트 경로가 이미 있다.
- 즉, "테스트가 하나도 없다"가 아니라 "에이전트 운영 특성을 검증하는 테스트가 아직 별도 층으로 정리되지 않았다"에 가깝다.

### 2.3 UI는 이미 다중 공급자 개념을 갖고 있다

- `web-ui/src/pages/admin/api-detail/components/APIKeySettingsPanel.tsx`는 `openai`, `anthropic`, `google`, `local` 공급자를 다룬다.
- 따라서 사용자 인터페이스 레벨에서는 이미 provider-agnostic 방향성이 들어와 있다.
- 문제는 이 철학이 실행 계층까지 완전히 내려가 있지는 않다는 점이다.

## 3. 지금 가장 먼저 추가해야 할 것

## 3.1 Provider Router / Adapter 계층

### 왜 필요한가

- WeekdayCode에서 가장 반복되는 메시지 중 하나는 `특정 모델 종속을 피하라`는 것이다.
- 현재 UI는 여러 공급자를 다루지만, `gateway-api/blueprintflow/executors/vl_executor.py`는 여전히 `http://vl-api:5004/api/v1/analyze`에 직접 결합되어 있다.
- 즉, 관리 화면은 다중 공급자를 전제하지만, 실제 실행 흐름은 아직 단일 서비스 결합이 강하다.

### 무엇을 추가할 것인가

- `gateway-api/adapters/` 또는 `gateway-api/services/` 아래에 공급자 라우터를 둔다.
- 역할은 최소한 세 층으로 나눈다.
- `provider selection`: 현재 작업이 어느 공급자로 가야 하는지 결정
- `model policy`: 기본 모델, fallback 모델, 금지 모델 정책
- `transport adapter`: 실제 API 호출 구현

### 기대 효과

- Claude, OpenAI, Google, Local VL 같은 선택지를 UI와 실행층에서 같은 철학으로 다룰 수 있다.
- 특정 공급자 가격이나 성능이 바뀌어도 전체 워크플로우를 뜯어고치지 않아도 된다.
- Codex를 교차검증용으로 쓰는 현재 전략과도 충돌하지 않는다.

### 1차 구현 범위

- VL executor가 직접 URL을 호출하지 않도록 얇은 adapter 인터페이스 추가
- provider별 설정 로딩 경로 정리
- 기본 모델과 fallback 규칙을 코드로 명시
- 로컬 전용 처리와 외부 전송 처리를 분기

## 3.2 Agent Regression Tests

### 왜 필요한가

- WeekdayCode는 계속 `테스트가 해자다`를 강조한다.
- 현재 테스트는 많지만, 에이전트 운영 규칙 자체를 회귀 검증하는 테스트는 거의 없다.
- 특히 지금 저장소는 프롬프트 계약 층을 이미 도입했기 때문에, 이제는 그 규칙이 실제로 지켜지는지를 확인해야 한다.

### 무엇을 추가할 것인가

- `prompt contract regression tests`
- `provider routing regression tests`
- `fallback safety tests`
- `verification scope tests`

### 검증하고 싶은 대표 규칙

- 충분한 근거가 모이면 추가 탐색을 멈춘다.
- 범위 밖 작업으로 확장하지 않는다.
- 외부 모델 전송이 금지된 케이스를 우회하지 않는다.
- 실패 후 `Reflector/Curator` 패킷이 최소 필드를 유지한다.

### 저장소 기준 후보 위치

- 백엔드: `gateway-api/tests/`
- Claude 운영층 검증용 문서/스크립트: `.claude/tests/` 또는 `docs/insights/experiments/` 성격의 새 디렉터리

### 기대 효과

- 프롬프트 튜닝이 감으로만 굴러가지 않는다.
- Claude Code와 Codex를 섞어 써도 규칙 위반 여부를 반복 확인할 수 있다.
- 장기적으로는 운영 규칙 변경 시 회귀 리스크를 줄일 수 있다.

## 3.3 External Model Egress Policy

### 왜 필요한가

- WeekdayCode는 OpenClaw, 노코드, 바이브 코딩 이야기에서 반복해서 `권한`과 `보안`을 경계한다.
- 현재 저장소에는 비밀정보 스캔과 코드 리뷰 자산은 있지만, 외부 모델 전송 정책은 분리되어 있지 않다.
- 이 프로젝트가 외부 AI 공급자를 지원하는 만큼, "무엇을 밖으로 보내도 되는가"는 별도 문서와 코드 정책이 필요하다.

### 무엇을 추가할 것인가

- 외부 전송 가능 데이터 분류표
- 로컬 전용 처리 규칙
- 금지 페이로드 예시
- 운영자 승인 필요 조건

### 최소 포함 항목

- 도면 원본 이미지
- OCR 결과 원문
- 고객 식별 가능 정보
- API 키/토큰/세션 정보
- 내부 운영 메타데이터

### 기대 효과

- 모델 선택 문제가 곧 보안 경계 문제라는 점을 운영 레벨에서 분리할 수 있다.
- UI에서 외부 공급자를 지원하더라도, 실제 전송 정책은 더 엄격하게 관리할 수 있다.
- 나중에 공급자가 늘어나도 공통 경계를 유지하기 쉬워진다.

## 4. 다음 우선순위로 들어갈 것

## 4.1 Decision Log

### 왜 필요한가

- WeekdayCode는 반복적으로 "감이 아니라 실제 운영 결과를 보라"고 말한다.
- 현재는 `codex-cross-check` 흐름이 있어도, 그 결과가 누적 자산으로 남는 구조는 약하다.

### 무엇을 남길 것인가

- 어떤 작업에 Claude Code를 메인으로 썼는가
- 언제 Codex 교차검증을 호출했는가
- 어떤 대안을 버렸는가
- 최종 선택 이유가 비용, 속도, 품질 중 무엇이었는가
- 이후 결과가 어땠는가

### 구현 형태

- `docs/insights/reports/` 아래 정기 문서
- 또는 `.claude/commands/codex-cross-check.md`와 연동되는 템플릿성 로그

### 기대 효과

- 모델 선택이 취향이 아니라 운영 데이터가 된다.
- 나중에 같은 유형의 작업에서 더 빨리 의사결정할 수 있다.

## 4.2 Failure Pattern Repository

### 왜 필요한가

- 지금은 Reflector/Curator 패턴이 있어도, 실패가 세션 단위에서만 정리되고 끝날 가능성이 크다.
- 반복 실패 유형을 누적하면 프롬프트 수정보다 더 큰 개선이 생길 수 있다.

### 무엇을 쌓을 것인가

- 자주 틀리는 API 파라미터 매핑
- 잘못된 범위 확장 패턴
- 긴 세션 후 문맥 오염 패턴
- 공급자별 실패 모드
- 잘못된 툴 호출 순서

### 기대 효과

- 같은 실수를 매번 새롭게 겪지 않는다.
- 프롬프트 규칙 강화가 필요한 지점을 데이터로 찾을 수 있다.

## 4.3 Experiment Ledger

### 왜 필요한가

- WeekdayCode는 모델과 툴을 감으로 평가하지 말고 운영 체감으로 판단하라고 반복한다.
- 이 프로젝트도 Claude Code / Codex / 외부 모델 조합을 실제 수치와 함께 쌓아야 한다.

### 기록 항목 예시

- 작업 유형
- 사용 모델
- 총 소요 시간
- 수정 횟수
- 테스트 통과율
- 실패 원인
- 재시도 필요 여부

### 기대 효과

- `어떤 작업은 어떤 모델이 유리한가`를 경험칙이 아니라 기록으로 판단할 수 있다.
- 비용 최적화 논의를 실제 데이터 기반으로 바꿀 수 있다.

## 5. 지금은 하지 않는 것이 더 좋은 것

### 5.1 새 에이전트 수를 늘리는 일

- 상세판을 다시 읽어도 핵심은 멀티 에이전트 수 확대가 아니다.
- 지금 프로젝트는 이미 Claude Code 메인, Codex 보조 구조를 갖고 있다.
- 여기서 더 중요한 것은 `에이전트 숫자`보다 `컨텍스트 압축`, `검증`, `실패 정리`, `라우팅`이다.

### 5.2 새로운 프롬프트 기법을 계속 덧붙이는 일

- 프롬프트 계약층은 이미 상당 부분 들어갔다.
- 지금 더 필요한 것은 규칙 추가보다 `규칙이 실제로 지켜지는지`, `어디서 깨지는지`를 확인하는 것이다.

### 5.3 전면적인 스택 교체

- WeekdayCode의 메시지는 새 유행 스택으로 갈아타라는 것이 아니다.
- 오히려 지금 구조를 더 단순하고 안전하게 만드는 편이 맞다.

## 6. 권장 실행 순서

### 1단계

- `provider router / adapter` 설계 문서 작성
- 외부 전송 데이터 경계 정의
- 최소 회귀 테스트 범위 정의

### 2단계

- VL executor를 adapter 계층으로 분리
- provider routing 테스트 추가
- 외부 전송 정책 문서와 예외 처리 코드 추가

### 3단계

- Codex decision log 템플릿 도입
- Reflector/Curator 실패 패턴 누적 문서 도입
- 모델/워크플로우 실험 ledger 운영 시작

## 7. 추천 우선순위 요약

### 지금 바로 할 것

- `provider router / adapter`
- `agent regression tests`
- `external model egress policy`

### 바로 다음에 할 것

- `decision log`
- `failure pattern repository`
- `experiment ledger`

## 8. 한 줄 결론

- 상세판 기준으로 보면, 이 프로젝트의 다음 성장은 더 많은 AI 기능 추가가 아니라 `검증 가능한 운영 체계`, `공급자 독립 실행 구조`, `보안 경계`, `판단 기록`을 더 선명하게 만드는 쪽이다.
