# Epic: 초기창업패키지 성과발표회 PPT 완성

> **ID**: E01
> **상태**: Active
> **기간**: 2026-02-27 ~ 2026-03-06
> **고객**: 내부 (초기창업패키지 주관기관 제출용)

---

## 목적

초기창업패키지 성과발표회용 PPT를 완성하여 2026-03-06까지 제출한다.
python-pptx로 생성한 v6 기반, 14슬라이드 구성.

## 성공 기준 (Definition of Done)

- [ ] 14슬라이드 전체 내용 확정 (슬라이드 14 "기타 의견" 포함)
- [ ] 수치 검증 21/21 항목 통과 (PDF + 코드베이스 대조)
- [ ] 대표자 최종 검토 완료
- [ ] 제출 파일 생성 (pptx 형식)

## Story 목록

| ID | Story | 예상 | 상태 |
|----|-------|------|------|
| S01 | [내용 검증 + 수치 교차확인](S01-content-verification.md) | 2h | ✅ Done |
| S02 | [디자인 보완 + 최종 프리뷰](S02-design-polish.md) | 1h | ✅ Done |
| S03 | [대표자 검토 + 기타의견 + 제출](S03-ceo-review.md) | 30m | ⬜ Todo |

## 기술 결정

- python-pptx 자동 생성: 반복 수정 + 데이터 동기화 용이
- 메트릭 카드 패턴: RoundedRectangle + 큰 숫자 + 라벨 (v6에서 도입)
- PIL 프리뷰: LibreOffice 미설치 환경 대응

## 참조

- `docs/초기창업패키지/presentation/generate_pptx.py`
- `docs/초기창업패키지/presentation/슬라이드_원고_확정.md`
- `docs/초기창업패키지/presentation/발표자료_제작계획.md`
- `docs/초기창업패키지/(붙임1) 2025년 초기창업패키지 창업기업 최종보고서 ver2.0.pdf`
