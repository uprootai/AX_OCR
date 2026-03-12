# {{CUSTOMER_NAME}} — 고객 프로젝트

> **고객 ID**: {{CUSTOMER_ID}}
> **도면 유형**: {{DRAWING_TYPE}}
> **담당자**: {{CONTACT_NAME}} ({{CONTACT_EMAIL}})

---

## 개요

| 항목 | 내용 |
|------|------|
| 업종 | {{INDUSTRY}} |
| 도면 유형 | {{DRAWING_TYPE}} |
| 온보딩 시작일 | {{START_DATE}} |
| 현재 Phase | Phase 1 (도면 분석) |

## 디렉토리 구조

```
{{CUSTOMER_ID}}/
├── README.md          ← 이 파일
├── meetings/          ← 회의록
├── requirements/      ← 요구사항 문서
├── samples/           ← 샘플 도면 (분석 테스트용)
├── delivery/          ← 납품 패키지 (generate-package.sh 산출물)
└── training/          ← 교육 자료 (퀵카드, 매뉴얼 커스터마이징)
```

## Phase 진행 상태

| Phase | 기간 | 상태 | 주요 산출물 |
|-------|------|------|------------|
| 1. 도면 분석 | 1~2주 | ⬜ | 커버리지 리포트 |
| 2. 모델 적응 | 2~4주 | ⬜ | 전용 파서/모델 |
| 3. 검증 및 납품 | 1~2주 | ⬜ | 납품 패키지 |

## 메모

- (여기에 고객별 특이사항 기록)
