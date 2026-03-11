# T02: 마이그레이션 자동화 스크립트 작성

> **Story**: S03-content-migration
> **상태**: ⬜ Todo (S02 Go 후)

## 스크립트 기능

`scripts/migrate-to-starlight.sh`:

### Step 1: 파일 복사
```bash
cp -r docs-site/docs/* docs-site-starlight/src/content/docs/
cp -r docs-site/static/img/* docs-site-starlight/public/img/
```

### Step 2: frontmatter 변환
- `sidebar_position` → 제거 또는 `sidebar.order`로 변환

### Step 3: FlowDiagram/SequenceDiagram import 삽입
- 파일에 `<FlowDiagram` 이 있으면 frontmatter 뒤에 import 추가
- `<FlowDiagram` → `<FlowDiagram client:load`

### Step 4: admonition 변환
- `:::warning` → `:::caution`

### Step 5: 이미지 경로 변환
- `/docs/img/` → `/img/`

### Step 6: 내부 링크 검증
- 모든 `](/docs/...` 링크의 대상 파일 존재 확인
- 깨진 링크 리스트 출력

## 검증

- [ ] 스크립트 dry-run 모드 (변경 없이 리포트만)
- [ ] 스크립트 실행 후 빌드 성공
- [ ] 변환 전/후 diff 리뷰
