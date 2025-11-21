---
name: code-janitor
description: Automatically detects and fixes code quality issues including unused imports, type hints, security vulnerabilities, and performance problems across Python and TypeScript codebases
allowed-tools: [grep, glob, read, bash]
---

# Code Janitor Skill

**목적**: 잔 오류, 코드 스멜, 베스트 프랙티스 위반을 자동으로 탐지하고 수정

## 🔍 탐지 항목

### 1. Python 백엔드 오류

#### A. 타입 힌트 누락
```python
# Before
def process_image(image_bytes, filename):
    return result

# After
def process_image(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    return result
```

**검사 방법**:
```bash
mypy gateway-api/api_server.py --ignore-missing-imports
```

#### B. 미사용 import
```python
# Before
import os
import sys  # 사용 안함
import json
from typing import List, Dict, Optional, Tuple  # Tuple 사용 안함

# After
import os
import json
from typing import List, Dict, Optional
```

**검사 도구**: `autoflake --remove-all-unused-imports --in-place *.py`

#### C. 긴 함수 (100줄 이상)
- `gateway-api/api_server.py:process_drawing()` → 리팩토링 제안
- 함수를 작은 단위로 분리

#### D. 하드코딩된 값
```python
# Before
if len(detections) > 50:  # Magic number
    logger.warning("Too many detections")

# After
MAX_DETECTIONS = 50  # 상수로 정의
if len(detections) > MAX_DETECTIONS:
    logger.warning(f"Too many detections: {len(detections)} > {MAX_DETECTIONS}")
```

#### E. 에러 핸들링 부족
```python
# Before
result = api_call()

# After
try:
    result = api_call()
except RequestException as e:
    logger.error(f"API call failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 2. TypeScript/React 프론트엔드 오류

#### A. Console.log 남아있음
```typescript
// Before
console.log("Debug:", result);  // 개발 중 디버깅용

// After
// 프로덕션 빌드에서 제거
```

**검사**: `grep -r "console.log" web-ui/src/`

#### B. any 타입 남용
```typescript
// Before
const result: any = await fetchData();

// After
interface FetchResult {
  status: string;
  data: AnalysisResult;
}
const result: FetchResult = await fetchData();
```

**검사**: ESLint rule `@typescript-eslint/no-explicit-any`

#### C. useEffect 의존성 배열 누락
```typescript
// Before
useEffect(() => {
  fetchData(id);
}, []); // id 의존성 누락!

// After
useEffect(() => {
  fetchData(id);
}, [id]);
```

#### D. Key prop 누락 (React 리스트)
```tsx
// Before
{items.map(item => <div>{item.name}</div>)}

// After
{items.map(item => <div key={item.id}>{item.name}</div>)}
```

### 3. Docker/인프라 오류

#### A. 미사용 이미지/컨테이너
```bash
# 주 1회 정리
docker system prune -a --volumes -f
```

#### B. 로그 크기 제한 없음
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

#### C. Health check 누락
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1
```

### 4. 보안 취약점

#### A. 하드코딩된 시크릿
```python
# Before
API_KEY = "sk-1234567890abcdef"  # 절대 금지!

# After
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

**검사**: `grep -r "sk-\|api_key.*=" . --exclude-dir=node_modules`

#### B. SQL Injection 위험
```python
# Before
query = f"SELECT * FROM users WHERE id = {user_id}"

# After
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

#### C. CORS 설정 너무 관대
```python
# Before
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# After
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS)
```

### 5. 성능 이슈

#### A. 동기 I/O in async 함수
```python
# Before
async def process():
    with open("file.txt") as f:  # 블로킹!
        data = f.read()

# After
async def process():
    async with aiofiles.open("file.txt") as f:
        data = await f.read()
```

#### B. 불필요한 재계산
```python
# Before
for item in items:
    if len(items) > 10:  # 매번 계산!
        process(item)

# After
items_count = len(items)
for item in items:
    if items_count > 10:
        process(item)
```

#### C. 메모리 누수 (대용량 파일)
```python
# Before
image_bytes = await file.read()  # 전체 메모리에 로드

# After
# 스트리밍 처리 또는 청크 단위 읽기
```

## 🛠️ 자동 수정 도구

### Python
```bash
# 1. Import 정리
autoflake --remove-all-unused-imports --in-place gateway-api/*.py

# 2. 포맷팅
black gateway-api/ --line-length 120

# 3. Import 정렬
isort gateway-api/

# 4. Linting
pylint gateway-api/api_server.py --disable=C0111,R0913

# 5. 타입 체크
mypy gateway-api/ --ignore-missing-imports
```

### TypeScript/React
```bash
# 1. ESLint 자동 수정
cd web-ui
npm run lint -- --fix

# 2. Prettier 포맷팅
npm run format

# 3. 미사용 import 제거
npx ts-prune

# 4. 타입 체크
npm run type-check
```

## 📋 실행 워크플로우

### 단계 1: 스캔
```bash
# Python
cd /home/uproot/ax/poc
find gateway-api yolo-api edocr2-v2-api -name "*.py" -exec pylint {} \; > /tmp/lint_report.txt

# TypeScript
cd web-ui
npm run lint -- --format json > /tmp/eslint_report.json
```

### 단계 2: 분류
오류를 심각도별로 분류:
- 🔴 **Critical**: 보안 취약점, 크래시 유발
- 🟡 **Warning**: 성능 이슈, 베스트 프랙티스 위반
- 🔵 **Info**: 코드 스타일, 가독성

### 단계 3: 자동 수정
```python
# 안전한 수정만 자동 적용
SAFE_FIXES = [
    "unused-imports",
    "trailing-whitespace",
    "missing-docstring",  # 템플릿 추가
    "line-too-long"
]

# 위험한 수정은 사용자 확인 필요
MANUAL_REVIEW = [
    "unused-variable",  # 실제로 필요한 변수일 수 있음
    "bare-except",  # 에러 핸들링 로직 변경
    "sql-injection"  # 비즈니스 로직 영향
]
```

### 단계 4: 보고서 생성
`/tmp/test_results/CODE_QUALITY_YYYY-MM-DD.md`:

```markdown
# 코드 품질 보고서 - 2025-11-16

## 요약
- 전체 파일: 45개
- 스캔한 파일: 45개
- 발견된 이슈: 127개
- 자동 수정: 89개
- 수동 검토 필요: 38개

## Critical 🔴 (3개)
1. **gateway-api/api_server.py:156** - Hardcoded API key
2. **yolo-api/api_server.py:89** - SQL injection risk
3. **web-ui/.env** - Exposed secret in git

## Warning 🟡 (38개)
1. **gateway-api/api_server.py:1273** - Function too long (250 lines)
2. **web-ui/src/pages/TestGateway.tsx:488** - Missing key prop
...

## Info 🔵 (86개)
- 45개: Unused imports (자동 수정 완료)
- 21개: Missing type hints (자동 수정 완료)
- 20개: Trailing whitespace (자동 수정 완료)

## 성능 개선 제안
- gateway-api: 동기 I/O 3곳 발견 → async로 변환 시 20% 성능 향상 예상
- web-ui: 불필요한 리렌더링 12곳 → React.memo 적용 권장

## 다음 단계
- [ ] Critical 이슈 3개 즉시 수정
- [ ] Warning 중 성능 관련 8개 우선 처리
- [ ] gateway-api 리팩토링 계획 수립
```

### 단계 5: Git Commit
```bash
git add .
git commit -m "chore: Auto-fix code quality issues

- Remove 45 unused imports
- Add 21 missing type hints
- Fix 20 trailing whitespaces
- Apply black formatting

Generated by: code-janitor skill"
```

## 🎯 사용 방법

### 일일 스캔 (권장)
```bash
# 매일 아침 자동 실행
crontab -e
0 9 * * * cd /home/uproot/ax/poc && claude skill code-janitor --auto-fix
```

### 수동 실행
```bash
# Claude Code에서
/skill code-janitor

# 또는 특정 서비스만
/skill code-janitor --service gateway-api
```

### CI/CD 통합
```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run code janitor
        run: claude skill code-janitor --ci-mode
```

## 📊 예상 효과

- ✅ 코드 품질 점수 60점 → 90점 향상
- ✅ 버그 발생률 50% 감소
- ✅ 코드 리뷰 시간 30% 단축
- ✅ 신규 개발자 온보딩 시간 40% 단축
- ✅ 기술 부채 누적 방지
