# S07: 표 형식 + Anchor 통일

> **상태**: ⬜ Todo
> **선행**: S01 (표 형식 정의), S04 (섹션 순서 확정)
> **산출물**: ~17개 파일 표 수정 + ~10개 파일 anchor 추가

---

## 목표

문서 내 표의 컬럼 헤더를 4종 표준 형식으로 통일하고,
복합 페이지에 명시적 anchor를 추가한다.

## Tasks

### T01 표 형식 표준 + 비준수 목록

**4종 표준**:

| 코드 | 용도 | 컬럼 |
|------|------|------|
| Type A | 접속 정보 | `URL \| 권한 \| 설명` |
| Type B | 라우트 맵 | `경로 \| 페이지 \| 설명 \| 가이드` |
| Type C | 탭 구성 | `탭 \| 설명 \| 주요 동작` |
| Type D | 기능 목록 | `기능 \| 설명` |
| Type E | API 정보 | `메서드 \| 엔드포인트 \| 설명` |
| Type F | 파라미터 | `파라미터 \| 타입 \| 기본값 \| 설명` |
| Type G | 기본 정보 | `항목 \| 값` |

비준수 파일 추출:
```bash
# 표 헤더가 표준 형식이 아닌 파일
grep -n "^|.*|.*|" src/content/docs/**/*.{md,mdx} |
  grep -v "URL.*권한\|경로.*페이지\|탭.*설명.*동작\|기능.*설명\|메서드.*엔드\|파라미터.*타입\|항목.*값"
```

### T02 비준수 표 수정 (~17개 파일)

수정 원칙:
- 컬럼 헤더만 표준으로 변경, 데이터는 유지
- 불필요한 컬럼 추가/삭제 없음
- 의미가 동일한 헤더는 표준 명칭으로 통일
  - `포트` → `항목: 값` 표의 행으로
  - `이름`, `명칭` → `기능` 또는 `항목`
  - `상태`, `비고` → `설명`에 통합 가능하면 통합

### T03 복합 페이지 anchor 추가 (~10개 파일)

**대상**: H2 섹션이 4개 이상인 문서 중, 다른 문서에서 특정 섹션을 직접 링크해야 하는 경우

**형식**:
```markdown
<a id="section-name"></a>

## 섹션 제목
```

**대상 파일 + anchor 예시**:

| 파일 | anchor | 참조처 |
|------|--------|-------|
| admin.mdx | `api-detail`, `backup-restore` | route-map.mdx |
| dashboard.mdx | `recent-projects`, `system-status` | route-map.mdx |
| project.mdx | `project-list`, `project-detail` | route-map.mdx |
| system-overview/index.mdx | `service-topology`, `communication` | architecture-map.mdx |
| frontend/index.mdx | `web-ui`, `bom-ui` | route-map.mdx |

**검증**: 모든 anchor가 실제 참조처에서 사용되는지 확인

## 완료 조건

- [ ] 비준수 표 0개
- [ ] 복합 페이지 anchor가 참조처와 연결됨
- [ ] 빌드 성공 (잘못된 HTML 태그 없음)
