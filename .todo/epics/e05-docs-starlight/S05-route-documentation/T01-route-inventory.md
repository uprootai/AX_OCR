# T01: web-ui 라우트 인벤토리 추출

> **Story**: S05-route-documentation
> **상태**: 🔄 진행 중 (WT2)

## 작업 내용

web-ui 소스에서 모든 라우트 선언 추출.

```bash
# 라우트 파일 위치 탐색
find web-ui/src -name "*route*" -o -name "*Route*" -o -name "App.tsx"

# path 선언 추출
grep -rn "path:" web-ui/src/ | sort
```

## 분류

| 분류 | 설명 |
|------|------|
| 공개 페이지 | 인증 없이 접근 |
| 사용자 페이지 | 일반 사용자 |
| 관리자 페이지 | admin 권한 |
| 시스템 라우트 | redirect, wildcard, wrapper |

## 산출물

- [ ] 총 라우트 수 확정
- [ ] 분류별 라우트 목록
