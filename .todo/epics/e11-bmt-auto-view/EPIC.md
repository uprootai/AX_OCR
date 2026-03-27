# E11: BMT 뷰 자동 분리 + BlueprintFlow executor 구현

> E10에서 수동 크롭(95.8%)으로 검증된 파이프라인을, 뷰 자동 분리 + executor 구현으로 완전 자동화

| 항목 | 값 |
|------|---|
| 시작 | 2026-03-26 |
| 의존성 | E10 완료 (S01~S06 Done) |
| 목표 | 이미지 업로드 → 자동 뷰 분리 → TAG 추출 → BOM 누락 리포트 (End-to-End) |
| 핵심 기술 | 뷰 라벨 OCR + OpenCV 경계선 감지 |

---

## 배경

E10에서 수동 좌표 크롭으로 95.8% TAG Recall을 달성했지만:
- 좌표가 하드코딩 → 다른 GVU 도면에서 동작 안 할 수 있음
- BlueprintFlow executor 미구현 → 빌더에서 실행 불가
- 고객이 "레이아웃이 매번 다르다"고 확인 (맵으로 잡으면 안 됨)

---

## Story 구조

| Story | 제목 | 의존성 | 설명 |
|-------|------|--------|------|
| S01 | 뷰 라벨 OCR 검출 | 없음 | "FRONT VIEW", "TOP VIEW" 등 라벨 텍스트 위치(bbox) 추출 |
| S02 | OpenCV 경계선 기반 섹션 범위 | S01 | 뷰 라벨 위치 + 빈 공간/경계선 감지 → 섹션 범위 추정 |
| S03 | 뷰 라벨 + 경계선 조합 자동 분리 | S01+S02 | 라벨 OCR → 경계선 감지 → 크롭 좌표 자동 생성 |
| S04 | OCR 앙상블 (PaddleOCR + Tesseract) | S03 | 뷰별 PaddleOCR + Tesseract 합산 → 100% 목표 |
| S05 | gateway-api executor 4개 구현 | S03 | view_splitter, tag_filter, excel_lookup, bom_check |
| S06 | End-to-End 데모 | S03~S05 | 빌더에서 이미지 업로드 → 누락 리포트 자동 생성 |

---

## 핵심 접근법: 뷰 라벨 OCR + 경계선 감지

```
1단계: PaddleOCR로 뷰 라벨 텍스트 위치 검출
  → "FRONT VIEW" bbox = (x=520, y=380, w=200, h=30)
  → "TOP VIEW" bbox = (x=1200, y=450, w=150, h=30)

2단계: 각 뷰 라벨 주변 OpenCV 경계선/빈 공간 감지
  → 라벨에서 가장 가까운 수평/수직 경계선 탐색
  → 경계선으로 둘러싸인 영역 = 해당 뷰의 섹션 범위

3단계: 크롭 좌표 자동 생성 → PaddleOCR 재실행
```

장점:
- 하드코딩 좌표 불필요
- 도면마다 레이아웃이 달라도 라벨만 찾으면 됨
- PaddleOCR이 이미 뷰 라벨을 검출하고 있음 (E10 S01에서 확인)
