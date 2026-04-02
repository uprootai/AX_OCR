# Codex Review Result — 2026-04-02

검토 대상: [gt-validation.mdx](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx)

## Findings

1. High — `전체 도면 직선 투사 결과`의 T8 수치가 현재 실행 가능한 소스와 맞지 않고, 페이지 내부에서도 돌출부 정의가 두 개로 섞여 있습니다.
[gt-validation.mdx#L261](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L261)
[gt-validation.mdx#L286](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L286)
[gt-validation.mdx#L204](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L204)
[s08_cardinal_v3_fullpage.py#L138](/home/uproot/ax/poc/blueprint-ai-bom/scripts/s08_cardinal_v3_fullpage.py#L138)
[s08_cardinal_v3_fullpage.py#L210](/home/uproot/ax/poc/blueprint-ai-bom/scripts/s08_cardinal_v3_fullpage.py#L210)
[generate_protrusion_detect.py](/home/uproot/ax/poc/blueprint-ai-bom/scripts/generate_protrusion_detect.py)
2026-04-02에 `s08_cardinal_v3_fullpage.py`를 임시 출력 경로로 실행했을 때 T8은 `동심원 10개 / 돌출 끝점 8개 / 직선 56 / 히트 직선 1 / 동심원 히트 1 / 돌출부 히트 0`이었습니다. 문서는 `11개 / 8개 / 60 / 2 / 2 / 0`으로 적고 있습니다. 또 같은 페이지의 돌출부 섹션은 `동서남북 4방향 최대치`만 사용한다고 설명하고 표도 4개 값만 제시하지만, fullpage/S01 스크립트는 여전히 360도 `radial_edge_scan` 클러스터링으로 7~8개 peak를 사용합니다. 임시 재생성 이미지 hash는 T1/T2/T4는 게시본과 같았고 T8 fullpage만 달랐습니다.

2. Medium — Step 3B 이미지 헤더가 본문 설명과 다른 파라미터를 노출합니다.
[gt-validation.mdx#L130](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L130)
[gt-validation.mdx#L156](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L156)
[gt-validation.mdx#L140](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L140)
[generate_concentric_steps.py#L334](/home/uproot/ax/poc/blueprint-ai-bom/scripts/generate_concentric_steps.py#L334)
[generate_concentric_steps.py#L348](/home/uproot/ax/poc/blueprint-ai-bom/scripts/generate_concentric_steps.py#L348)
본문과 A/B 비교 표는 방안 B를 `HOUGH_GRADIENT_ALT`, `dp=1.5`, `param2=0.85`로 설명합니다. 그런데 현재 게시 중인 [step3b_hough_tuned.jpg](/home/uproot/ax/poc/docs-site-starlight/public/images/gt-validation/steps/step3b_hough_tuned.jpg)는 실제로 `dp=1.2, param2=120, minDist=171px` 헤더를 보여주며, 생성 스크립트도 그 문구를 그대로 그립니다. 이미지 자체는 현재 스크립트와 byte-level로 일치하므로, “이미지가 낡았다”가 아니라 “최신 이미지 안의 설명이 틀렸다”가 맞습니다.

3. Medium — GT-1/GT-2 케이스 섹션 제목의 베어링 타입이 앞쪽 GT 표와 뒤바뀌어 있습니다.
[gt-validation.mdx#L24](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L24)
[gt-validation.mdx#L26](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L26)
[gt-validation.mdx#L421](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L421)
[gt-validation.mdx#L459](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L459)
GT 표에서는 `TD0062037 = T5 BEARING ASSY`, `TD0062055 = THRUST BEARING ASSY`입니다. 그런데 아래 케이스 섹션은 `GT-1: TD0062037 — Thrust Bearing`, `GT-2: TD0062055 — Radial Bearing`으로 표기합니다. 수치 본문은 맞지만 제목 분류가 반대로 달려 있어 독자가 사례 의미를 잘못 이해하게 만듭니다.

4. Low — 헤딩 단계는 깨지지 않았지만, 문서 범위와 알려진 문제 서술은 아직 섞여 있습니다.
[gt-validation.mdx#L3](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L3)
[gt-validation.mdx#L171](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L171)
[gt-validation.mdx#L293](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L293)
[gt-validation.mdx#L320](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L320)
H2/H3/H4 순서는 정상이고 skipped heading은 없었습니다. 다만 frontmatter 설명은 아직 `2개 ASSY GT 도면의 v2→v5`라고 적혀 있어 현재 본문 범위인 `7개 GT / v7 / Cardinal v3`와 맞지 않습니다. 또한 `시각화 범례` H4가 두 번 반복되고, 핸드오프에 있던 `72/123 필터 과다 통과`, `fullpage 이미지와 새 돌출부 기준 미동기화`는 본문에 “문제”로 명시돼 있지 않습니다.

## Verification Summary

- 수치 정합성
- [gt-validation.mdx#L28](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx#L28)의 `v7 최종 결과`는 [e12-section-detection.mdx#L329](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/e12-section-detection.mdx#L329)의 `v7 결과`와 일치했습니다. 합계 `7/7, 7/7, 5/7 = 19/21 (90%)`도 내부 합산상 맞습니다.
- `generate_concentric_steps.py` 실행 결과는 문서의 T1 파이프라인 수치와 일치했습니다: A안 `53 -> 48 -> 41`, B안 `3 -> 5 -> 2`, 베어링 `4원(r=102~285)`.
- `generate_concentric_alt_all.py` 실행 결과는 `GRADIENT_ALT 전체 도면 검증` 표와 일치했습니다.
- `generate_protrusion_detect.py` 실행 결과는 돌출부 표와 일치했습니다: T1 `318/274/316/317`, T2 `310/293/308/309`, T4 `326/285/340/337`, T8 `315/293/311/310`.
- `s08_cardinal_v3_fullpage.py`는 T1/T2/T4는 문서와 맞았지만 T8은 불일치했습니다.
- `s01_cardinal_integration.py`는 문서 수치와 일치했습니다: T1 `248 -> 123 -> 72`, T2 `259 -> 129 -> 83`.

- 이미지/텍스트 일관성
- MDX가 참조하는 이미지 41개는 모두 존재했습니다. `/images/gt-validation/...` 37개, `/img/ensemble/...` 4개 모두 missing 0건이었습니다.
- `generate_concentric_steps.py`, `generate_concentric_alt_all.py`, `generate_protrusion_detect.py` 임시 재생성 결과는 게시 이미지와 모두 hash 일치했습니다.
- `s08_cardinal_v3_fullpage.py`는 `t8_cardinal_v3_full.jpg`만 게시본과 hash 불일치였습니다.

- 섹션 구조
- H2/H3/H4 계층 자체는 유효했습니다.
- 다만 페이지 상반부는 `7 GT + v7 + Cardinal v3`, 하반부는 기존 `2 GT 상세 사례`가 남아 있어 범위 설명이 분리되지 않은 상태입니다.

- 알려진 문제 문서화 상태
- 문서화됨: `T4/T8 고해상도에서 화살촉 4개만 검출`, `ASSY 도면의 OD/ID는 세션명에만 존재`.
- 미흡함: `72/123 투사선 필터 과다 통과 및 사선 포함`, `fullpage 투사 이미지가 새 4방향 돌출부 기준과 sync되지 않음`.

- 스크립트 실행 검증
- 2026-04-02 기준 `python AST parse`는 5개 스크립트 모두 통과했습니다.
- OCR health는 `http://localhost:5006/health`에서 HTTP 200이었습니다.
- 사용자 요청 3개 스크립트는 모두 정상 실행됐습니다.
- 검토 패킷에 함께 적힌 `s08_cardinal_v3_fullpage.py`, `s01_cardinal_integration.py`도 추가로 실행해 수치 대조에 사용했습니다.

## Recommended Next Actions

1. [s08_cardinal_v3_fullpage.py](/home/uproot/ax/poc/blueprint-ai-bom/scripts/s08_cardinal_v3_fullpage.py)의 돌출부 검출을 [generate_protrusion_detect.py](/home/uproot/ax/poc/blueprint-ai-bom/scripts/generate_protrusion_detect.py)의 `cardinal_max_scan`(4방향 최대치)으로 교체하고, `T8` fullpage 이미지를 재생성한 뒤 [gt-validation.mdx](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx)의 관련 수치를 갱신합니다.
2. [generate_concentric_steps.py](/home/uproot/ax/poc/blueprint-ai-bom/scripts/generate_concentric_steps.py)의 Step 3B 헤더를 `HOUGH_GRADIENT_ALT`, `dp=1.5`, `param2=0.85` 기준으로 수정한 뒤 이미지를 재생성합니다.
3. [gt-validation.mdx](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx)의 GT-1/GT-2 케이스 제목을 `GT-1 TD0062037 = T5 BEARING ASSY`, `GT-2 TD0062055 = THRUST BEARING ASSY`로 바로잡고, frontmatter `description`도 현재 범위(`7개 GT`, `v7`, `Cardinal v3`)에 맞게 업데이트합니다.
4. [gt-validation.mdx](/home/uproot/ax/poc/docs-site-starlight/src/content/docs/customer-cases/dsebearing/ensemble/gt-validation.mdx) `L320` 근처에 `투사선 필터 72/123 과다 통과 + 사선 포함` known issue를 명시합니다.
