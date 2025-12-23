---
description: Track user-reported issue in KNOWN_ISSUES.md (project)
---

Please track this issue in KNOWN_ISSUES.md following the workflow:

## Risk Level Classification

| Level | Icon | Criteria | Response Time |
|-------|------|----------|---------------|
| Critical | 🔴 | System down, data loss, security | Immediate |
| High | 🟠 | Major feature broken, workflow blocked | < 4 hours |
| Medium | 🟡 | Feature degraded, workaround exists | < 24 hours |
| Low | 🟢 | Minor UI issue, cosmetic | Next sprint |

---

## When User Reports "안된다" (It doesn't work)

### 1. Acknowledge the issue
```
이슈를 확인했습니다. 조사를 시작하겠습니다.
```

### 2. Quick Diagnosis
```bash
# 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}"

# Gateway 로그 확인
docker logs gateway-api --tail 50 | grep -i error

# 프론트엔드 빌드 상태
cd web-ui && npm run build 2>&1 | tail -20
```

### 3. Add to KNOWN_ISSUES.md

```markdown
### Issue #X: [Title]

**Status**: 🔴/🟠/🟡/🟢 **OPEN**
**Severity**: [Critical/High/Medium/Low]
**Component**: [API name / Frontend / Docker]
**Discovered**: YYYY-MM-DD HH:MM
**Reported By**: User

---

**Symptoms**:
- [What's happening]
- [Error messages if any]
- [Expected vs Actual behavior]

**Reproduction Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Impact**:
- [Who/what is affected]
- [Severity of impact]
- [Workaround available?]

---

**Root Cause**: [If known, otherwise "Under investigation"]

**Workaround**: [Temporary solution if available]

---

**Investigation Log**:

#### YYYY-MM-DD HH:MM - Initial Investigation
- Checked logs: [findings]
- Tested: [what was tested]
- Hypothesis: [current theory]

---

**Investigation Checklist**:
- [ ] Check container status
- [ ] Review error logs
- [ ] Reproduce issue locally
- [ ] Identify root cause
- [ ] Apply fix
- [ ] Verify resolution
- [ ] Update documentation

---

**Related**:
- Files: [paths]
- PRs: [links]
- Similar Issues: [references]

**Notes**:
- [Additional context]
```

### 4. Investigate Root Cause

#### For Backend Issues:
```bash
# Gateway API 로그
docker logs gateway-api -f 2>&1 | grep -E "(ERROR|WARNING|Exception)"

# 특정 API 로그
docker logs <api-name> --tail 100

# 메모리/CPU 확인
docker stats --no-stream
```

#### For Frontend Issues:
```bash
# 빌드 에러 확인
cd web-ui
npm run build

# 타입 에러 확인
npm run lint

# 테스트 실행
npm run test:run
```

#### For Docker Issues:
```bash
# 컨테이너 상태
docker ps -a

# 네트워크 확인
docker network ls

# 볼륨 확인
docker volume ls
```

### 5. Document Findings
Update the investigation log with:
- What was checked
- What was found
- Current hypothesis

### 6. Apply Fix and Verify
```markdown
**Resolution**:
- Fix applied: [description]
- Files changed: [list]
- Verification: [how verified]
```

---

## When User Reports "잘된다" (It works)

### 1. Mark as RESOLVED
Update status in KNOWN_ISSUES.md:
```markdown
**Status**: ✅ **RESOLVED**
**Resolved**: YYYY-MM-DD HH:MM
**Resolution Time**: [X hours/days]
```

### 2. Add Resolution Details
```markdown
**Resolution**:
- Root cause: [what was wrong]
- Fix: [what was changed]
- Files: [list of changed files]
- Verification: [how it was verified]

**Lessons Learned**:
- [What we learned]
- [How to prevent in future]
```

### 3. Move to Resolved Section
Move the issue to the "## Resolved Issues" section at the bottom.

### 4. Update Related Docs
- [ ] Update ROADMAP.md with [x]
- [ ] Update CHANGELOG.md if significant
- [ ] Consider adding to docs/insights/lessons-learned/

---

## Issue Templates by Category

### API Connection Issue
```markdown
### Issue #X: [API Name] 연결 실패

**Status**: 🟠 **OPEN**
**Severity**: High
**Component**: [api-name]-api

**Symptoms**:
- API 호출 시 Connection refused
- Gateway 로그: "Failed to connect to [service]:5XXX"

**Quick Check**:
- [ ] Container running? `docker ps | grep [api-name]`
- [ ] Port accessible? `curl http://localhost:5XXX/api/v1/health`
- [ ] Network OK? `docker network inspect ax_default`
```

### Frontend Build Failure
```markdown
### Issue #X: Frontend 빌드 실패

**Status**: 🟠 **OPEN**
**Severity**: High
**Component**: web-ui

**Symptoms**:
- `npm run build` 실패
- TypeScript/ESLint 에러

**Quick Check**:
- [ ] Type errors? `npm run build 2>&1 | grep -i error`
- [ ] Lint errors? `npm run lint`
- [ ] Dependencies OK? `rm -rf node_modules && npm install`
```

### Workflow Execution Failure
```markdown
### Issue #X: BlueprintFlow 워크플로우 실패

**Status**: 🟠 **OPEN**
**Severity**: High
**Component**: BlueprintFlow

**Symptoms**:
- 워크플로우 실행 중단
- SSE 연결 끊김

**Quick Check**:
- [ ] Gateway 로그 확인
- [ ] Executor 로그 확인
- [ ] 개별 노드 테스트
```

---

## Severity Guidelines

### 🔴 Critical
- Production down
- Data loss/corruption
- Security vulnerability
- All users affected

### 🟠 High
- Major feature broken
- Workflow completely blocked
- No workaround available
- Many users affected

### 🟡 Medium
- Feature partially working
- Workaround exists
- Some users affected
- Performance degraded

### 🟢 Low
- Minor UI issues
- Cosmetic problems
- Edge cases only
- Documentation gaps
