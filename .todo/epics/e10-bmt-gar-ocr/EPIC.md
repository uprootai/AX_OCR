# E10: BMT GAR 배치도 TAG 추출 OCR 실험

> GAR 배치도(래스터 이미지)에서 TAG 라벨을 추출하고, Part List/ERP BOM과 자동 매칭하는 파이프라인 검증

| 항목 | 값 |
|------|---|
| 시작 | 2026-03-25 |
| 목표 | GAR 이미지 → TAG 추출 → BOM 누락 확인 파이프라인 POC |
| 입력 | `/home/uproot/ax/poc/apply-company/BMT/도면&BOM AI검증 솔루션 관련 자료/` |
| 핵심 이미지 | GAR 3페이지 (`/tmp/gar-page3.png`, 1684x2382px, 래스터) |
| 참조 문서 | `docs-site-starlight/.../bmt/call-analysis-detail.mdx` |
| BlueprintFlow | `:5173/blueprintflow/builder` — "BMT TAG 추출" 템플릿 생성 예정 |

---

## 배경

2026-03-25 통화에서 확인: 핵심 입력은 GAR 배치도 이미지(Page 3)이며, VD 상세도면이 아님.
Page 3은 **래스터 이미지**(텍스트 레이어 없음)이므로 pdfplumber 불가, OCR/비전 AI 필수.

---

## Story 구조

| Story | 제목 | 의존성 | 설명 |
|-------|------|--------|------|
| S01 | OCR 엔진별 벤치마크 (전체 이미지) | 없음 | 8개 OCR 엔진을 하나씩 실행, TAG 추출률 비교 |
| S02 | 뷰별 레이아웃 분리 실험 | S01 | Top/Front/Right/A View 영역 분리 → 개별 OCR |
| S03 | TAG vs 치수 필터링 | S01 | 알파벳 시작 = TAG, 숫자만 = 치수 규칙 + 엑셀 교차검증 |
| S04 | Part List/ERP BOM 자동 매칭 | S01+S03 | 추출된 TAG → Part List → BOM 누락 확인 자동화 |
| S05 | 멀티모달 VLM 실험 | S01 | Claude/GPT Vision으로 TAG 추출 비교 |
| S06 | BlueprintFlow 템플릿 생성 | S01~S04 | 검증된 파이프라인을 빌더 템플릿으로 등록 |

---

## 제약사항

- **메모리**: OCR 서비스를 동시에 올리지 않음. 하나씩 켰다가 끔
- **Docker**: 각 엔진 컨테이너 개별 기동 (`docker compose up <service> -d` → 테스트 → `docker compose stop <service>`)
- **검증 기준**: 실제 엑셀(Part List, ERP BOM)과 항상 교차 대조
- **TAG 규칙**: 알파벳 시작 = TAG (V, PT, TT, FT, B, PI, GSO, GSC, CV, ORI 등)
