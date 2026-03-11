# S08: 최종 검증 + 배포

> **상태**: ⬜ Todo
> **선행**: S02~S07 전체 완료
> **산출물**: 검증 리포트, 라이브 배포, 커밋

---

## 목표

모든 스타일 규칙 적용을 검증하고,
빌드 + 배포 + 시각 확인을 수행한다.

## Tasks

### T01 lint-style.sh 전체 실행

```bash
cd docs-site-starlight
bash scripts/lint-style.sh --report
```

**목표 출력**:
```
=== Docs Style Lint Report ===
Total files: 115
PASS: 115/115 (100%)
FAIL: 0/115 (0%)

Category breakdown:
| 카테고리 | 파일 | tags | H1 | bq | 순서 | API | 총점 |
|---------|-----|------|-----|-----|------|-----|------|
| system-overview | 6 | 100% | 100% | 100% | 100% | 100% | 100% |
| ... | ... | ... | ... | ... | ... | ... | ... |
```

### T02 Starlight 빌드

```bash
source ~/.nvm/nvm.sh && nvm use v22.22.1
cd docs-site-starlight && npx astro build
```

**목표**: 116페이지, 0 에러, <15초

### T03 배포 + Playwright 검증

```bash
# 배포
docker cp dist/. 851bbbb77fde_docs-site:/usr/share/nginx/html/
docker exec 851bbbb77fde_docs-site nginx -s reload
```

**5개 대표 페이지 스크린샷**:
1. `http://211.197.137.4:9000/docs/` — 메인 (사이드바 확인)
2. `http://211.197.137.4:9000/docs/system-overview/architecture-map/` — 다이어그램 렌더링
3. `http://211.197.137.4:9000/docs/frontend/route-map/` — 라우트 표 + 권한 컬럼
4. `http://211.197.137.4:9000/docs/analysis-pipeline/yolo-detection/` — API 섹션 확인
5. `http://211.197.137.4:9000/docs/frontend/pages/admin/` — anchor 기반 복합 문서

### T04 상태 업데이트 + 커밋

1. `.todo/ACTIVE.md` — E06 완료 상태 반영
2. `.todo/COMPLETED.md` — E06 아카이브
3. 커밋: `feat: E06 문서 스타일 규격 적용 — 115개 파일 100% 준수`

## 완료 조건

- [ ] lint-style.sh 0 violation
- [ ] 빌드 116페이지, 0 에러
- [ ] 5개 스크린샷에서 스타일 규격 시각 확인
- [ ] ACTIVE.md + COMPLETED.md 업데이트
- [ ] 커밋 완료
