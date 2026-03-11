# E04: AX 테스트 컴플렉스 온보딩

> **고객**: 부산 제조 중소기업 10개사 (기존 3 + 신규 7)
> **기간**: 2025.09 ~ 2028.12 (4년)
> **규모**: 총 249억원
> **범위**: 솔루션 공급 + 커스터마이징 + 교육 + 운영 지원

---

## 배경

초기창업패키지에서 실증한 파나시아·동서기연·테크로스 3개사를 포함하여,
AX 실증 산단 구축 사업을 통해 총 10개 제조 중소기업에 도면 자동 분석 AI를 공급한다.

기존 3개사는 이미 진행 중이며, 나머지 7개사는 모집·확정 후 순차 온보딩한다.
신규 기업의 도면 유형(P&ID / 기계 도면 / 기타)은 확정 전까지 알 수 없으므로,
**어떤 업종이 와도 대응할 수 있는 범용 온보딩 체계**를 먼저 구축한다.

## 기존 자산 (재활용)

| 자산 | 경로 | 상태 |
|------|------|------|
| 납품 패키지 (동서기연) | `blueprint-ai-bom/exports/dsebearing-delivery/` | ✅ 완성 |
| 온보딩 가이드 (8단계) | `docs-site/docs/batch-delivery/onboarding-guide.mdx` | ✅ 완성 |
| CLI 온보딩 스크립트 | `scripts/onboard.py` (3종 프리셋) | ✅ 완성 |
| 설치 가이드 (527줄) | `docs-site/docs/deployment/installation.md` | ✅ 완성 |
| 운영/관리자 매뉴얼 | `docs-site/docs/deployment/` | ✅ 완성 |
| 21개 API OpenAPI 스펙 | `gateway-api/api_specs/` | ✅ 완성 |
| YOLO 학습 파이프라인 | `models/yolo-api/training/` | ✅ 완성 |
| 동서기연 전용 파서/라우터 | `gateway-api/services/dsebearing_*` | ✅ 선례 |
| BMAD-Lite 템플릿 | `.todo/templates/` | ✅ 완성 |

## Stories

| ID | Story | 핵심 목표 | 상태 |
|----|-------|-----------|------|
| S01 | [범용 납품 패키지 템플릿화](S01-delivery-template.md) | 고객명만 바꾸면 되는 범용 구조 | ⬜ Todo |
| S02 | [커스터마이징 파이프라인 표준화](S02-customization-pipeline.md) | 신규 업종 대응 절차 정립 | ⬜ Todo |
| S03 | [사용자 교육 체계 구축](S03-training-system.md) | 엔지니어용 교육 자료 + 영상 | ⬜ Todo |
| S04 | [기존 3개사 통합 관리](S04-existing-migration.md) | 파나시아/동서기연/테크로스 일원화 | ⬜ Todo |
| S05 | [신규 기업 순차 온보딩](S05-new-onboarding.md) | 7개사 확정 시 적용 | ⬜ Blocked (모집 중) |

## 의존 관계

```
S01 (템플릿화) ──┐
S02 (커스터마이징) ├──→ S04 (기존 3개사) ──→ S05 (신규 7개사)
S03 (교육 체계)  ──┘
```

S01~S03는 병렬 진행 가능. S04는 S01~S03 완료 후. S05는 기업 확정 시.
