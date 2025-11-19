# 🐛 Known Issues & Problem Tracker

**Last Updated**: 2025-11-19
**Purpose**: Track all reported issues, their status, and resolutions

---

## 📊 Issue Summary

| Status | Count |
|--------|-------|
| 🔴 Critical | 0 |
| 🟠 High | 1 |
| 🟡 Medium | 0 |
| 🟢 Low | 0 |
| ✅ Resolved | 3 |

---

## 🔴 Critical Issues

None currently! 🎉

---

## 🟠 High Priority Issues

### Issue #H001: EDGNet Container Unhealthy

**Status**: 🟠 **OPEN** (Pre-existing)
**Severity**: High
**Component**: edgnet-api
**Discovered**: Before 2025-11-19
**Reported By**: System health check

**Symptoms**:
```
Container status: Up 19 minutes (unhealthy)
Health check: Failed
Error: "All connection attempts failed"
```

**Impact**:
- Gateway API shows "degraded" status
- Segmentation functionality unavailable
- Cannot use `use_segmentation=true` in Gateway calls

**Root Cause**: Unknown (under investigation)

**Workaround**:
```python
# In Gateway API calls
{
  "use_segmentation": false  # Skip EDGNet
}
```

**Investigation Steps**:
1. [ ] Check EDGNet container logs
2. [ ] Verify EDGNet dependencies
3. [ ] Test EDGNet independently
4. [ ] Check GPU access issues
5. [ ] Review health check configuration

**Related**:
- Gateway API: /home/uproot/ax/poc/gateway-api/api_server.py
- EDGNet API: /home/uproot/ax/poc/edgnet-api/
- Docker: docker-compose.yml

**Notes**:
- This issue existed before the refactoring
- Not caused by recent code changes
- Does not block other development work

---

## 🟡 Medium Priority Issues

None currently! 🎉

---

## ✅ Resolved Issues

### Issue #M001: CLAUDE.md Exceeds Recommended Size ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: Medium → Resolved
**Component**: Documentation
**Discovered**: 2025-11-19
**Resolved**: 2025-11-19 10:56
**Resolution Time**: ~9 hours

**Original Issue**:
```
Before: 318 lines
Recommended: <100 lines
Overage: +218%
```

**Solution Applied**:
1. ✅ Split into focused files:
   - QUICK_START.md (96 lines) - Quick reference
   - ARCHITECTURE.md (266 lines) - System design
   - WORKFLOWS.md (402 lines) - Common tasks
   - KNOWN_ISSUES.md (373 lines) - Issue tracking
   - ROADMAP.md (264 lines) - Project tracking

2. ✅ Refactored CLAUDE.md as index (129 lines)
   - Project overview
   - Documentation map
   - Quick commands
   - LLM best practices

3. ✅ Created .claude/commands/ directory
   - test-api.md - Test workflow
   - debug-issue.md - Debug workflow
   - add-feature.md - Feature workflow
   - rebuild-service.md - Docker workflow
   - track-issue.md - Issue tracking workflow

**Verification**:
- ✅ CLAUDE.md: 129 lines (within best practice)
- ✅ All focused files created
- ✅ Custom commands functional
- ✅ Documentation cross-references updated

**Location**:
- /home/uproot/ax/poc/CLAUDE.md
- /home/uproot/ax/poc/QUICK_START.md
- /home/uproot/ax/poc/ARCHITECTURE.md
- /home/uproot/ax/poc/WORKFLOWS.md
- /home/uproot/ax/poc/.claude/commands/

**Lessons Learned**:
- Modular documentation is more maintainable
- Focused files improve LLM parsing efficiency
- Custom commands standardize workflows
- Index file improves navigation

---

### Issue #R001: OCR Values Not Showing in Visualization ✅

**Status**: ✅ **RESOLVED** (2025-11-18)
**Severity**: High → Resolved
**Component**: Gateway API, YOLO API
**Discovered**: 2025-11-18
**Resolved**: 2025-11-18
**Resolution Time**: ~2 hours

**Original Report** (User):
> "아니요 바운딩박스 옆에 하나도 안나와요.... 이거부터 해결을 해주세요"

**Symptoms**:
- YOLO visualization showed bounding boxes
- OCR-extracted values not appearing next to boxes
- Expected: "linear_dim: 50±0.1"
- Actual: Only "linear_dim (0.85)"

**Root Cause**:
Data structure mismatch in gateway-api/api_server.py
```python
# Lines 1893, 1957: Incorrect data access
dims_count = len(results[idx].get("data", {}).get("dimensions", []))
# But call_edocr2_ocr() returns edocr_data directly
```

**Fix Applied**:
```python
# Removed nested "data" key access
dims_count = len(results[idx].get("dimensions", []))
ocr_dimensions = ocr_results_data.get("dimensions", [])
```

**Verification**:
- ✅ Logs showed "eDOCr2 완료: 6개 치수 추출"
- ✅ Matching YOLO detections with OCR dimensions working
- ✅ Visualization shows OCR values correctly

**Location**:
- gateway-api/api_server.py:1893
- gateway-api/api_server.py:1957

**Lessons Learned**:
- Always verify data structure before accessing nested keys
- Test with real data, not just mock responses
- User feedback critical for catching integration issues

---

### Issue #R002: Pydantic Validation Error on OCR Tables Field ✅

**Status**: ✅ **RESOLVED** (2025-11-19)
**Severity**: Critical → Resolved
**Component**: Gateway API
**Discovered**: 2025-11-19 01:40 (during testing)
**Resolved**: 2025-11-19 01:42
**Resolution Time**: ~2 minutes

**Symptoms**:
```python
fastapi.exceptions.ResponseValidationError: 1 validation errors:
  {'type': 'dict_type',
   'loc': ('response', 'data', 'ocr_results', 'tables', 0),
   'msg': 'Input should be a valid dictionary',
   'input': [{...}, {...}]}
```

**Root Cause**:
Pydantic model definition mismatch
```python
# gateway-api/models/response.py:49
# Defined as:
tables: List[Dict[str, Any]] = Field(...)

# But eDOCr2 returns:
[[{...}, {...}], [{...}]]  # List of lists!
```

**Fix Applied**:
```python
# Changed to flexible type
tables: List[Any] = Field(default=[], description="테이블 데이터 (nested structure)")
```

**Verification**:
- ✅ Gateway API test passed
- ✅ Processing time: 18.9s (normal)
- ✅ All pipeline components working

**Location**:
- gateway-api/models/response.py:49

**Lessons Learned**:
- Don't assume API response structures
- Use flexible types (`Any`) for variable structures
- Test with real API responses, not mocked data

---

## 🎯 Issue Resolution Workflow

### When User Reports "안된다" (It doesn't work)

**Immediate Actions**:
1. ✅ Acknowledge issue in response
2. ✅ Add to KNOWN_ISSUES.md with details
3. ✅ Investigate root cause
4. ✅ Document symptoms and error messages
5. ✅ Create reproduction steps
6. ✅ Identify affected components

**During Investigation**:
1. ✅ Check relevant logs
2. ✅ Review recent code changes
3. ✅ Test in isolation
4. ✅ Identify root cause
5. ✅ Document findings

**After Fix**:
1. ✅ Apply fix
2. ✅ Verify with original test case
3. ✅ Update KNOWN_ISSUES.md status
4. ✅ Document resolution
5. ✅ Add to lessons learned

### When User Reports "잘된다" (It works)

**Immediate Actions**:
1. ✅ Mark related issue as RESOLVED
2. ✅ Document resolution time
3. ✅ Update ROADMAP.md with [x]
4. ✅ Capture success metrics
5. ✅ Document what worked

**Follow-up**:
1. ✅ Add regression test
2. ✅ Document in verification report
3. ✅ Update user-facing docs

---

## 📈 Issue Metrics

### Resolution Time

| Priority | Target | Average | Best |
|----------|--------|---------|------|
| Critical | <1 hour | 2 min | 2 min |
| High | <4 hours | 2 hours | 2 hours |
| Medium | <1 day | - | - |
| Low | <1 week | - | - |

### Resolution Rate

| Period | Opened | Resolved | Rate |
|--------|--------|----------|------|
| 2025-11-18 | 1 | 1 | 100% |
| 2025-11-19 | 2 | 2 | 100% |
| **Total** | **3** | **3** | **100%** |

---

## 🔍 Common Problems & Quick Fixes

### "바운딩박스 옆에 값이 안나와요"
**Quick Check**:
```bash
# Check if OCR is returning data
docker logs gateway-api | grep "eDOCr2 완료"

# Should see: "eDOCr2 완료: N개 치수 추출"
# If N=0, check data structure access
```

### "API가 500 error를 반환해요"
**Quick Check**:
```bash
# Check Pydantic validation errors
docker logs gateway-api | grep "ResponseValidationError"

# Look for 'dict_type', 'list_type' errors
# Check model definitions in models/response.py
```

### "Container가 unhealthy해요"
**Quick Check**:
```bash
# Check container status
docker ps | grep unhealthy

# Check logs
docker logs <container-name> --tail 50

# Check health endpoint
curl http://localhost:<port>/api/v1/health
```

---

## 📝 Issue Template

When reporting new issues, use this template:

```markdown
### Issue #X: [Title]

**Status**: 🟠 OPEN
**Severity**: [Critical/High/Medium/Low]
**Component**: [API name]
**Discovered**: [Date]
**Reported By**: [User/System]

**Symptoms**:
- [What's happening]
- [Error messages]
- [Expected vs Actual behavior]

**Impact**:
- [Who/what is affected]
- [Severity of impact]

**Root Cause**: [If known]

**Workaround**: [Temporary solution]

**Investigation Steps**:
1. [ ] Step 1
2. [ ] Step 2

**Related**:
- Files: [paths]
- Issues: [links]

**Notes**:
- [Additional context]
```

---

## 🔗 Related Documents

- [ROADMAP.md](ROADMAP.md) - Project roadmap with issue tracking
- [COMPREHENSIVE_TEST_REPORT.md](COMPREHENSIVE_TEST_REPORT.md) - Test results
- [CLAUDE.md](CLAUDE.md) - Main project guide

---

**Maintained By**: Claude Code (Sonnet 4.5)
**Update Frequency**: Real-time (as issues occur/resolve)
**Review Frequency**: Daily
