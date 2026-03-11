# S03: H1 제목 + Blockquote 표준화

> **상태**: ⬜ Todo
> **선행**: S01 (제목 패턴 정의)
> **산출물**: 115개 파일 H1 + blockquote 수정

---

## 목표

모든 문서의 H1 제목을 `한글 (English)` 패턴으로 통일하고,
blockquote 요약이 누락된 파일을 보완한다.

## Tasks

### T01 H1 제목 매핑표 작성

현재 → 목표 변환 목록 (전체 115개):

**system-overview (6)**
| 현재 | 목표 |
|------|------|
| `# 시스템 개요` | `# 시스템 개요 (System Overview)` |
| `# 아키텍처 맵` | `# 아키텍처 맵 (Architecture Map)` |
| `# 서비스 카탈로그` | `# 서비스 카탈로그 (Service Catalog)` |
| `# 기술 스택` | `# 기술 스택 (Tech Stack)` |
| `# 포트 및 네트워크` | `# 포트 및 네트워크 (Port & Network)` |
| `# 아키텍처 결정 기록` | `# 아키텍처 결정 기록 (Architecture Decisions)` |

**api-reference (19)** — 영어 제목에 한글 보충:
| 현재 | 목표 |
|------|------|
| `# YOLO Detection API` | `# YOLO 검출 API (YOLO Detection)` |
| `# eDOCr2 OCR API` | `# eDOCr2 OCR API` (이미 혼합) |
| `# Blueprint AI BOM API` | `# Blueprint AI BOM API (BOM 자동 생성)` |
| ... | 나머지 16개도 동일 패턴 |

**나머지 카테고리** — T01에서 전체 매핑표 확정

### T02 일괄 변환

자동화 가능 범위:
- 순수 한글 제목 → `(영어)` 추가: 스크립트 (매핑표 기반)
- 순수 영어 제목 → `한글 (영어)` 변환: 스크립트 (매핑표 기반)
- 혼합 제목 → 수동 확인

```bash
node scripts/fix-titles.mjs --dry-run
node scripts/fix-titles.mjs
```

### T03 blockquote 보완

누락 파일 (~6개) 식별 후 수동 추가:
- H1 바로 다음 줄에 `>` 시작
- 1문장, 한국어, 문서가 다루는 범위 요약
- "좋습니다", "강력합니다" 등 홍보 문구 금지

## 완료 조건

- [ ] 115/115 파일 H1이 `한글 (English)` 또는 `English (한글)` 패턴
- [ ] 115/115 파일 blockquote 존재
- [ ] lint-style.sh H1 + blockquote 검사 PASS
