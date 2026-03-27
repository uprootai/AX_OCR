# E12: BMT 세션 UI — Human-in-the-Loop 도면 검증 시스템

> GAR 배치도 → 크롭별 TAG 검출 → 사람 확인/수정 → BOM 매칭 → 리포트
> 기존 BlueprintFlow AI BOM 세션 UI 위에 BMT 전용 워크플로우 구축

---

## 배경

E10(OCR 벤치마크) → E11(Min-Content E2E 파이프라인)에서 백엔드 파이프라인은 완성.
세션 UI에는 결과 테이블만 표시 중. **크롭별 Human-in-the-Loop 검증 UI가 없음.**

고객 데모를 위해 세션 내에서:
1. 도면 업로드 → 자동 뷰 분리
2. 각 크롭별 TAG OCR 결과 확인/수정
3. BOM 매칭 확인 → 불일치 판정
4. 리포트 생성

이 전체 흐름을 웹 UI에서 수행 가능해야 함.

---

## 현재 상태

| 항목 | 상태 |
|------|------|
| 백엔드 E2E 파이프라인 | ✅ 완성 (bmt_e2e_pipeline.py 150줄) |
| 백엔드 executor 4개 | ✅ 완성 (view_splitter, tag_filter, excel_lookup, bom_check) |
| 프론트엔드 BmtResultsSection | ✅ 결과 테이블 표시 (요약카드, 필터, 상세) |
| 크롭 시각화 이미지 | ✅ 정적 이미지 표시 (e11-mincontent-final.png 등) |
| OCR 벤치마크 차트 | ✅ 구현 |
| **크롭별 TAG 확인/수정 UI** | ❌ 미구현 |
| **Human-in-the-Loop 승인 흐름** | ❌ 미구현 |
| **파이프라인 실시간 실행** | ❌ 미구현 (CLI로만 실행) |

---

## 아키텍처 설계

### 프론트엔드 구조

```
WorkflowPage.tsx
  └── BmtWorkflowSection (NEW — 전체 BMT 흐름 관장)
        ├── Step 1: BmtCropViewer — 도면 + 9개 크롭 영역 오버레이
        │     └── 크롭 클릭 → 해당 크롭 확대 + TAG 오버레이
        ├── Step 2: BmtTagReview — 크롭별 TAG 검출 결과 확인/수정
        │     ├── 크롭 이미지 + TAG bbox 오버레이
        │     ├── TAG 목록 (승인/수정/삭제)
        │     ├── TAG 수동 추가
        │     └── 크롭 네비게이션 (이전/다음)
        ├── Step 3: BmtBomMatching — BOM 매칭 결과 + 불일치 판정
        │     ├── 매칭/불일치/미매핑 테이블
        │     ├── 불일치 항목 확인 (Part List vs ERP BOM 코드 나란히)
        │     └── 판정: 실제 오류 / 정상 차이 / 무시
        └── Step 4: BmtReport — Excel 리포트 생성 + 다운로드
```

### 백엔드 API 추가 필요

```
POST /bmt/{session_id}/run-pipeline        — 파이프라인 실행 (비동기)
GET  /bmt/{session_id}/crops               — 크롭 목록 + 이미지 URL
GET  /bmt/{session_id}/crops/{crop_id}/tags — 크롭별 TAG 검출 결과
PUT  /bmt/{session_id}/tags/{tag_id}       — TAG 수정 (Human Review)
POST /bmt/{session_id}/tags                — TAG 수동 추가
DELETE /bmt/{session_id}/tags/{tag_id}     — TAG 삭제
POST /bmt/{session_id}/bom-match           — BOM 매칭 실행
GET  /bmt/{session_id}/bom-match           — BOM 매칭 결과
PUT  /bmt/{session_id}/bom-match/{item_id} — 불일치 판정 (Human Review)
GET  /bmt/{session_id}/report              — Excel 리포트 다운로드
```

### 데이터 모델

```python
# 세션 metadata.bmt_results 확장
{
  "pipeline_status": "idle|running|completed|error",
  "crops": [
    {
      "id": "crop_0",
      "name": "FRONT VIEW",
      "bbox": [421, 0, 1081, 867],
      "image_url": "/bmt/{session_id}/crops/crop_0/image",
      "tags": [
        {
          "id": "tag_0",
          "tag": "V01",
          "bbox": [x, y, w, h],    # 크롭 내 좌표
          "confidence": 0.95,
          "engine": "paddle",
          "review_status": "pending|approved|modified|deleted",
          "modified_tag": null,     # 수정된 경우 새 값
          "reviewed_by": null,
          "reviewed_at": null
        }
      ]
    }
  ],
  "bom_match": {
    "status": "pending|completed",
    "items": [
      {
        "tag": "V01",
        "pl_code": "FB2F29-R64A-A111-36L-EXT-GVU-DNV",
        "erp_code": "FB2F29-R64A-A111-36L-EXT-GVU-DNV",
        "match_status": "match|mismatch|unmapped",
        "review_status": "pending|confirmed|false_positive",
        "review_notes": ""
      }
    ]
  }
}
```

---

## Stories

### S01: 크롭 이미지 생성 + API (백엔드)

**목표**: Min-Content 크롭 실행 → 크롭 이미지 저장 → API로 제공

**작업**:
- [ ] `POST /bmt/{session_id}/run-pipeline` — 파이프라인 실행, 크롭 이미지를 세션 uploads에 저장
- [ ] `GET /bmt/{session_id}/crops` — 크롭 목록 반환 (name, bbox, image_url, tag_count)
- [ ] `GET /bmt/{session_id}/crops/{crop_id}/image` — 크롭 이미지 serve
- [ ] 크롭별 TAG를 좌표(bbox)와 함께 저장

**산출물**: bmt_router.py (FastAPI router)
**예상 시간**: 3시간

### S02: 크롭 뷰어 (프론트엔드)

**목표**: 원본 도면에 9개 크롭 영역 오버레이 + 크롭 클릭 시 확대

**작업**:
- [ ] BmtCropViewer 컴포넌트 — 도면 이미지 위에 크롭 bbox를 색상별 사각형으로 표시
- [ ] 크롭 클릭 → 해당 크롭 이미지 확대 표시 + TAG 수 배지
- [ ] 크롭 목록 사이드바 (현재 선택 하이라이트)
- [ ] TAG가 있는 크롭만 필터

**산출물**: BmtCropViewer.tsx
**예상 시간**: 3시간

### S03: TAG 검출 결과 확인/수정 UI (프론트엔드)

**목표**: 크롭별 TAG를 이미지 위에 오버레이 + 승인/수정/삭제

**작업**:
- [ ] BmtTagReview 컴포넌트 — 크롭 이미지 + TAG bbox 오버레이
- [ ] TAG 목록 패널: 각 TAG에 승인(✅)/수정(✏️)/삭제(🗑️) 버튼
- [ ] TAG 수정 모달: TAG 이름 편집 (V14-1 → V14 수정 등)
- [ ] TAG 수동 추가: 크롭 이미지에서 영역 드래그 → TAG 이름 입력
- [ ] 크롭 네비게이션: 이전/다음 크롭으로 이동
- [ ] 진행률 표시: 승인/대기/수정 카운트
- [ ] `PUT /bmt/{session_id}/tags/{tag_id}` API 호출

**산출물**: BmtTagReview.tsx
**예상 시간**: 5시간
**참고**: 기존 SymbolVerificationSection 패턴 참조

### S04: BOM 매칭 + 불일치 판정 UI (프론트엔드)

**목표**: 승인된 TAG → Part List → ERP BOM 매칭 결과 + 불일치 판정

**작업**:
- [ ] BmtBomReview 컴포넌트 — 매칭/불일치/미매핑 테이블
- [ ] 불일치 항목: Part List 코드 vs ERP BOM 코드 나란히 표시 + diff 하이라이트
- [ ] 판정 버튼: "실제 오류" / "정상 차이" / "무시"
- [ ] 판정 메모 입력
- [ ] 요약 업데이트: 판정 완료 후 확정 카운트 갱신

**산출물**: BmtBomReview.tsx
**예상 시간**: 3시간
**참고**: 기존 BOMSection 패턴 참조

### S05: 파이프라인 실행 + 단계별 진행 UI

**목표**: 세션 UI에서 버튼 하나로 파이프라인 실행 + 단계별 진행 표시

**작업**:
- [ ] "파이프라인 실행" 버튼 → `POST /bmt/{session_id}/run-pipeline` 호출
- [ ] 6단계 진행 표시 (스텝 인디케이터)
- [ ] 각 단계 완료 시 UI 자동 갱신
- [ ] 에러 발생 시 해당 단계에서 중단 + 에러 메시지

**산출물**: BmtPipelineRunner.tsx
**예상 시간**: 2시간

### S06: 리포트 생성 + Excel 다운로드

**목표**: Human Review 완료 후 최종 리포트 생성

**작업**:
- [ ] "리포트 생성" 버튼 → 승인된 TAG + 판정된 BOM 결과로 Excel 생성
- [ ] Excel 다운로드 링크
- [ ] 리포트 미리보기 (Summary 시트 내용 표시)

**산출물**: BmtReport.tsx
**예상 시간**: 2시간

### S07: 통합 + 스텝 네비게이션

**목표**: S01~S06을 BmtWorkflowSection으로 통합, 스텝 네비게이션

**작업**:
- [ ] BmtWorkflowSection 컴포넌트 — 4단계 탭/스텝 UI
  - Step 1: 크롭 뷰 (BmtCropViewer)
  - Step 2: TAG 확인 (BmtTagReview)
  - Step 3: BOM 매칭 (BmtBomReview)
  - Step 4: 리포트 (BmtReport)
- [ ] 스텝 간 이동 (이전/다음)
- [ ] 각 스텝 완료 조건: Step 2는 모든 TAG 승인 시, Step 3은 모든 불일치 판정 시
- [ ] WorkflowPage.tsx에서 기존 BmtResultsSection 대체

**산출물**: BmtWorkflowSection.tsx
**예상 시간**: 3시간

---

## 의존관계

```
S01 (백엔드 API) → S02 (크롭 뷰어)
S01 → S03 (TAG 확인) → S04 (BOM 매칭) → S06 (리포트)
S05 (파이프라인 실행)는 독립
S07 (통합)은 S02~S06 전부 완료 후
```

## 예상 총 소요

| Story | 시간 |
|-------|------|
| S01 백엔드 API | 3h |
| S02 크롭 뷰어 | 3h |
| S03 TAG 확인/수정 | 5h |
| S04 BOM 매칭 판정 | 3h |
| S05 파이프라인 실행 | 2h |
| S06 리포트 | 2h |
| S07 통합 | 3h |
| **합계** | **~21h** |

## 우선순위

**MVP (고객 데모 최소 요건)**: S01 + S02 + S03 + S04 = ~14h
**Full**: S01~S07 = ~21h

---

## 참고

- 기존 패턴: `SymbolVerificationSection` (심볼 승인/거부)
- 기존 패턴: `DetectionResultsSection` (캔버스 오버레이)
- 기존 패턴: `BOMSection` (BOM 테이블 + 하이라이트)
- BMT docs-site: `docs-site-starlight/src/content/docs/customer-cases/bmt/`
- E2E 파이프라인: `apply-company/BMT/samples/bmt_e2e_pipeline.py`
- 세션 ID: `2e6bae64-75e9-4101-b3a0-edbc11922aa8`
- 프로젝트 ID: `c01db741`
