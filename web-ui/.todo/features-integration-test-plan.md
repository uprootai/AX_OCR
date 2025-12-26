# Features 연동 테스트 계획

> 생성일: 2025-12-26
> 완료일: 2025-12-26
> 목적: 빌더 features → 워크플로우 페이지 연동 검증

---

## 테스트 결과 요약

| TC | 설명 | Features 수 | 결과 | 비고 |
|----|------|------------|------|------|
| TC1 | 기본 검출 Only | 1 | **PASS** | 심볼 검출 배지만 표시 |
| TC2 | GD&T 조합 | 4 | **PASS** | GD&T 기하공차 섹션 표시 |
| TC3 | P&ID 전용 | 3 | **PASS** | 선 검출, P&ID 연결성 섹션 표시 |
| TC4 | BOM 풀셋 | 5 | **PASS** | 표제란 OCR 섹션 표시 |
| TC5 | 장기 로드맵 | 4 | **PASS** | 배지 매핑 수정 완료 |
| TC6 | 빈 Features | 0 | **PASS** | 기본 VLM 분류 섹션만 표시 |
| TC7 | 전체 Features | 18 | **PASS** | 12+ 배지 표시, 모든 섹션 |

**총 결과: 7 PASS / 0 PARTIAL - 모든 테스트 통과!**

---

## 테스트 케이스 상세

### TC1: 기본 검출 Only
- **Session ID**: `3ee4c152-80e6-4530-b311-499d3cf801f5`
- **Features**: `symbol_detection`
- **결과**: PASS
- **확인 사항**: 심볼 검출 배지 1개만 표시

### TC2: GD&T / 기계 도면 조합
- **Session ID**: `8d982314-384c-4faa-ae36-2d5c0ef57264`
- **Features**: `symbol_detection`, `dimension_ocr`, `gdt_parsing`, `relation_extraction`
- **결과**: PASS
- **확인 사항**: 4개 배지 + GD&T 기하공차 섹션 표시

### TC3: P&ID 전용
- **Session ID**: `25201bfe-e548-43c3-8005-dd64f5c6f12b`
- **Features**: `symbol_detection`, `line_detection`, `pid_connectivity`
- **결과**: PASS
- **확인 사항**: 3개 배지 + 선 검출 섹션 표시

### TC4: BOM 생성 풀셋
- **Session ID**: `fdc57ef5-bf1c-486f-b1fb-7febe4fdcc57`
- **Features**: `symbol_detection`, `title_block_ocr`, `quantity_extraction`, `balloon_matching`, `bom_generation`
- **결과**: PASS
- **확인 사항**: 5개 배지 + 표제란 OCR 섹션 표시

### TC5: 장기 로드맵 기능
- **Session ID**: `3dd9d15e-609e-46d9-b03c-7cb856e831fe` (재생성)
- **Features**: `drawing_region_segmentation`, `notes_extraction`, `revision_comparison`, `vlm_auto_classification`
- **결과**: PASS (수정 후)
- **확인 사항**: 4개 배지 정상 표시 (영역 세분화, 노트 추출, 리비전 비교, VLM 자동 분류)
- **수정 내용**: `ActiveFeaturesSection.tsx`에 장기 로드맵 FEATURE_CONFIG 추가

### TC6: 빈 Features (Edge Case)
- **Session ID**: `a3d1e31a-e6a8-4da1-92e7-22147c0f5ab5`
- **Features**: (없음)
- **결과**: PASS
- **확인 사항**: 활성화된 기능 배지 없음, VLM 도면 분류 기본 섹션만 표시

### TC7: 전체 Features
- **Session ID**: `96d47baa-f87d-43c1-b2a9-35ad2fb0da50`
- **Features**: 18개 전체
- **결과**: PASS
- **확인 사항**: 12+ 배지 3줄 표시, 모든 기능 섹션 활성화

---

## 검증 체크리스트

- [x] 세션 생성 시 features 저장 확인
- [x] 워크플로우 페이지에서 features 배지 표시
- [x] 선택된 features에 해당하는 섹션만 표시
- [x] 선택되지 않은 features 섹션 숨김 확인
- [x] 장기 로드맵 features 배지 매핑 완료

---

## 스크린샷 참조

- `TC1-symbol-only-*.png`
- `TC2-gdt-features-*.png`
- `TC3-pid-features-*.png`
- `TC4-bom-features-*.png`
- `TC5-roadmap-features-*.png`
- `TC6-empty-features-*.png`
- `TC7-all-features-*.png`
